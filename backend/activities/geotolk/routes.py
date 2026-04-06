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

Grasshopper integration:
    GET  /api/geotolk/gh/boreholes                        — List interpreted boreholes for a project
    GET  /api/geotolk/gh/borehole/<id>                    — Get single borehole with full layer data
"""

import base64
from datetime import datetime

from flask import Blueprint, jsonify, request

from sqlalchemy import or_

from core.database import get_db_session, get_ml_session
from core.models import (
    GeoTolkSession, GeoTolkInterpretation, GeoTolkMLTrainingData, RecentActivity,
    Project, ProjectAccess,
)
from activities.geotolk.parsing.snd_parser import parse_snd_with_events, parse_snd_header_coords

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
        coords = parse_snd_header_coords(content)
        parsed['coords'] = coords
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
    snd_raw_content = data.get('snd_raw_content')

    has_oedometer = data.get('has_oedometer', False)

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
            has_oedometer=bool(has_oedometer),
            snd_raw_content=snd_raw_content,
            status='pending',
        )
        # Store full parsed data (all arrays) for caching
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


@geotolk_bp.route('/sessions/<int:session_id>/complete', methods=['POST'])
def complete_session(session_id: int):
    """
    Mark a session as completed, store structured ML training data,
    and log the activity. Called when the user clicks Fullfør.
    """
    data = request.get_json() or {}
    files_data = data.get('files', [])        # list of interpreted file dicts
    username   = data.get('username', 'unknown')

    db = get_db_session()
    ml_db = get_ml_session()
    try:
        session = db.query(GeoTolkSession).filter(GeoTolkSession.id == session_id).first()
        if not session:
            return jsonify({'error': 'Session not found'}), 404

        session.status       = 'completed'
        session.completed_at = datetime.utcnow()

        # Store ML training records for every interpreted file (in ML database)
        ml_count = 0
        for fd in files_data:
            if fd.get('status') != 'interpreted':
                continue
            layers = fd.get('layers', [])
            if not layers:
                continue

            parsed       = fd.get('parsed_data', {})
            coords       = fd.get('coords')  # {x, y, z} or None
            raw_content  = fd.get('snd_raw_content', '')

            # Extract header (lines before data block, typically first ~20 lines)
            snd_header = ''
            if raw_content:
                header_lines = []
                for line in raw_content.splitlines():
                    if line.strip().startswith('*'):
                        header_lines.append(line)
                        break
                    header_lines.append(line)
                snd_header = '\n'.join(header_lines)

            ml_rec = GeoTolkMLTrainingData(
                interpretation_id=fd.get('interpretation_id', 0),
                session_id=session_id,
                project_id=session.project_id,
                filename=fd.get('filename', ''),
                max_depth=parsed.get('max_depth'),
                coord_x=coords.get('x') if coords else None,
                coord_y=coords.get('y') if coords else None,
                coord_z=coords.get('z') if coords else None,
                snd_raw_content=raw_content or None,
                snd_header=snd_header or None,
                has_oedometer=bool(fd.get('has_oedometer', False)),
                interpreted_by=username,
                interpreted_at=datetime.utcnow(),
            )
            # Store the full sounding signal for feature extraction
            ml_rec.set_sounding({
                'depth': parsed.get('depth', []),
                'c2':    parsed.get('c2', []),
                'c3':    parsed.get('c3', []),
                'c4':    parsed.get('c4', []),
            })
            ml_rec.set_layers(layers)
            ml_rec.set_events({
                'spyling': parsed.get('spyling', []),
                'slag':    parsed.get('slag', []),
            })
            ml_db.add(ml_rec)
            ml_count += 1

        # Log as project activity (in main database)
        if session.project_id:
            activity = RecentActivity(
                username=username,
                project_id=session.project_id,
                activity_type='GeoTolk',
                activity_name=(
                    f'GeoTolk fullført: {session.activity_name} '
                    f'({session.completed_files} filer tolket)'
                ),
            )
            db.add(activity)

        ml_db.commit()
        db.commit()
        return jsonify({
            'success':    True,
            'ml_records': ml_count,
            'session':    session.to_dict(),
        })
    except Exception as exc:
        ml_db.rollback()
        db.rollback()
        return jsonify({'error': str(exc)}), 500
    finally:
        ml_db.close()
        db.close()


@geotolk_bp.route('/training-data', methods=['GET'])
def get_training_data():
    """Export all structured ML training data (from ML database)."""
    limit = request.args.get('limit', 1000, type=int)

    ml_db = get_ml_session()
    try:
        records = ml_db.query(GeoTolkMLTrainingData).order_by(
            GeoTolkMLTrainingData.created_at.desc()
        ).limit(limit).all()

        return jsonify({
            'success': True,
            'count':   len(records),
            'data':    [r.to_dict() for r in records],
        })
    finally:
        ml_db.close()


@geotolk_bp.route('/sessions/<int:session_id>/resume', methods=['GET'])
def resume_session(session_id: int):
    """
    Return a session with full interpretation data for resuming in the frontend.
    Includes parsed_data with full arrays and raw SND content,
    so the user can continue interpreting without re-uploading files.
    """
    db = get_db_session()
    try:
        session = db.query(GeoTolkSession).filter(GeoTolkSession.id == session_id).first()
        if not session:
            return jsonify({'error': 'Session not found'}), 404

        result = session.to_dict()
        files = []
        for interp in session.interpretations:
            files.append({
                'interpretation_id': interp.id,
                'filename':          interp.filename,
                'parsed_data':       interp.get_parsed_data(),
                'layers':            interp.get_layers(),
                'has_oedometer':     interp.has_oedometer or False,
                'status':            interp.status,
                'content':           interp.snd_raw_content or '',
            })
        result['files'] = files
        return jsonify({'success': True, 'session': result})
    finally:
        db.close()


@geotolk_bp.route('/project-sessions', methods=['GET'])
def list_project_sessions():
    """List completed GeoTolk sessions for a project (for Beregninger tab)."""
    project_id = request.args.get('project_id', type=int)
    limit      = request.args.get('limit', 20, type=int)

    if not project_id:
        return jsonify({'error': 'project_id is required'}), 400

    db = get_db_session()
    try:
        sessions = (
            db.query(GeoTolkSession)
            .filter(GeoTolkSession.project_id == project_id)
            .order_by(GeoTolkSession.created_at.desc())
            .limit(limit)
            .all()
        )
        result = []
        for s in sessions:
            d = s.to_dict()
            d['username'] = s.username
            # Summary of interpreted files
            interpreted = [i for i in s.interpretations if i.status == 'interpreted']
            d['interpreted_files'] = [
                {'filename': i.filename, 'num_layers': len(i.get_layers())}
                for i in interpreted
            ]
            result.append(d)
        return jsonify({'success': True, 'sessions': result})
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Grasshopper integration endpoints
# ---------------------------------------------------------------------------

def _resolve_project_id(db, project_name: str, username: str):
    """Look up a project by name. If username is given, restrict to projects
    the user has access to. Returns project_id or None."""
    query = db.query(Project).filter(
        Project.is_active == True,  # noqa: E712
        Project.name == project_name,
    )
    if username:
        query = query.filter(
            or_(
                Project.created_by == username,
                Project.id.in_(
                    db.query(ProjectAccess.project_id).filter(
                        ProjectAccess.username == username
                    )
                ),
            )
        )
    project = query.first()
    return project.id if project else None


@geotolk_bp.route('/gh/boreholes', methods=['GET'])
def gh_list_boreholes():
    """
    Return all interpreted boreholes for a project with full layer data.

    Designed as the single endpoint a Grasshopper component needs:
    send project name + username, get back every borehole with its layers.

    Query params:
        project_name (str)           — Project name (required if no project_id)
        project_id   (int)           — Project ID   (required if no project_name)
        username     (str, optional) — Filter by interpreter username
    """
    project_id   = request.args.get('project_id', type=int)
    project_name = request.args.get('project_name', type=str)
    username     = request.args.get('username', type=str)

    if not project_id and not project_name:
        return jsonify({'error': 'project_name or project_id is required'}), 400

    db = get_db_session()
    try:
        # Resolve project name → id when needed
        if not project_id:
            project_id = _resolve_project_id(db, project_name, username)
            if not project_id:
                return jsonify({'error': f'Project "{project_name}" not found'}), 404

        query = (
            db.query(GeoTolkInterpretation)
            .join(GeoTolkSession, GeoTolkInterpretation.session_id == GeoTolkSession.id)
            .filter(
                GeoTolkSession.project_id == project_id,
                GeoTolkInterpretation.status == 'interpreted',
            )
        )
        if username:
            query = query.filter(GeoTolkSession.username == username)

        interps = query.order_by(GeoTolkInterpretation.filename).all()

        boreholes = []
        for interp in interps:
            layers      = interp.get_layers()
            parsed_data = interp.get_parsed_data()

            # Extract coordinates from raw SND content or from parsed_data
            coords = parsed_data.get('coords')
            if not coords and interp.snd_raw_content:
                coords = parse_snd_header_coords(interp.snd_raw_content)

            boreholes.append({
                'id':        interp.id,
                'filename':  interp.filename,
                'max_depth': interp.max_depth,
                'num_layers': len(layers),
                'x':         coords.get('x') if coords else None,
                'y':         coords.get('y') if coords else None,
                'z':         coords.get('z') if coords else None,
                'layers':    layers,
                'sounding': {
                    'depth': parsed_data.get('depth', []),
                    'c2':    parsed_data.get('c2', []),
                    'c3':    parsed_data.get('c3', []),
                    'c4':    parsed_data.get('c4', []),
                },
                'events': {
                    'spyling': parsed_data.get('spyling', []),
                    'slag':    parsed_data.get('slag', []),
                },
            })

        return jsonify({
            'success':    True,
            'project_id': project_id,
            'count':      len(boreholes),
            'boreholes':  boreholes,
        })
    finally:
        db.close()


@geotolk_bp.route('/gh/borehole/<int:interp_id>', methods=['GET'])
def gh_get_borehole(interp_id: int):
    """
    Get full borehole data with layers — designed for Grasshopper consumption.

    The layer list is ordered top-to-bottom and each layer contains:
        type  — soil type string (e.g. "leire", "sand", "fjell", "morene", etc.)
        start — layer top depth [m]
        end   — layer bottom depth [m]
    """
    db = get_db_session()
    try:
        interp = (
            db.query(GeoTolkInterpretation)
            .filter(GeoTolkInterpretation.id == interp_id)
            .first()
        )
        if not interp:
            return jsonify({'error': 'Borehole not found'}), 404

        if interp.status != 'interpreted':
            return jsonify({'error': 'Borehole has not been interpreted yet'}), 400

        layers      = interp.get_layers()
        parsed_data = interp.get_parsed_data()

        # Extract coordinates from raw SND content or from parsed_data
        coords = parsed_data.get('coords')
        if not coords and interp.snd_raw_content:
            coords = parse_snd_header_coords(interp.snd_raw_content)

        return jsonify({
            'success': True,
            'borehole': {
                'id':         interp.id,
                'filename':   interp.filename,
                'max_depth':  interp.max_depth,
                'x':          coords.get('x') if coords else None,
                'y':          coords.get('y') if coords else None,
                'z':          coords.get('z') if coords else None,
                'layers':     layers,
                'sounding': {
                    'depth': parsed_data.get('depth', []),
                    'c2':    parsed_data.get('c2', []),
                    'c3':    parsed_data.get('c3', []),
                    'c4':    parsed_data.get('c4', []),
                },
                'events': {
                    'spyling': parsed_data.get('spyling', []),
                    'slag':    parsed_data.get('slag', []),
                },
            },
        })
    finally:
        db.close()

