# -*- coding: utf-8 -*-
"""
RamGAP Flask Backend
====================
Application entry point. Creates the Flask app, registers all activity
Blueprints, and starts the development server.

Activity routes live in backend/activities/<name>/routes.py.
Database models and connection helpers live in backend/core/.
"""

import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from flasgger import Swagger

from core.database import init_db
from activities.plaxis.routes        import plaxis_bp
from activities.geotolk.routes       import geotolk_bp
from activities.projects.routes      import projects_bp
from activities.modeling.routes       import modeling_bp
from activities.plaxis_agent.routes  import plaxis_agent_bp

# These blueprints have extra dependencies — import gracefully so the
# rest of the backend still works if a package is missing on Azure.
_blueprint_errors: list[str] = []

try:
    from activities.quiz.routes import quiz_bp
except Exception as _e:
    quiz_bp = None
    _blueprint_errors.append(f'quiz: {_e}')

try:
    from activities.geogpt.routes import geogpt_bp
except Exception as _e:
    geogpt_bp = None
    _blueprint_errors.append(f'geogpt: {_e}')

try:
    from activities.standarder.routes import standarder_bp
except Exception as _e:
    standarder_bp = None
    _blueprint_errors.append(f'standarder: {_e}')

if _blueprint_errors:
    for _err in _blueprint_errors:
        print(f'WARNING: Blueprint import failed — {_err}')

# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------

app = Flask(__name__)
CORS(app)

# Register activity Blueprints
app.register_blueprint(plaxis_bp)
app.register_blueprint(geotolk_bp)
app.register_blueprint(projects_bp)
app.register_blueprint(modeling_bp)
app.register_blueprint(plaxis_agent_bp)
if quiz_bp:
    app.register_blueprint(quiz_bp)
if geogpt_bp:
    app.register_blueprint(geogpt_bp)
if standarder_bp:
    app.register_blueprint(standarder_bp)

# ---------------------------------------------------------------------------
# Swagger / OpenAPI documentation
# ---------------------------------------------------------------------------
# Auto-generate a minimal OpenAPI spec from all registered routes so that
# every endpoint shows up in Swagger UI without needing YAML docstrings.

_BLUEPRINT_TAGS = {
    'plaxis': 'Plaxis',
    'geotolk': 'GeoTolk',
    'projects': 'Projects',
    'modeling': 'Modeling',
    'plaxis_agent': 'GAPI',
    'geogpt': 'GeoGPT',
    'standarder': 'Standarder',
}

def _build_paths(app_instance):
    """Build OpenAPI paths dict from Flask URL rules."""
    paths: dict = {}
    ignored = {'static', 'flasgger.static', 'flasgger.apispec_1'}
    for rule in app_instance.url_map.iter_rules():
        if rule.endpoint in ignored or rule.rule.startswith('/flasgger'):
            continue
        # Convert Flask <param> to OpenAPI {param}
        path = rule.rule
        parameters = []
        for arg in rule.arguments:
            path = path.replace(f'<int:{arg}>', f'{{{arg}}}')
            path = path.replace(f'<path:{arg}>', f'{{{arg}}}')
            path = path.replace(f'<{arg}>', f'{{{arg}}}')
            parameters.append({
                'name': arg, 'in': 'path', 'required': True, 'type': 'string',
            })
        if path not in paths:
            paths[path] = {}
        # Determine tag from blueprint
        view_func = app_instance.view_functions.get(rule.endpoint)
        tag = 'System'
        if '.' in rule.endpoint:
            bp_name = rule.endpoint.rsplit('.', 1)[0]
            tag = _BLUEPRINT_TAGS.get(bp_name, bp_name)
        summary = (view_func.__doc__ or '').strip().split('\n')[0] if view_func else ''
        for method in (rule.methods - {'OPTIONS', 'HEAD'}):
            paths[path][method.lower()] = {
                'tags': [tag],
                'summary': summary or rule.endpoint,
                'parameters': parameters,
                'responses': {'200': {'description': 'Success'}},
            }
    return paths

with app.app_context():
    _paths = _build_paths(app)

Swagger(app, template={
    'info': {
        'title': 'RamGAP API',
        'description': 'Geoteknisk ingeniørplattform — Plaxis, GeoTolk, GeoGPT, Modellering',
        'version': '0.1.0',
    },
    'basePath': '/',
    'schemes': ['http', 'https'],
    'paths': _paths,
})

# Initialize database on startup.
# Flask debug mode spawns two processes (supervisor + worker). Guard against
# running init_db() twice by checking WERKZEUG_RUN_MAIN — in debug mode we
# only initialise in the inner worker process; in production we always run it.
_run_main = os.environ.get('WERKZEUG_RUN_MAIN')
if not (os.getenv('DEBUG', 'true').lower() == 'true') or _run_main == 'true':
    try:
        init_db()
    except Exception as _exc:
        print(f'Warning: Database initialization failed: {_exc}')
        print('Backend will start, but database operations may not work.')


# ---------------------------------------------------------------------------
# System endpoints (not activity-specific)
# ---------------------------------------------------------------------------

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check — used by the frontend to verify the backend is running."""
    return jsonify({'status': 'healthy', 'message': 'RamGAP backend is running.'})


@app.route('/api/status', methods=['GET'])
def get_status():
    """Application status."""
    registered = sorted({r.rule for r in app.url_map.iter_rules() if r.rule.startswith('/api/')})
    return jsonify({
        'status': 'ok',
        'ready': True,
        'blueprint_errors': _blueprint_errors,
        'registered_api_routes': registered,
    })


# Legacy placeholder (kept until all frontends are updated)
@app.route('/api/data', methods=['GET'])
def get_data():
    return jsonify({'data': [], 'message': 'No data yet'})


@app.route('/api/data', methods=['POST'])
def create_data():
    return jsonify({'success': True, 'data': request.get_json()}), 201


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    app.run(
        debug=os.getenv('DEBUG', 'true').lower() == 'true',
        host=os.getenv('HOST', '0.0.0.0'),
        port=int(os.getenv('PORT', '5050')),
        # Prevent the reloader from watching system libs, venv, and pycache.
        # plxscripting uses sockets which can trigger false reloads of socket.py
        exclude_patterns=[
            r'*\.venv\*', '*/.venv/*',
            r'*\__pycache__\*', '*/__pycache__/*',
            r'C:\Program Files\*', 'C:/Program Files/*',
            r'*\Lib\*', '*/Lib/*',
            r'*\lib\*', '*/lib/*',
        ],
        use_reloader=os.getenv('USE_RELOADER', 'false').lower() == 'true',
    )
