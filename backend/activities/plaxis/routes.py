# -*- coding: utf-8 -*-
"""
Plaxis Routes
=============
Flask Blueprint with all REST API endpoints for the Plaxis activity.

Endpoints:
    POST /api/plaxis/connect              — Connect to a running Plaxis session
    POST /api/plaxis/disconnect           — Disconnect
    GET  /api/plaxis/status               — Check connection status
    GET  /api/plaxis/model-info           — Fetch phases and structure names
    POST /api/plaxis/run                  — Run a result-extraction job
    GET  /api/plaxis/calculations         — List saved calculation records
    GET  /api/plaxis/calculations/<id>    — Get a specific calculation
    POST /api/plaxis/calculations/<id>/rerun — Re-run a previous calculation
"""

import json
from datetime import datetime
from typing import Any, Dict

from flask import Blueprint, jsonify, request

from core.database import get_db_session
from core.models import PlaxisCalculation
from activities.plaxis.runner.runner import run_plaxis_extraction

plaxis_bp = Blueprint('plaxis', __name__, url_prefix='/api/plaxis')

# In-process session store (one entry per user session).
# Replace with Redis or a DB table when multi-worker deployment is needed.
_plaxis_sessions: Dict[str, Any] = {}

# ---------------------------------------------------------------------------
# Demo data (returned when Plaxis is not available)
# ---------------------------------------------------------------------------
_DEMO_STRUCTURES = {
    'plates': [
        {'name': 'Spunt_venstre', 'display_name': 'Name: Spunt_venstre, x = 0.0', 'x': 0.0, 'type': 'plate'},
        {'name': 'Spunt_høyre',   'display_name': 'Name: Spunt_høyre, x = 15.0',  'x': 15.0,'type': 'plate'},
    ],
    'embedded_beams':       [],
    'node_to_node_anchors': [
        {'name': 'Anker_1', 'display_name': 'Name: Anker_1, (0.0,-2.0) → (5.0,-4.0)',
         'x1': 0.0, 'y1': -2.0, 'x2': 5.0, 'y2': -4.0, 'type': 'node_to_node_anchor'},
    ],
    'fixed_end_anchors': [],
    'geogrids':          [],
}
_DEMO_PHASES = [
    {'id': i, 'name': name, 'msf_enabled': False, 'ux_enabled': False, 'capacity_enabled': False}
    for i, name in enumerate([
        'Initial phase', 'Installasjon spunt', 'Utgraving nivå 1',
        'Installasjon anker', 'Utgraving til bunn', 'FoS analyse',
    ])
]
_DEMO_RESULTS = {
    'capacity': {
        'plates': {
            'Spunt_venstre': {
                'Utgraving til bunn': {'Nx': 245.3, 'Q': 89.2, 'M': 312.5},
                'FoS analyse':        {'Nx': 267.8, 'Q': 95.4, 'M': 345.2},
            }
        }
    },
    'msf':          {'FoS analyse': 1.32},
    'displacement': {'plates': {'Spunt_venstre': {'Utgraving til bunn': 23.5, 'FoS analyse': 28.1}}},
}


# ---------------------------------------------------------------------------
# Connection
# ---------------------------------------------------------------------------

@plaxis_bp.route('/connect', methods=['POST'])
def connect():
    """Connect to a running Plaxis Input server."""
    data       = request.get_json() or {}
    port       = data.get('port')
    password   = data.get('password')
    session_id = data.get('session_id', 'default')

    if not port or not password:
        return jsonify({'error': 'port and password are required'}), 400

    try:
        port = int(port)
    except ValueError:
        return jsonify({'error': 'port must be a number'}), 400

    try:
        from plxscripting.easy import new_server
        s_i, g_i = new_server('localhost', port, password=password)
        _plaxis_sessions[session_id] = {
            'port': port, 'password': password,
            's_i': s_i, 'g_i': g_i, 'connected': True,
        }
        return jsonify({'success': True, 'message': 'Connected to Plaxis.', 'session_id': session_id})
    except ImportError:
        _plaxis_sessions[session_id] = {
            'port': port, 'password': password,
            's_i': None, 'g_i': None, 'connected': False,
        }
        return jsonify({
            'success': True,
            'warning': 'plxscripting not available — demo mode active.',
            'session_id': session_id,
        })
    except Exception as exc:
        return jsonify({'success': False, 'error': str(exc)}), 400


@plaxis_bp.route('/disconnect', methods=['POST'])
def disconnect():
    """Remove a Plaxis session."""
    data       = request.get_json() or {}
    session_id = data.get('session_id', 'default')
    _plaxis_sessions.pop(session_id, None)
    return jsonify({'success': True, 'message': 'Disconnected.'})


@plaxis_bp.route('/status', methods=['GET'])
def status():
    """Return the connection status for the given session."""
    session_id = request.args.get('session_id', 'default')
    session    = _plaxis_sessions.get(session_id)
    if session:
        return jsonify({'connected': True, 'port': session['port']})
    return jsonify({'connected': False})


# ---------------------------------------------------------------------------
# Model info
# ---------------------------------------------------------------------------

@plaxis_bp.route('/model-info', methods=['GET'])
def model_info():
    """Return structures and phases from the open Plaxis model (or demo data)."""
    session_id = request.args.get('session_id', 'default')
    session    = _plaxis_sessions.get(session_id)

    if not session or not session.get('g_i'):
        return jsonify({
            'success': True, 'demo_mode': True,
            'structures': _DEMO_STRUCTURES, 'phases': _DEMO_PHASES,
        })

    g_i = session['g_i']
    try:
        from activities.plaxis.extraction.model_info import extract_model_info
        info = extract_model_info(g_i)
        info.update({'success': True, 'demo_mode': False})
        return jsonify(info)
    except Exception as exc:
        return jsonify({'success': False, 'error': str(exc)}), 500


# ---------------------------------------------------------------------------
# Run extraction
# ---------------------------------------------------------------------------

@plaxis_bp.route('/run', methods=['POST'])
def run_extraction():
    """Run a Plaxis result-extraction job and save the record to the database."""
    data       = request.get_json() or {}
    session_id = data.get('session_id', 'default')
    job        = data.get('job')

    if not job:
        return jsonify({'error': 'job configuration is required'}), 400

    input_port     = data.get('input_port')
    input_password = data.get('input_password')
    output_port    = data.get('output_port')
    output_password= data.get('output_password')

    # Fall back to stored session values
    session = _plaxis_sessions.get(session_id, {})
    input_port     = input_port     or session.get('port')
    input_password = input_password or session.get('password')

    project_id    = data.get('project_id')
    activity_name = data.get('activity_name', 'Plaxis calculation')

    db = get_db_session()
    calc = PlaxisCalculation(
        project_id=project_id, username=session_id,
        activity_name=activity_name, status='started',
        input_port=input_port, output_port=output_port,
        output_path=job.get('resultsPath', {}).get('path'),
    )
    structures = job.get('structures', {})
    calc.set_structures(
        structures.get('plates', []) + structures.get('embedded_beams', []),
        structures.get('node_to_node_anchors', []) + structures.get('fixed_end_anchors', []),
    )
    analysis = job.get('analysis', {})
    calc.set_phases(
        analysis.get('capacity_check', {}).get('phases', []),
        analysis.get('msf', {}).get('phases', []),
        analysis.get('displacement', {}).get('phases', []),
    )
    calc.displacement_component = analysis.get('displacement', {}).get('component', 'Ux')
    db.add(calc)
    db.commit()
    calc_id = calc.id

    # Demo mode: no real Plaxis connection
    if not input_port or not input_password:
        calc.status       = 'completed'
        calc.completed_at = datetime.utcnow()
        calc.results_json = json.dumps(_DEMO_RESULTS)
        db.commit()
        db.close()
        return jsonify({
            'success': True, 'demo_mode': True,
            'calculation_id': calc_id,
            'results': _DEMO_RESULTS,
            'output_file': 'Demo — no file generated',
            'message': 'Demo mode: showing sample results.',
        })

    try:
        calc.status = 'running'
        db.commit()

        results = run_plaxis_extraction(
            input_port=input_port,
            input_password=input_password,
            output_port=output_port,
            output_password=output_password,
            job=job,
        )

        if results.get('success'):
            calc.status       = 'completed'
            calc.output_file  = results.get('output_file')
            calc.results_json = json.dumps({
                'capacity':     results.get('capacity', {}),
                'msf':          results.get('msf', {}),
                'displacement': results.get('displacement', {}),
            })
        else:
            calc.status        = 'failed'
            calc.error_message = results.get('error') or '; '.join(results.get('errors', []))

        calc.completed_at = datetime.utcnow()
        db.commit()
        results['calculation_id'] = calc_id
        return jsonify(results)

    except Exception as exc:
        calc.status        = 'failed'
        calc.error_message = str(exc)
        calc.completed_at  = datetime.utcnow()
        db.commit()
        return jsonify({'success': False, 'calculation_id': calc_id, 'error': str(exc)}), 500
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Calculation history
# ---------------------------------------------------------------------------

@plaxis_bp.route('/calculations', methods=['GET'])
def list_calculations():
    """Return saved calculation records, optionally filtered by project or user."""
    project_id = request.args.get('project_id', type=int)
    username   = request.args.get('username')
    limit      = request.args.get('limit', 20, type=int)

    db = get_db_session()
    try:
        query = db.query(PlaxisCalculation)
        if project_id:
            query = query.filter(PlaxisCalculation.project_id == project_id)
        if username:
            query = query.filter(PlaxisCalculation.username == username)
        calcs = query.order_by(PlaxisCalculation.started_at.desc()).limit(limit).all()
        return jsonify({'success': True, 'calculations': [c.to_dict() for c in calcs]})
    finally:
        db.close()


@plaxis_bp.route('/calculations/<int:calc_id>', methods=['GET'])
def get_calculation(calc_id: int):
    """Return a single calculation record."""
    db = get_db_session()
    try:
        calc = db.query(PlaxisCalculation).filter(PlaxisCalculation.id == calc_id).first()
        if not calc:
            return jsonify({'error': 'Calculation not found'}), 404
        return jsonify({'success': True, 'calculation': calc.to_dict()})
    finally:
        db.close()


@plaxis_bp.route('/calculations/<int:calc_id>/rerun', methods=['POST'])
def rerun_calculation(calc_id: int):
    """Re-run a previous calculation with the same parameters."""
    data = request.get_json() or {}

    db = get_db_session()
    try:
        original = db.query(PlaxisCalculation).filter(PlaxisCalculation.id == calc_id).first()
        if not original:
            return jsonify({'error': 'Calculation not found'}), 404

        input_password = data.get('input_password')
        if not input_password:
            return jsonify({'error': 'input_password is required to re-run'}), 400

        input_port  = data.get('input_port')  or original.input_port
        output_port = data.get('output_port') or original.output_port
        output_password = data.get('output_password')
        session_id  = data.get('session_id', original.username)

        structures = original.get_structures()
        phases     = original.get_phases()

        job = {
            'structures': {
                'plates':               structures['spunts'],
                'embedded_beams':       [],
                'node_to_node_anchors': structures['anchors'],
                'fixed_end_anchors':    [],
                'geogrids':             [],
            },
            'analysis': {
                'capacity_check': {
                    'enabled': bool(phases['capacity']),
                    'phases':   phases['capacity'],
                },
                'msf': {
                    'enabled': bool(phases['msf']),
                    'phases':   phases['msf'],
                },
                'displacement': {
                    'enabled':   bool(phases['displacement']),
                    'phases':    phases['displacement'],
                    'component': original.displacement_component or 'Ux',
                },
            },
            'resultsPath': {'path': original.output_path or data.get('output_path', '')},
        }
        db.close()

        results = run_plaxis_extraction(
            input_port=input_port,
            input_password=input_password,
            output_port=output_port,
            output_password=output_password,
            job=job,
        )
        return jsonify(results)

    except Exception as exc:
        return jsonify({'error': str(exc)}), 500
    finally:
        try:
            db.close()
        except Exception:
            pass

