# -*- coding: utf-8 -*-
"""
RamGAP Flask Backend
REST API for RamGAP application
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
from database.db import init_db, get_db_session
from database.models import Base, Project, ProjectAccess, RecentActivity, PlaxisCalculation
from sqlalchemy import or_
from datetime import datetime
import json

app = Flask(__name__)
CORS(app)

# Initialize database on startup
init_db()


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'message': 'RamGAP Backend is running'
    })


@app.route('/api/status', methods=['GET'])
def get_status():
    """Get application status"""
    return jsonify({
        'status': 'ok',
        'ready': True,
        'message': 'Klar til videre utvikling'
    })


# ==================== PROJECT ENDPOINTS ====================

@app.route('/api/projects', methods=['GET'])
def get_projects():
    """Get all projects the user has access to"""
    username = request.args.get('username', '')
    if not username:
        return jsonify({'error': 'Username required'}), 400
    
    db = get_db_session()
    try:
        # Get projects where user is creator OR has explicit access
        projects = db.query(Project).filter(
            Project.is_active == True,
            or_(
                Project.created_by == username,
                Project.id.in_(
                    db.query(ProjectAccess.project_id).filter(
                        ProjectAccess.username == username
                    )
                )
            )
        ).order_by(Project.updated_at.desc()).all()
        
        return jsonify({
            'projects': [p.to_dict() for p in projects],
            'count': len(projects)
        })
    finally:
        db.close()


@app.route('/api/projects', methods=['POST'])
def create_project():
    """Create a new project"""
    data = request.get_json()
    
    name = data.get('name')
    description = data.get('description', '')
    created_by = data.get('created_by')
    allowed_users = data.get('allowed_users', [])
    
    if not name or not created_by:
        return jsonify({'error': 'Name and created_by are required'}), 400
    
    db = get_db_session()
    try:
        # Create project
        project = Project(
            name=name,
            description=description,
            created_by=created_by
        )
        db.add(project)
        db.flush()  # Get the project ID
        
        # Add access for allowed users
        for username in allowed_users:
            if username and username != created_by:
                access = ProjectAccess(
                    project_id=project.id,
                    username=username,
                    granted_by=created_by
                )
                db.add(access)
        
        db.commit()
        
        return jsonify({
            'success': True,
            'project': project.to_dict(),
            'message': f'Prosjekt "{name}" opprettet'
        }), 201
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/projects/<int:project_id>', methods=['DELETE'])
def delete_project(project_id):
    """Delete a project"""
    username = request.args.get('username', '')
    
    db = get_db_session()
    try:
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return jsonify({'error': 'Project not found'}), 404
        
        # Only creator can delete
        if project.created_by != username:
            return jsonify({'error': 'Only creator can delete project'}), 403
        
        db.delete(project)
        db.commit()
        
        return jsonify({'success': True, 'message': 'Prosjekt slettet'})
    finally:
        db.close()


@app.route('/api/projects/<int:project_id>/access', methods=['POST'])
def add_project_access(project_id):
    """Add user access to a project"""
    data = request.get_json()
    username = data.get('username')
    granted_by = data.get('granted_by')
    
    if not username:
        return jsonify({'error': 'Username required'}), 400
    
    db = get_db_session()
    try:
        # Check if access already exists
        existing = db.query(ProjectAccess).filter(
            ProjectAccess.project_id == project_id,
            ProjectAccess.username == username
        ).first()
        
        if existing:
            return jsonify({'message': 'User already has access'}), 200
        
        access = ProjectAccess(
            project_id=project_id,
            username=username,
            granted_by=granted_by
        )
        db.add(access)
        db.commit()
        
        return jsonify({'success': True, 'message': f'Tilgang gitt til {username}'}), 201
    finally:
        db.close()


# ==================== RECENT ACTIVITY ENDPOINTS ====================

@app.route('/api/activity', methods=['GET'])
def get_recent_activity():
    """Get recent activity for a user"""
    username = request.args.get('username', '')
    limit = request.args.get('limit', 10, type=int)
    
    if not username:
        return jsonify({'error': 'Username required'}), 400
    
    db = get_db_session()
    try:
        activities = db.query(RecentActivity).filter(
            RecentActivity.username == username
        ).order_by(RecentActivity.timestamp.desc()).limit(limit).all()
        
        return jsonify({
            'activities': [a.to_dict() for a in activities],
            'count': len(activities)
        })
    finally:
        db.close()


@app.route('/api/activity', methods=['POST'])
def log_activity():
    """Log user activity"""
    data = request.get_json()
    
    username = data.get('username')
    activity_type = data.get('activity_type')
    activity_name = data.get('activity_name')
    activity_data = data.get('activity_data')
    
    if not username or not activity_type or not activity_name:
        return jsonify({'error': 'username, activity_type, and activity_name required'}), 400
    
    db = get_db_session()
    try:
        activity = RecentActivity(
            username=username,
            activity_type=activity_type,
            activity_name=activity_name,
            activity_data=activity_data
        )
        db.add(activity)
        db.commit()
        
        return jsonify({'success': True}), 201
    finally:
        db.close()


# ==================== PROJECT ACTIVITY ENDPOINTS ====================

@app.route('/api/projects/<int:project_id>/activities', methods=['GET'])
def get_project_activities(project_id):
    """Get activities for a specific project"""
    limit = request.args.get('limit', 10, type=int)
    
    db = get_db_session()
    try:
        activities = db.query(RecentActivity).filter(
            RecentActivity.project_id == project_id
        ).order_by(RecentActivity.timestamp.desc()).limit(limit).all()
        
        return jsonify({
            'activities': [a.to_dict() for a in activities],
            'count': len(activities)
        })
    finally:
        db.close()


@app.route('/api/projects/<int:project_id>/activities', methods=['POST'])
def log_project_activity(project_id):
    """Log activity for a specific project"""
    data = request.get_json()
    
    username = data.get('username')
    activity_type = data.get('activity_type')
    activity_name = data.get('activity_name')
    
    if not username or not activity_type or not activity_name:
        return jsonify({'error': 'username, activity_type, and activity_name required'}), 400
    
    db = get_db_session()
    try:
        activity = RecentActivity(
            username=username,
            project_id=project_id,
            activity_type=activity_type,
            activity_name=activity_name
        )
        db.add(activity)
        db.commit()
        
        return jsonify({'success': True}), 201
    finally:
        db.close()


# ==================== PLAXIS ENDPOINTS ====================

# Store Plaxis connection info in memory (per-session in production, use proper session management)
plaxis_sessions = {}

@app.route('/api/plaxis/connect', methods=['POST'])
def plaxis_connect():
    """Connect to Plaxis server"""
    data = request.get_json()
    
    port = data.get('port')
    password = data.get('password')
    session_id = data.get('session_id', 'default')
    
    if not port or not password:
        return jsonify({'error': 'Port and password required'}), 400
    
    try:
        port = int(port)
    except ValueError:
        return jsonify({'error': 'Port must be a number'}), 400
    
    # Try to connect using plxscripting
    try:
        from plxscripting.easy import new_server
        s_i, g_i = new_server('localhost', port, password=password)
        
        # Store connection info
        plaxis_sessions[session_id] = {
            'port': port,
            'password': password,
            's_i': s_i,
            'g_i': g_i,
            'connected': True
        }
        
        return jsonify({
            'success': True,
            'message': 'Connected to Plaxis successfully',
            'session_id': session_id
        })
    except ImportError:
        # plxscripting not available - store session anyway for later use
        plaxis_sessions[session_id] = {
            'port': port,
            'password': password,
            's_i': None,
            'g_i': None,
            'connected': False,
            'plxscripting_available': False
        }
        return jsonify({
            'success': True,
            'warning': 'plxscripting not available in this Python. Calculations will try to connect directly.',
            'session_id': session_id
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@app.route('/api/plaxis/disconnect', methods=['POST'])
def plaxis_disconnect():
    """Disconnect from Plaxis"""
    data = request.get_json()
    session_id = data.get('session_id', 'default')
    
    if session_id in plaxis_sessions:
        del plaxis_sessions[session_id]
    
    return jsonify({'success': True, 'message': 'Disconnected'})


@app.route('/api/plaxis/model-info', methods=['GET'])
def plaxis_get_model_info():
    """Get structures and phases from Plaxis model"""
    session_id = request.args.get('session_id', 'default')
    
    # Check if session exists and has a valid connection
    session = plaxis_sessions.get(session_id)
    if not session or not session.get('g_i'):
        # Return demo data if not connected
        return jsonify({
            'success': True,
            'demo_mode': True,
            'structures': {
                'plates': [
                    {'name': 'Spunt_venstre', 'display_name': 'Name: Spunt_venstre, x = 0.0', 'x': 0.0, 'type': 'plate'},
                    {'name': 'Spunt_høyre', 'display_name': 'Name: Spunt_høyre, x = 15.0', 'x': 15.0, 'type': 'plate'}
                ],
                'embedded_beams': [],
                'node_to_node_anchors': [
                    {'name': 'Anker_1', 'display_name': 'Name: Anker_1, (0.0,-2.0) → (5.0,-4.0)', 'x1': 0.0, 'y1': -2.0, 'x2': 5.0, 'y2': -4.0, 'type': 'node_to_node_anchor'}
                ],
                'fixed_end_anchors': [],
                'geogrids': []
            },
            'phases': [
                {'id': 0, 'name': 'Initial phase', 'msf_enabled': False, 'ux_enabled': False, 'capacity_enabled': False},
                {'id': 1, 'name': 'Installasjon spunt', 'msf_enabled': False, 'ux_enabled': False, 'capacity_enabled': False},
                {'id': 2, 'name': 'Utgraving nivå 1', 'msf_enabled': False, 'ux_enabled': False, 'capacity_enabled': False},
                {'id': 3, 'name': 'Installasjon anker', 'msf_enabled': False, 'ux_enabled': False, 'capacity_enabled': False},
                {'id': 4, 'name': 'Utgraving til bunn', 'msf_enabled': False, 'ux_enabled': False, 'capacity_enabled': False},
                {'id': 5, 'name': 'FoS analyse', 'msf_enabled': False, 'ux_enabled': False, 'capacity_enabled': False}
            ]
        })
    
    g_i = session['g_i']
    
    try:
        structures = {
            'plates': [],
            'embedded_beams': [],
            'node_to_node_anchors': [],
            'fixed_end_anchors': [],
            'geogrids': []
        }
        
        g_i.gotostructures()
        
        # Extract Plates
        if hasattr(g_i, 'Plates'):
            for plate in g_i.Plates:
                structures['plates'].append({
                    'name': plate.Name.value,
                    'display_name': f"Name: {plate.Name.value}, x = {plate.Parent.First.x.value}",
                    'x': plate.Parent.First.x.value,
                    'type': 'plate'
                })
        
        # Extract Embedded Beam Rows
        if hasattr(g_i, 'EmbeddedBeamRows'):
            for ebr in g_i.EmbeddedBeamRows:
                structures['embedded_beams'].append({
                    'name': ebr.Name.value,
                    'display_name': f"Name: {ebr.Name.value}, x = {ebr.Parent.First.x.value}",
                    'x': ebr.Parent.First.x.value,
                    'type': 'embedded_beam'
                })
        
        # Extract Node to Node Anchors
        if hasattr(g_i, 'NodeToNodeAnchors'):
            for n2n in g_i.NodeToNodeAnchors:
                structures['node_to_node_anchors'].append({
                    'name': n2n.Name.value,
                    'display_name': f"Name: {n2n.Name.value}, ({n2n.Parent.First.x.value},{n2n.Parent.First.y.value}) → ({n2n.Parent.Second.x.value},{n2n.Parent.Second.y.value})",
                    'x1': n2n.Parent.First.x.value,
                    'y1': n2n.Parent.First.y.value,
                    'x2': n2n.Parent.Second.x.value,
                    'y2': n2n.Parent.Second.y.value,
                    'type': 'node_to_node_anchor'
                })
        
        # Extract Fixed End Anchors
        if hasattr(g_i, 'FixedEndAnchors'):
            for fea in g_i.FixedEndAnchors:
                structures['fixed_end_anchors'].append({
                    'name': fea.Name.value,
                    'display_name': f"Name: {fea.Name.value}, ({fea.Parent.x.value},{fea.Parent.y.value})",
                    'x': fea.Parent.x.value,
                    'y': fea.Parent.y.value,
                    'type': 'fixed_end_anchor'
                })
        
        # Extract Geogrids
        if hasattr(g_i, 'Geogrids'):
            for geo in g_i.Geogrids:
                structures['geogrids'].append({
                    'name': geo.Name.value,
                    'display_name': f"Name: {geo.Name.value}, ({geo.Parent.First.x.value},{geo.Parent.First.y.value}) → ({geo.Parent.Second.x.value},{geo.Parent.Second.y.value})",
                    'x1': geo.Parent.First.x.value,
                    'y1': geo.Parent.First.y.value,
                    'x2': geo.Parent.Second.x.value,
                    'y2': geo.Parent.Second.y.value,
                    'type': 'geogrid'
                })
        
        # Extract Phases
        g_i.gotostages()
        phase_names = g_i.Phases.Identification.value
        
        phases = []
        for i, name in enumerate(phase_names):
            phases.append({
                'id': i,
                'name': name,
                'msf_enabled': False,
                'ux_enabled': False,
                'capacity_enabled': False
            })
        
        return jsonify({
            'success': True,
            'demo_mode': False,
            'structures': structures,
            'phases': phases
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/plaxis/status', methods=['GET'])
def plaxis_status():
    """Check Plaxis connection status"""
    session_id = request.args.get('session_id', 'default')
    
    if session_id in plaxis_sessions:
        session = plaxis_sessions[session_id]
        return jsonify({
            'connected': True,
            'port': session['port']
        })
    
    return jsonify({
        'connected': False
    })


@app.route('/api/plaxis/run', methods=['POST'])
def plaxis_run_extraction():
    """Run Plaxis extraction with the provided job configuration"""
    data = request.get_json()
    
    session_id = data.get('session_id', 'default')
    job = data.get('job')
    project_id = data.get('project_id')
    activity_name = data.get('activity_name', 'Plaxis beregning')
    
    # Get port and password from request (new way) or session (old way)
    input_port = data.get('input_port')
    input_password = data.get('input_password')
    output_port = data.get('output_port')
    output_password = data.get('output_password')
    
    if not job:
        return jsonify({'error': 'Job configuration required'}), 400
    
    # If no direct ports provided, try to get from session
    if not input_port or not input_password:
        if session_id in plaxis_sessions:
            session = plaxis_sessions[session_id]
            input_port = input_port or session.get('port')
            input_password = input_password or session.get('password')
    
    # Create calculation record in database
    db_session = get_db_session()
    calc = PlaxisCalculation(
        project_id=project_id,
        username=session_id,
        activity_name=activity_name,
        status='started',
        input_port=input_port,
        output_port=output_port,
        output_path=job.get('resultsPath', {}).get('path')
    )
    
    # Extract structures and phases from job
    structures = job.get('structures', {})
    spunts = structures.get('plates', []) + structures.get('embedded_beams', [])
    anchors = (structures.get('node_to_node_anchors', []) + 
               structures.get('fixed_end_anchors', []))
    calc.set_structures(spunts, anchors)
    
    analysis = job.get('analysis', {})
    capacity_phases = analysis.get('capacity_check', {}).get('phases', [])
    msf_phases = analysis.get('msf', {}).get('phases', [])
    displacement_phases = analysis.get('displacement', {}).get('phases', [])
    displacement_component = analysis.get('displacement', {}).get('component', 'Ux')
    calc.set_phases(capacity_phases, msf_phases, displacement_phases)
    calc.displacement_component = displacement_component
    
    db_session.add(calc)
    db_session.commit()
    calc_id = calc.id
    
    # If still no ports, return demo mode
    if not input_port or not input_password:
        calc.status = 'completed'
        calc.completed_at = datetime.utcnow()
        calc.results_json = json.dumps({
            'demo_mode': True,
            'capacity': {'plates': {'Spunt_venstre': {'Utgraving til bunn': {'Nx': 245.3, 'Q': 89.2, 'M': 312.5}}}},
            'msf': {'FoS analyse': 1.32},
            'displacement': {'plates': {'Spunt_venstre': {'Utgraving til bunn': 23.5}}}
        })
        db_session.commit()
        db_session.close()
        
        return jsonify({
            'success': True,
            'demo_mode': True,
            'calculation_id': calc_id,
            'results': {
                'capacity': {'plates': {'Spunt_venstre': {'Utgraving til bunn': {'Nx': 245.3, 'Q': 89.2, 'M': 312.5}, 'FoS analyse': {'Nx': 267.8, 'Q': 95.4, 'M': 345.2}}}},
                'msf': {'FoS analyse': 1.32},
                'displacement': {'plates': {'Spunt_venstre': {'Utgraving til bunn': 23.5, 'FoS analyse': 28.1}}}
            },
            'output_file': 'Demo - ingen fil generert',
            'message': 'Demo-modus: Viser eksempelresultater. Oppgi Input/Output port og passord.'
        })
    
    try:
        # Update status to running
        calc.status = 'running'
        db_session.commit()
        
        # Import and run the extraction
        from plaxis.plaxis_runner import run_plaxis_extraction
        
        results = run_plaxis_extraction(
            input_port=input_port,
            input_password=input_password,
            output_port=output_port,
            output_password=output_password,
            job=job
        )
        
        # Update calculation with results
        if results.get('success'):
            calc.status = 'completed'
            calc.output_file = results.get('output_file')
            calc.results_json = json.dumps({
                'capacity': results.get('capacity', {}),
                'msf': results.get('msf', {}),
                'displacement': results.get('displacement', {})
            })
        else:
            calc.status = 'failed'
            calc.error_message = results.get('error') or '; '.join(results.get('errors', []))
        
        calc.completed_at = datetime.utcnow()
        db_session.commit()
        
        results['calculation_id'] = calc_id
        return jsonify(results)
        
    except ImportError as e:
        calc.status = 'failed'
        calc.error_message = f'Import error: {str(e)}'
        calc.completed_at = datetime.utcnow()
        db_session.commit()
        db_session.close()
        return jsonify({
            'success': False,
            'calculation_id': calc_id,
            'error': f'Import error: {str(e)}. Ensure plxscripting is available.'
        }), 500
    except Exception as e:
        calc.status = 'failed'
        calc.error_message = str(e)
        calc.completed_at = datetime.utcnow()
        db_session.commit()
        db_session.close()
        return jsonify({
            'success': False,
            'calculation_id': calc_id,
            'error': str(e)
        }), 500
    finally:
        db_session.close()


@app.route('/api/plaxis/calculations', methods=['GET'])
def get_plaxis_calculations():
    """Get list of Plaxis calculations, optionally filtered by project or user"""
    project_id = request.args.get('project_id', type=int)
    username = request.args.get('username')
    limit = request.args.get('limit', 20, type=int)
    
    db_session = get_db_session()
    try:
        query = db_session.query(PlaxisCalculation)
        
        if project_id:
            query = query.filter(PlaxisCalculation.project_id == project_id)
        if username:
            query = query.filter(PlaxisCalculation.username == username)
        
        calculations = query.order_by(PlaxisCalculation.started_at.desc()).limit(limit).all()
        
        return jsonify({
            'success': True,
            'calculations': [calc.to_dict() for calc in calculations]
        })
    finally:
        db_session.close()


@app.route('/api/plaxis/calculations/<int:calc_id>', methods=['GET'])
def get_plaxis_calculation(calc_id):
    """Get a specific Plaxis calculation by ID"""
    db_session = get_db_session()
    try:
        calc = db_session.query(PlaxisCalculation).filter(PlaxisCalculation.id == calc_id).first()
        if not calc:
            return jsonify({'error': 'Calculation not found'}), 404
        
        return jsonify({
            'success': True,
            'calculation': calc.to_dict()
        })
    finally:
        db_session.close()


@app.route('/api/plaxis/calculations/<int:calc_id>/rerun', methods=['POST'])
def rerun_plaxis_calculation(calc_id):
    """Re-run a previous Plaxis calculation with same parameters"""
    data = request.get_json() or {}
    
    db_session = get_db_session()
    try:
        # Get original calculation
        original = db_session.query(PlaxisCalculation).filter(PlaxisCalculation.id == calc_id).first()
        if not original:
            return jsonify({'error': 'Calculation not found'}), 404
        
        # Get new connection params (required for re-run)
        input_port = data.get('input_port') or original.input_port
        input_password = data.get('input_password')
        output_port = data.get('output_port') or original.output_port
        output_password = data.get('output_password')
        session_id = data.get('session_id', original.username)
        
        if not input_password:
            return jsonify({'error': 'Passord påkrevd for å kjøre på nytt'}), 400
        
        # Build job from original calculation
        structures = original.get_structures()
        phases = original.get_phases()
        
        job = {
            'structures': {
                'plates': structures['spunts'],
                'embedded_beams': [],
                'node_to_node_anchors': structures['anchors'],
                'fixed_end_anchors': [],
                'geogrids': []
            },
            'analysis': {
                'capacity_check': {
                    'enabled': len(phases['capacity']) > 0,
                    'phases': phases['capacity']
                },
                'msf': {
                    'enabled': len(phases['msf']) > 0,
                    'phases': phases['msf']
                },
                'displacement': {
                    'enabled': len(phases['displacement']) > 0,
                    'phases': phases['displacement'],
                    'component': original.displacement_component or 'Ux'
                }
            },
            'resultsPath': {
                'path': original.output_path or data.get('output_path', '')
            }
        }
        
        db_session.close()
        
        # Create new run request
        new_request = {
            'session_id': session_id,
            'job': job,
            'project_id': original.project_id,
            'input_port': input_port,
            'input_password': input_password,
            'output_port': output_port,
            'output_password': output_password
        }
        
        # Call the run endpoint logic directly
        with app.test_request_context(json=new_request):
            from flask import g
            g.rerun_data = new_request
        
        # Actually run it by posting to ourselves
        import requests as req
        response = req.post(
            'http://localhost:5050/api/plaxis/run',
            json=new_request,
            timeout=300
        )
        
        return jsonify(response.json())
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if db_session:
            db_session.close()


# ==================== LEGACY ENDPOINTS ====================

@app.route('/api/data', methods=['GET'])
def get_data():
    """Placeholder endpoint for data retrieval"""
    return jsonify({
        'data': [],
        'message': 'Ingen data ennå'
    })


@app.route('/api/data', methods=['POST'])
def create_data():
    """Placeholder endpoint for data creation"""
    data = request.get_json()
    return jsonify({
        'success': True,
        'data': data,
        'message': 'Data mottatt'
    }), 201


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5050)
