# -*- coding: utf-8 -*-
"""
Modeling Activity Routes
=========================
REST API for modeling activities — creating activities, uploading Excel/IFC,
receiving GH optimization results, and serving downloads.

Blueprint prefix: /api/modeling
"""

import json
from datetime import datetime, timezone

from flask import Blueprint, request, jsonify, send_file
import io

from core.database import get_db_session
from core.models import ModelingActivity
from activities.modeling import service as blob_svc

modeling_bp = Blueprint('modeling', __name__)


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _activity_or_404(db, activity_id: int):
    a = db.query(ModelingActivity).filter_by(id=activity_id).first()
    if not a:
        return None, jsonify({'error': 'Activity not found'}), 404
    return a, None, None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@modeling_bp.route('/api/modeling/activities', methods=['GET'])
def list_activities():
    """List modeling activities for a project."""
    project_id = request.args.get('project_id', type=int)
    username   = request.args.get('username', '')
    db = get_db_session()
    try:
        q = db.query(ModelingActivity)
        if project_id:
            q = q.filter_by(project_id=project_id)
        elif username:
            q = q.filter_by(username=username)
        activities = q.order_by(ModelingActivity.created_at.desc()).all()
        return jsonify({'activities': [a.to_dict() for a in activities]})
    finally:
        db.close()


@modeling_bp.route('/api/modeling/activities', methods=['POST'])
def create_activity():
    """Create a new modeling activity."""
    data = request.get_json() or {}
    name       = data.get('name', '').strip()
    username   = data.get('username', '').strip()
    project_id = data.get('project_id')

    if not name or not username:
        return jsonify({'error': 'name and username are required'}), 400

    db = get_db_session()
    try:
        activity = ModelingActivity(
            project_id=project_id,
            name=name,
            username=username,
            status='active',
        )
        db.add(activity)
        db.commit()
        db.refresh(activity)
        return jsonify({'activity': activity.to_dict()}), 201
    finally:
        db.close()


@modeling_bp.route('/api/modeling/activities/<int:activity_id>', methods=['GET'])
def get_activity(activity_id: int):
    """Get a single modeling activity."""
    db = get_db_session()
    try:
        a, err, code = _activity_or_404(db, activity_id)
        if err:
            return err, code
        return jsonify({'activity': a.to_dict()})
    finally:
        db.close()


@modeling_bp.route('/api/modeling/activities/<int:activity_id>', methods=['DELETE'])
def delete_activity(activity_id: int):
    """Delete a modeling activity."""
    db = get_db_session()
    try:
        a, err, code = _activity_or_404(db, activity_id)
        if err:
            return err, code
        db.delete(a)
        db.commit()
        return jsonify({'success': True})
    finally:
        db.close()


# ---------------------------------------------------------------------------
# File upload — Excel
# ---------------------------------------------------------------------------

@modeling_bp.route('/api/modeling/activities/<int:activity_id>/upload/excel',
                   methods=['POST'])
def upload_excel(activity_id: int):
    """
    Upload an Excel file for this activity.
    Accepts multipart/form-data with field 'file'.
    """
    db = get_db_session()
    try:
        a, err, code = _activity_or_404(db, activity_id)
        if err:
            return err, code

        if 'file' not in request.files:
            return jsonify({'error': 'No file field in request'}), 400

        f = request.files['file']
        filename = f.filename or 'input.xlsx'
        data     = f.read()

        blob_name = blob_svc.blob_name_excel(
            a.project_id or 0, activity_id, filename
        )
        blob_svc.upload_file(blob_name, data,
                             'application/vnd.openxmlformats-officedocument'
                             '.spreadsheetml.sheet')

        a.excel_blob_name = blob_name
        a.excel_filename  = filename
        a.status          = 'has_excel'
        a.updated_at      = datetime.now(timezone.utc)
        db.commit()

        return jsonify({'success': True, 'blob_name': blob_name,
                        'activity': a.to_dict()})
    finally:
        db.close()


# ---------------------------------------------------------------------------
# File upload — GH results (IFC + run-report.json + run-summary.md)
# ---------------------------------------------------------------------------

@modeling_bp.route('/api/modeling/activities/<int:activity_id>/upload/results',
                   methods=['POST'])
def upload_results(activity_id: int):
    """
    Upload GH optimization results.
    Accepts multipart/form-data:
      - ifc     : IFC file (optional)
      - report  : run-report.json
      - summary : run-summary.md (optional)
    """
    db = get_db_session()
    try:
        a, err, code = _activity_or_404(db, activity_id)
        if err:
            return err, code

        # run-report.json (required)
        if 'report' not in request.files:
            return jsonify({'error': 'report (run-report.json) is required'}), 400

        report_bytes = request.files['report'].read()
        try:
            report_data = json.loads(report_bytes.decode('utf-8'))
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            return jsonify({'error': f'Invalid JSON in report: {exc}'}), 400

        a.run_report_json = json.dumps(report_data)

        # run-summary.md (optional)
        if 'summary' in request.files:
            summary_bytes = request.files['summary'].read()
            a.run_summary_md = summary_bytes.decode('utf-8', errors='replace')

        # IFC file (optional)
        if 'ifc' in request.files:
            ifc_file = request.files['ifc']
            ifc_filename = ifc_file.filename or 'model.ifc'
            ifc_data     = ifc_file.read()
            blob_name = blob_svc.blob_name_ifc(
                a.project_id or 0, activity_id, ifc_filename
            )
            blob_svc.upload_file(blob_name, ifc_data, 'application/octet-stream')
            a.ifc_blob_name = blob_name
            a.ifc_filename  = ifc_filename

        a.status     = 'has_results'
        a.updated_at = datetime.now(timezone.utc)
        db.commit()

        return jsonify({'success': True, 'activity': a.to_dict()})
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Results data — for visualisation
# ---------------------------------------------------------------------------

@modeling_bp.route('/api/modeling/activities/<int:activity_id>/results',
                   methods=['GET'])
def get_results(activity_id: int):
    """Return parsed run-report and summary for visualisation."""
    db = get_db_session()
    try:
        a, err, code = _activity_or_404(db, activity_id)
        if err:
            return err, code

        if not a.run_report_json:
            return jsonify({'error': 'No results uploaded yet'}), 404

        return jsonify({
            'run_report':  json.loads(a.run_report_json),
            'run_summary': a.run_summary_md or '',
            'activity':    a.to_dict(),
        })
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Downloads — returns SAS URL redirect
# ---------------------------------------------------------------------------

@modeling_bp.route('/api/modeling/activities/<int:activity_id>/download/excel',
                   methods=['GET'])
def download_excel(activity_id: int):
    """Return a short-lived SAS download URL for the Excel file."""
    db = get_db_session()
    try:
        a, err, code = _activity_or_404(db, activity_id)
        if err:
            return err, code
        if not a.excel_blob_name:
            return jsonify({'error': 'No Excel file uploaded'}), 404

        url = blob_svc.get_sas_url(a.excel_blob_name)
        return jsonify({'url': url, 'filename': a.excel_filename})
    finally:
        db.close()


@modeling_bp.route('/api/modeling/activities/<int:activity_id>/download/ifc',
                   methods=['GET'])
def download_ifc(activity_id: int):
    """Return a short-lived SAS download URL for the IFC file."""
    db = get_db_session()
    try:
        a, err, code = _activity_or_404(db, activity_id)
        if err:
            return err, code
        if not a.ifc_blob_name:
            return jsonify({'error': 'No IFC file uploaded'}), 404

        url = blob_svc.get_sas_url(a.ifc_blob_name)
        return jsonify({'url': url, 'filename': a.ifc_filename})
    finally:
        db.close()
