# -*- coding: utf-8 -*-
"""
Projects Routes
===============
Flask Blueprint for project management and activity logging.

Endpoints:
    GET  /api/projects                          — List projects for current user
    POST /api/projects                          — Create a new project
    DELETE /api/projects/<id>                   — Delete a project
    POST /api/projects/<id>/access              — Grant a user access
    GET  /api/projects/<id>/activities          — Get project activity log
    POST /api/projects/<id>/activities          — Log a project activity

    GET  /api/activity                          — Get recent activity for a user
    POST /api/activity                          — Log a user activity
"""

from flask import Blueprint, jsonify, request
from sqlalchemy import or_

from core.database import get_db_session
from core.models import Project, ProjectAccess, RecentActivity

projects_bp = Blueprint('projects', __name__, url_prefix='/api')


# ---------------------------------------------------------------------------
# Projects
# ---------------------------------------------------------------------------

@projects_bp.route('/projects', methods=['GET'])
def list_projects():
    """Return all projects the requesting user has access to."""
    username = request.args.get('username', '')
    if not username:
        return jsonify({'error': 'username is required'}), 400

    db = get_db_session()
    try:
        projects = db.query(Project).filter(
            Project.is_active == True,  # noqa: E712
            or_(
                Project.created_by == username,
                Project.id.in_(
                    db.query(ProjectAccess.project_id).filter(
                        ProjectAccess.username == username
                    )
                ),
            ),
        ).order_by(Project.updated_at.desc()).all()

        return jsonify({'projects': [p.to_dict() for p in projects], 'count': len(projects)})
    finally:
        db.close()


@projects_bp.route('/projects', methods=['POST'])
def create_project():
    """Create a new project and grant access to the specified users."""
    data          = request.get_json() or {}
    name          = data.get('name')
    description   = data.get('description', '')
    created_by    = data.get('created_by')
    allowed_users = data.get('allowed_users', [])

    if not name or not created_by:
        return jsonify({'error': 'name and created_by are required'}), 400

    db = get_db_session()
    try:
        project = Project(name=name, description=description, created_by=created_by)
        db.add(project)
        db.flush()

        for username in allowed_users:
            if username and username != created_by:
                db.add(ProjectAccess(
                    project_id=project.id,
                    username=username,
                    granted_by=created_by,
                ))

        db.commit()
        return jsonify({
            'success': True,
            'project': project.to_dict(),
            'message': f'Project "{name}" created.',
        }), 201
    except Exception as exc:
        db.rollback()
        return jsonify({'error': str(exc)}), 500
    finally:
        db.close()


@projects_bp.route('/projects/<int:project_id>', methods=['DELETE'])
def delete_project(project_id: int):
    """Delete a project (only the creator may do this)."""
    username = request.args.get('username', '')

    db = get_db_session()
    try:
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return jsonify({'error': 'Project not found'}), 404
        if project.created_by != username:
            return jsonify({'error': 'Only the project creator may delete it'}), 403

        db.delete(project)
        db.commit()
        return jsonify({'success': True, 'message': 'Project deleted.'})
    finally:
        db.close()


@projects_bp.route('/projects/<int:project_id>/access', methods=['POST'])
def add_access(project_id: int):
    """Grant an additional user access to a project."""
    data       = request.get_json() or {}
    username   = data.get('username')
    granted_by = data.get('granted_by')

    if not username:
        return jsonify({'error': 'username is required'}), 400

    db = get_db_session()
    try:
        existing = db.query(ProjectAccess).filter(
            ProjectAccess.project_id == project_id,
            ProjectAccess.username   == username,
        ).first()
        if existing:
            return jsonify({'message': 'User already has access.'}), 200

        db.add(ProjectAccess(project_id=project_id, username=username, granted_by=granted_by))
        db.commit()
        return jsonify({'success': True, 'message': f'Access granted to {username}.'}), 201
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Activity log per project
# ---------------------------------------------------------------------------

@projects_bp.route('/projects/<int:project_id>/activities', methods=['GET'])
def get_project_activities(project_id: int):
    """Return the activity log for a specific project."""
    limit = request.args.get('limit', 10, type=int)

    db = get_db_session()
    try:
        activities = db.query(RecentActivity).filter(
            RecentActivity.project_id == project_id
        ).order_by(RecentActivity.timestamp.desc()).limit(limit).all()
        return jsonify({'activities': [a.to_dict() for a in activities], 'count': len(activities)})
    finally:
        db.close()


@projects_bp.route('/projects/<int:project_id>/activities', methods=['POST'])
def log_project_activity(project_id: int):
    """Log an activity against a specific project."""
    data          = request.get_json() or {}
    username      = data.get('username')
    activity_type = data.get('activity_type')
    activity_name = data.get('activity_name')

    if not (username and activity_type and activity_name):
        return jsonify({'error': 'username, activity_type, and activity_name are required'}), 400

    db = get_db_session()
    try:
        db.add(RecentActivity(
            username=username, project_id=project_id,
            activity_type=activity_type, activity_name=activity_name,
        ))
        db.commit()
        return jsonify({'success': True}), 201
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Global activity log
# ---------------------------------------------------------------------------

@projects_bp.route('/activity', methods=['GET'])
def get_activity():
    """Return recent activity for a user across all projects."""
    username = request.args.get('username', '')
    limit    = request.args.get('limit', 10, type=int)

    if not username:
        return jsonify({'error': 'username is required'}), 400

    db = get_db_session()
    try:
        activities = db.query(RecentActivity).filter(
            RecentActivity.username == username
        ).order_by(RecentActivity.timestamp.desc()).limit(limit).all()
        return jsonify({'activities': [a.to_dict() for a in activities], 'count': len(activities)})
    finally:
        db.close()


@projects_bp.route('/activity', methods=['POST'])
def log_activity():
    """Log a user activity."""
    data          = request.get_json() or {}
    username      = data.get('username')
    activity_type = data.get('activity_type')
    activity_name = data.get('activity_name')

    if not (username and activity_type and activity_name):
        return jsonify({'error': 'username, activity_type, and activity_name are required'}), 400

    db = get_db_session()
    try:
        db.add(RecentActivity(
            username=username,
            activity_type=activity_type,
            activity_name=activity_name,
            activity_data=data.get('activity_data'),
        ))
        db.commit()
        return jsonify({'success': True}), 201
    finally:
        db.close()
