# -*- coding: utf-8 -*-
"""
GeoTolk Routes
==============
Flask Blueprint with all REST API endpoints for the GeoTolk activity.

Endpoints:
    POST /api/geotolk/parse                               — Parse SND file content
    GET  /api/geotolk/sessions                            — List interpretation sessions
    POST /api/geotolk/sessions                            — Create a new session
    GET  /api/geotolk/sessions/<id>                       — Get session with interpretations
    POST /api/geotolk/sessions/<id>/interpretations       — Add an interpretation
    PUT  /api/geotolk/interpretations/<id>                — Update layer interpretation
    GET  /api/geotolk/training-data                       — Export all interpreted data
"""

import base64
from datetime import datetime

from flask import Blueprint, jsonify, request

from core.database import get_db_session
from core.models import GeoTolkSession, GeoTolkInterpretation
from activities.geotolk.parsing.snd_parser import parse_snd_with_events

geotolk_bp = Blueprint('geotolk', __name__, url_prefix='/api/geotolk')


@geotolk_bp.route('/parse', methods=['POST'])
def parse_snd():
    """Parse SND file content and return structured measurement data."""
    data            = request.get_json() or {}
    content         = data.get('content')
    content_base64  = data.get('content_base64')

    if content_base64:
        try:
            content = base64.b64decode(content_base64).decode('utf-8', errors='ignore')
        except Exception as exc:
            return jsonify({'error': f'Could not decode base64: {exc}'}), 400

    if not content:
        return jsonify({'error': 'No file content provided'}), 400

    try:
        parsed = parse_snd_with_events(content)
        return jsonify({'success': True, 'data': parsed})
    except Exception as exc:
        return jsonify({'error': str(exc)}), 400


@geotolk_bp.route('/sessions', methods=['GET'])
def list_sessions():
    """List GeoTolk sessions, optionally filtered by project."""
    project_id = request.args.get('project_id', type=int)
    limit      = request.args.get('limit', 20, type=int)

    db = get_db_session()
    try:
        query = db.query(GeoTolkSession)
        if project_id:
            query = query.filter(GeoTolkSession.project_id == project_id)
        sessions = query.order_by(GeoTolkSession.created_at.desc()).limit(limit).all()
        return jsonify({'success': True, 'sessions': [s.to_dict() for s in sessions]})
    finally:
        db.close()


@geotolk_bp.route('/sessions', methods=['POST'])
def create_session():
    """Create a new GeoTolk interpretation session."""
    data          = request.get_json() or {}
    project_id    = data.get('project_id')
    activity_name = data.get('activity_name', 'GeoTolk interpretation')
    username      = data.get('username', 'unknown')

    db = get_db_session()
    try:
        session = GeoTolkSession(
            project_id=project_id,
            activity_name=activity_name,
            username=username,
            status='active',
        )
        db.add(session)
        db.commit()
        return jsonify({'success': True, 'session': session.to_dict()}), 201
    except Exception as exc:
        db.rollback()
        return jsonify({'error': str(exc)}), 500
    finally:
        db.close()


@geotolk_bp.route('/sessions/<int:session_id>', methods=['GET'])
def get_session(session_id: int):
    """Return a session with all its interpretations."""
    db = get_db_session()
    try:
        session = db.query(GeoTolkSession).filter(GeoTolkSession.id == session_id).first()
        if not session:
            return jsonify({'error': 'Session not found'}), 404
        result = session.to_dict()
        result['interpretations'] = [i.to_dict() for i in session.interpretations]
        return jsonify({'success': True, 'session': result})
    finally:
        db.close()


@geotolk_bp.route('/sessions/<int:session_id>/interpretations', methods=['POST'])
def add_interpretation(session_id: int):
    """Add a file interpretation to an existing session."""
    data        = request.get_json() or {}
    filename    = data.get('filename')
    parsed_data = data.get('parsed_data', {})
    layers      = data.get('layers', [])

    if not filename:
        return jsonify({'error': 'filename is required'}), 400

    db = get_db_session()
    try:
        session = db.query(GeoTolkSession).filter(GeoTolkSession.id == session_id).first()
        if not session:
            return jsonify({'error': 'Session not found'}), 404

        interp = GeoTolkInterpretation(
            session_id=session_id,
            filename=filename,
            max_depth=parsed_data.get('max_depth'),
            status='pending',
        )
        interp.set_parsed_data(parsed_data)
        if layers:
            interp.set_layers(layers)
            interp.status         = 'interpreted'
            interp.interpreted_at = datetime.utcnow()

        db.add(interp)
        session.total_files += 1
        if layers:
            session.completed_files += 1
        db.commit()
        return jsonify({'success': True, 'interpretation': interp.to_dict()}), 201
    except Exception as exc:
        db.rollback()
        return jsonify({'error': str(exc)}), 500
    finally:
        db.close()


@geotolk_bp.route('/interpretations/<int:interp_id>', methods=['PUT'])
def update_interpretation(interp_id: int):
    """Update the layer interpretation for a file."""
    data   = request.get_json() or {}
    layers = data.get('layers', [])

    db = get_db_session()
    try:
        interp = db.query(GeoTolkInterpretation).filter(
            GeoTolkInterpretation.id == interp_id
        ).first()
        if not interp:
            return jsonify({'error': 'Interpretation not found'}), 404

        was_pending = interp.status == 'pending'
        interp.set_layers(layers)
        interp.status         = 'interpreted'
        interp.interpreted_at = datetime.utcnow()

        if was_pending:
            session = db.query(GeoTolkSession).filter(
                GeoTolkSession.id == interp.session_id
            ).first()
            if session:
                session.completed_files += 1

        db.commit()
        return jsonify({'success': True, 'interpretation': interp.to_dict()})
    except Exception as exc:
        db.rollback()
        return jsonify({'error': str(exc)}), 500
    finally:
        db.close()


@geotolk_bp.route('/training-data', methods=['GET'])
def get_training_data():
    """Export all interpreted file data for ML training."""
    limit = request.args.get('limit', 1000, type=int)

    db = get_db_session()
    try:
        records = db.query(GeoTolkInterpretation).filter(
            GeoTolkInterpretation.status == 'interpreted'
        ).limit(limit).all()

        data = [
            {
                'filename':    r.filename,
                'max_depth':   r.max_depth,
                'parsed_data': r.get_parsed_data(),
                'layers':      r.get_layers(),
            }
            for r in records
        ]
        return jsonify({'success': True, 'count': len(data), 'data': data})
    finally:
        db.close()

