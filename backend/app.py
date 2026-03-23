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

from core.database import init_db
from activities.plaxis.routes    import plaxis_bp
from activities.geotolk.routes   import geotolk_bp
from activities.projects.routes  import projects_bp
from activities.modeling.routes  import modeling_bp

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
    return jsonify({'status': 'ok', 'ready': True})


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
        # Prevent the reloader from watching the virtual environment directory
        exclude_patterns=[r'*\.venv\*', '*/.venv/*', r'*\__pycache__\*'],
    )
