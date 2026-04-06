# -*- coding: utf-8 -*-
"""
Modeling Activity Routes
=========================
REST API for modeling activities — creating activities, uploading Excel/IFC,
receiving GH optimization results, tørmur optimisation, and downloads.

Blueprint prefix: /api/modeling
"""

import json
import uuid
from datetime import datetime, timezone

from flask import Blueprint, request, jsonify, send_file, Response
import io

from sqlalchemy import func

from core.database import get_db_session
from core.models import ModelingActivity, Project, ProjectAccess
from activities.modeling import service as blob_svc
from activities.modeling.tormur_engine import TorrmurInput, calculate, volume_per_meter
from activities.modeling.tormur_optimizer import (
    OptimizationRange, optimize_wall, SectionResult, _safety_factors,
)
from activities.modeling.polyline_utils import sections_from_polylines

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


# ---------------------------------------------------------------------------
# Tørmur — helpers
# ---------------------------------------------------------------------------

def _round(val, decimals=3):
    """Round a numeric value safely, returning None for non-numeric."""
    if val is None or val == '':
        return None
    try:
        return round(float(val), decimals)
    except (TypeError, ValueError):
        return None


def _build_run_report(
    results: list[SectionResult],
    base_params: dict,
    opt_range: OptimizationRange,
) -> dict:
    """Build run-report.json from optimisation results."""
    sections = []
    for r in results:
        # Re-run calculation to get accurate safety factors per section
        inp_dict = {**base_params, 'H': r.height, 'bt': r.bt, 'bb': r.bb}
        inp = TorrmurInput(**{
            k: v for k, v in inp_dict.items()
            if k in TorrmurInput.__dataclass_fields__
        })
        res = calculate(inp) if r.height > 0 else None
        sf = _safety_factors(res) if res else {
            'SlidingFactor': 0, 'OverturningFactor': 0, 'BearingFactor': 0,
            'SlidingOk': True, 'OverturningOk': True, 'BearingOk': True, 'AllOk': True,
        }

        # Determine governing check
        governing = 'Sliding'
        if not sf.get('BearingOk', True):
            governing = 'Bearing'
        elif not sf.get('SlidingOk', True):
            governing = 'Sliding'
        elif sf.get('AllOk', True):
            # All OK — pick the one closest to its limit
            ratios = [
                ('Sliding', sf.get('SlidingFactor', 99)),
                ('Overturning', sf.get('OverturningFactor', 99)),
                ('Bearing', sf.get('BearingFactor', 99)),
            ]
            governing = min(ratios, key=lambda x: x[1])[0]
        sf['GoverningCheck'] = governing

        # Build diagnostics from engine output
        diag = {}
        if res:
            diag = {
                'EA': _round(res.get('B38')),
                'T': _round(res.get('B39')),
                'Gvekt': _round(res.get('B40')),
                'RV': _round(res.get('B41')),
                'RH': _round(res.get('B42')),
                'e': _round(res.get('H40')),
                'qV': _round(res.get('H41')),
                'rb': _round(res.get('H42')),
                'rb_krav': _round(res.get('H43')),
                'b0': _round(res.get('H44')),
                'sigma_V': _round(res.get('M44')),
                'Ng': _round(res.get('M40')),
                'Nq': _round(res.get('M41')),
                'KA': _round(res.get('B35')),
                'KA_korr': _round(res.get('B36')),
                'K_delta': _round(res.get('B37')),
                'tan_rho_bak': _round(res.get('B27')),
                'tan_rho_under': _round(res.get('B26')),
                'foundation_check': res.get('H45', ''),
                'bearing_check': res.get('M45', ''),
                'msg_D46': res.get('D46', ''),
                'msg_I46': res.get('I46', ''),
            }

        sections.append({
            'Index': len(sections),
            'Station': r.station,
            'Height': r.height,
            'TopWidth': round(r.bt, 3),
            'BottomWidth': round(r.bb, 3),
            'SmoothedTopWidth': round(r.bt, 3),
            'SmoothedBottomWidth': round(r.bb, 3),
            'FaceAngleDeg': r.face_angle_deg,
            'SmoothedFaceAngleDeg': r.face_angle_deg,
            'Area': round(r.volume_per_m, 3),
            'VolumePerMeter': round(r.volume_per_m, 3),
            'TopPoint': r.top_point,
            'BottomPoint': r.bot_point,
            'Checks': sf,
            'Diagnostics': diag,
        })

    total_length = max(r.station for r in results) if results else 0
    total_volume = sum(r.volume_per_m for r in results) * (
        (total_length / max(len(results) - 1, 1)) if len(results) > 1 else 1
    )

    return {
        'ProjectName': 'Tørmur',
        'RunId': uuid.uuid4().hex,
        'CreatedUtc': datetime.now(timezone.utc).isoformat(),
        'Config': {
            'WallType': 'tormur_v220',
            'SlidingMin': 1.5,
            'OverturningMin': 2.0,
            'BearingMin': 3.0,
            'TopWidthMin': opt_range.bt_min,
            'TopWidthMax': opt_range.bt_max,
            'TopWidthStep': opt_range.bt_step,
            'BottomWidthMin': opt_range.bb_min,
            'BottomWidthMax': opt_range.bb_max,
            'BottomWidthStep': opt_range.bb_step,
            **{k: v for k, v in base_params.items()
               if k not in ('H', 'bt', 'bb')},
        },
        'Sections': sections,
        'TotalLength': round(total_length, 2),
        'TotalVolume': round(total_volume, 2),
    }


def _build_summary_md(report: dict) -> str:
    """Generate markdown summary from a run report."""
    n = len(report.get('Sections', []))
    n_fail = sum(1 for s in report.get('Sections', [])
                 if not s.get('Checks', {}).get('AllOk', True))
    lines = [
        '# Tørmur optimeringsrapport',
        f'- RunId: {report.get("RunId", "?")}',
        f'- Dato: {report.get("CreatedUtc", "?")}',
        f'- Seksjoner: {n}',
        f'- Totallengde: {report.get("TotalLength", 0):.2f} m',
        f'- Totalvolum: {report.get("TotalVolume", 0):.2f} m³',
        f'- Feilede seksjoner: {n_fail}',
        '',
        '## Parametere',
    ]
    cfg = report.get('Config', {})
    for k, v in cfg.items():
        if k in ('WallType', 'SlidingMin', 'OverturningMin', 'BearingMin'):
            continue
        lines.append(f'- {k}: {v}')
    return '\n'.join(lines)


# ---------------------------------------------------------------------------
# Tørmur — store / retrieve parameters
# ---------------------------------------------------------------------------

@modeling_bp.route('/api/modeling/activities/<int:activity_id>/tormur-params',
                   methods=['POST'])
def save_tormur_params(activity_id: int):
    """Save tørmur V220 parameters on the activity (as JSON)."""
    db = get_db_session()
    try:
        a, err, code = _activity_or_404(db, activity_id)
        if err:
            return err, code

        params = request.get_json() or {}
        a.tormur_params_json = json.dumps(params)
        a.updated_at = datetime.now(timezone.utc)
        db.commit()
        return jsonify({'success': True, 'activity': a.to_dict()})
    finally:
        db.close()


@modeling_bp.route('/api/modeling/activities/<int:activity_id>/tormur-params',
                   methods=['GET'])
def get_tormur_params(activity_id: int):
    """Retrieve saved tørmur V220 parameters."""
    db = get_db_session()
    try:
        a, err, code = _activity_or_404(db, activity_id)
        if err:
            return err, code
        params = json.loads(a.tormur_params_json) if a.tormur_params_json else {}
        return jsonify({'params': params, 'activity': a.to_dict()})
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Tørmur — single-section check (live preview)
# ---------------------------------------------------------------------------

@modeling_bp.route('/api/modeling/tormur/check', methods=['POST'])
def tormur_check():
    """Run a single V220 check and return results (for live preview)."""
    data = request.get_json() or {}

    fields = {f.name for f in TorrmurInput.__dataclass_fields__.values()}
    kwargs = {}
    for k, v in data.items():
        if k in fields:
            ftype = TorrmurInput.__dataclass_fields__[k].type
            if ftype == 'bool':
                kwargs[k] = bool(v)
            else:
                try:
                    kwargs[k] = float(v)
                except (TypeError, ValueError):
                    pass

    inp = TorrmurInput(**kwargs)
    res = calculate(inp)

    return jsonify({
        'ok': res.is_ok(),
        'foundation_check': res.get('H45'),
        'bearing_check': res.get('M45'),
        'messages': {
            'A33': res.get('A33', ''),
            'A34': res.get('A34', ''),
            'D46': res.get('D46', ''),
            'I46': res.get('I46', ''),
        },
        'key_values': {
            'EA': res.get('B38'),
            'T': res.get('B39'),
            'Gvekt': res.get('B40'),
            'RV': res.get('B41'),
            'RH': res.get('B42'),
            'e': res.get('H40'),
            'qV': res.get('H41'),
            'rb': res.get('H42'),
            'rb_krav': res.get('H43'),
            'b0': res.get('H44'),
            'sigma_V': res.get('M44'),
            'Ng': res.get('M40'),
            'Nq': res.get('M41'),
        },
    })


# ---------------------------------------------------------------------------
# Tørmur — optimisation (from UI with explicit section heights)
# ---------------------------------------------------------------------------

@modeling_bp.route('/api/modeling/activities/<int:activity_id>/optimize',
                   methods=['POST'])
def optimize_tormur(activity_id: int):
    """
    Run per-section tørmur optimisation.

    Body JSON::

        {
            "params": { ... V220 params (excl. H, bt, bb) ... },
            "sections": [{"station": 0, "height": 3.5}, ...],
            "bt_range": [min, max, step],
            "bb_range": [min, max, step],
            "smooth_window": 3
        }
    """
    db = get_db_session()
    try:
        a, err, code = _activity_or_404(db, activity_id)
        if err:
            return err, code

        data = request.get_json() or {}
        params = data.get('params', {})
        sections = data.get('sections', [])
        if not sections:
            return jsonify({'error': 'sections array is required'}), 400

        bt_r = data.get('bt_range', [0.4, 3.0, 0.1])
        bb_r = data.get('bb_range', [0.4, 5.0, 0.1])
        opt = OptimizationRange(
            bt_min=bt_r[0], bt_max=bt_r[1], bt_step=bt_r[2],
            bb_min=bb_r[0], bb_max=bb_r[1], bb_step=bb_r[2],
        )
        smooth = data.get('smooth_window', 3)

        results = optimize_wall(params, sections, opt, smooth)
        report = _build_run_report(results, params, opt)
        summary = _build_summary_md(report)

        a.run_report_json = json.dumps(report)
        a.run_summary_md = summary
        a.tormur_params_json = json.dumps(params)
        a.status = 'has_results'
        a.updated_at = datetime.now(timezone.utc)
        db.commit()

        return jsonify({
            'success': True,
            'report': report,
            'summary': summary,
            'activity': a.to_dict(),
        })
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Tørmur — optimisation from Grasshopper (polylines → sections → optimise)
# ---------------------------------------------------------------------------

def _find_project(db, project_name: str, username: str):
    """Find an existing project by name where user is owner or has access.

    Returns ``(project, None, None)`` on success or ``(None, error_response, code)``.
    """
    # Case-insensitive name match, owner OR in access list
    project = (
        db.query(Project)
        .filter(func.lower(Project.name) == project_name.lower())
        .filter(
            (func.lower(Project.created_by) == username.lower())
            | Project.id.in_(
                db.query(ProjectAccess.project_id)
                .filter(func.lower(ProjectAccess.username) == username.lower())
            )
        )
        .first()
    )
    if not project:
        return None, jsonify({
            'error': f'Prosjekt "{project_name}" ble ikke funnet for bruker "{username}". '
                     'Opprett prosjektet i RamGAP først.'
        }), 404
    return project, None, None


def _find_activity(db, activity_name: str, project_id: int):
    """Find an existing activity by name within a project.

    Returns ``(activity, None, None)`` on success or ``(None, error_response, code)``.
    """
    activity = (
        db.query(ModelingActivity)
        .filter(
            func.lower(ModelingActivity.name) == activity_name.lower(),
            ModelingActivity.project_id == project_id,
        )
        .first()
    )
    if not activity:
        return None, jsonify({
            'error': f'Aktivitet "{activity_name}" ble ikke funnet i prosjektet. '
                     'Opprett aktiviteten i RamGAP først og sett V220-parametere.'
        }), 404
    return activity, None, None


@modeling_bp.route('/api/modeling/optimize-from-gh', methods=['POST'])
def optimize_from_gh_by_name():
    """
    Grasshopper endpoint (name-based): send project name, activity name
    and polylines — V220 params are loaded from the activity (set in RamGAP).

    Body JSON::

        {
            "username":        "TBLM",
            "project_name":    "Støttemur E18",
            "activity_name":   "Kjøring 1",
            "top_polyline":    [[x,y,z], ...],
            "bottom_polyline": [[x,y,z], ...],
            "interval":        1.0,
            "bt_range":        [0.4, 3.0, 0.1],
            "bb_range":        [0.4, 5.0, 0.1],
            "smooth_window":   3
        }
    """
    db = get_db_session()
    try:
        data = request.get_json() or {}
        username      = data.get('username', '').strip()
        project_name  = data.get('project_name', '').strip()
        activity_name = data.get('activity_name', '').strip()

        if not username:
            return jsonify({'error': 'username is required'}), 400
        if not project_name:
            return jsonify({'error': 'project_name is required'}), 400
        if not activity_name:
            return jsonify({'error': 'activity_name is required'}), 400

        top_pts  = [tuple(p) for p in data.get('top_polyline', [])]
        bot_pts  = [tuple(p) for p in data.get('bottom_polyline', [])]
        interval = data.get('interval', 1.0)

        if len(top_pts) < 2 or len(bot_pts) < 2:
            return jsonify({
                'error': 'top_polyline and bottom_polyline must have >= 2 points'
            }), 400

        project, err, code = _find_project(db, project_name, username)
        if err:
            return err, code

        activity, err, code = _find_activity(db, activity_name, project.id)
        if err:
            return err, code

        # Load V220 params from activity (set in RamGAP frontend)
        if not activity.tormur_params_json:
            return jsonify({
                'error': f'Ingen V220-parametere lagret for aktivitet "{activity_name}". '
                         'Sett parametere i RamGAP før du kjører fra Grasshopper.'
            }), 400

        params = json.loads(activity.tormur_params_json)

        sections = sections_from_polylines(top_pts, bot_pts, interval)
        if not sections:
            return jsonify({'error': 'Could not generate sections from polylines'}), 400

        bt_r = data.get('bt_range', [0.4, 3.0, 0.1])
        bb_r = data.get('bb_range', [0.4, 5.0, 0.1])
        opt  = OptimizationRange(
            bt_min=bt_r[0], bt_max=bt_r[1], bt_step=bt_r[2],
            bb_min=bb_r[0], bb_max=bb_r[1], bb_step=bb_r[2],
        )
        smooth = data.get('smooth_window', 3)

        results = optimize_wall(params, sections, opt, smooth)
        report  = _build_run_report(results, params, opt)
        summary = _build_summary_md(report)

        activity.run_report_json  = json.dumps(report)
        activity.run_summary_md   = summary
        activity.status           = 'has_results'
        activity.updated_at       = datetime.now(timezone.utc)
        db.commit()

        return jsonify({
            'success':     True,
            'activity_id': activity.id,
            'report':      report,
            'summary':     summary,
            'activity':    activity.to_dict(),
        })
    finally:
        db.close()


@modeling_bp.route('/api/modeling/activities/<int:activity_id>/optimize-from-gh',
                   methods=['POST'])
def optimize_from_gh(activity_id: int):
    """
    Grasshopper endpoint: send polylines + params, receive optimised sections.

    Body JSON::

        {
            "username":        "TBLM",
            "top_polyline":    [[x,y,z], ...],
            "bottom_polyline": [[x,y,z], ...],
            "interval":        1.0,
            "params":          { ... V220 params ... },
            "bt_range":        [0.4, 3.0, 0.1],
            "bb_range":        [0.4, 5.0, 0.1],
            "smooth_window":   3
        }
    """
    db = get_db_session()
    try:
        a, err, code = _activity_or_404(db, activity_id)
        if err:
            return err, code

        data = request.get_json() or {}
        top_pts = [tuple(p) for p in data.get('top_polyline', [])]
        bot_pts = [tuple(p) for p in data.get('bottom_polyline', [])]
        interval = data.get('interval', 1.0)
        params = data.get('params', {})

        if len(top_pts) < 2 or len(bot_pts) < 2:
            return jsonify({
                'error': 'top_polyline and bottom_polyline must have >= 2 points'
            }), 400

        sections = sections_from_polylines(top_pts, bot_pts, interval)
        if not sections:
            return jsonify({'error': 'Could not generate sections from polylines'}), 400

        bt_r = data.get('bt_range', [0.4, 3.0, 0.1])
        bb_r = data.get('bb_range', [0.4, 5.0, 0.1])
        opt = OptimizationRange(
            bt_min=bt_r[0], bt_max=bt_r[1], bt_step=bt_r[2],
            bb_min=bb_r[0], bb_max=bb_r[1], bb_step=bb_r[2],
        )
        smooth = data.get('smooth_window', 3)

        results = optimize_wall(params, sections, opt, smooth)
        report = _build_run_report(results, params, opt)
        summary = _build_summary_md(report)

        a.run_report_json = json.dumps(report)
        a.run_summary_md = summary
        a.tormur_params_json = json.dumps(params)
        a.status = 'has_results'
        a.updated_at = datetime.now(timezone.utc)
        db.commit()

        return jsonify({
            'success': True,
            'report': report,
            'summary': summary,
            'activity': a.to_dict(),
        })
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Tørmur — Excel export
# ---------------------------------------------------------------------------

@modeling_bp.route('/api/modeling/activities/<int:activity_id>/export/excel',
                   methods=['GET'])
def export_excel(activity_id: int):
    """Generate and return an .xlsx summary of the optimisation results."""
    db = get_db_session()
    try:
        a, err, code = _activity_or_404(db, activity_id)
        if err:
            return err, code
        if not a.run_report_json:
            return jsonify({'error': 'No results to export'}), 404

        report = json.loads(a.run_report_json)
        sections = report.get('Sections', [])
        config = report.get('Config', {})

        try:
            import openpyxl
        except ImportError:
            return jsonify({'error': 'openpyxl not installed on server'}), 500

        wb = openpyxl.Workbook()

        # Sheet 1: Summary
        ws1 = wb.active
        ws1.title = 'Sammendrag'
        ws1.append(['Tørmur optimeringsrapport'])
        ws1.append(['RunId', report.get('RunId', '')])
        ws1.append(['Dato', report.get('CreatedUtc', '')])
        ws1.append(['Antall seksjoner', len(sections)])
        ws1.append(['Totallengde (m)', report.get('TotalLength', 0)])
        ws1.append(['Totalvolum (m³)', report.get('TotalVolume', 0)])
        n_fail = sum(1 for s in sections
                     if not s.get('Checks', {}).get('AllOk', True))
        ws1.append(['Feilede seksjoner', n_fail])

        # Sheet 2: Parameters
        ws2 = wb.create_sheet('Parametere')
        ws2.append(['Parameter', 'Verdi'])
        for k, v in config.items():
            ws2.append([k, v])

        # Sheet 3: Sections
        ws3 = wb.create_sheet('Seksjoner')
        headers = ['Stasjon', 'Høyde', 'Topp-bredde', 'Bunn-bredde',
                    'Vinkel (°)', 'Areal (m²)', 'Glidning SF',
                    'Velting SF', 'Bæreevne SF', 'Godkjent']
        ws3.append(headers)
        for s in sections:
            ch = s.get('Checks', {})
            ws3.append([
                s.get('Station', 0),
                s.get('Height', 0),
                s.get('SmoothedTopWidth', s.get('TopWidth', 0)),
                s.get('SmoothedBottomWidth', s.get('BottomWidth', 0)),
                s.get('SmoothedFaceAngleDeg', s.get('FaceAngleDeg', 0)),
                s.get('Area', 0),
                ch.get('SlidingFactor', 0),
                ch.get('OverturningFactor', 0),
                ch.get('BearingFactor', 0),
                'OK' if ch.get('AllOk') else 'NEI',
            ])

        buf = io.BytesIO()
        wb.save(buf)
        buf.seek(0)

        filename = f'Tormur_{a.name}_{report.get("RunId", "")[:8]}.xlsx'
        return Response(
            buf.getvalue(),
            mimetype='application/vnd.openxmlformats-officedocument'
                     '.spreadsheetml.sheet',
            headers={
                'Content-Disposition': f'attachment; filename="{filename}"'
            },
        )
    finally:
        db.close()
