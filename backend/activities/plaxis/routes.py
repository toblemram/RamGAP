# -*- coding: utf-8 -*-
"""
Plaxis Routes
=============
Flask Blueprint with all REST API endpoints for the Plaxis activity.

All Plaxis computation goes through the job queue (PlaxisWorker):
    POST /api/plaxis/jobs                 — Submit a job (frontend → worker)
    GET  /api/plaxis/jobs/<id>            — Poll job status (frontend polling)
    GET  /api/plaxis/jobs/poll            — Claim next pending job (worker polling)
    POST /api/plaxis/jobs/<id>/complete   — Submit result (worker → backend)

Other endpoints:
    POST /api/plaxis/ai-quality-check     — AI model review
    POST /api/plaxis/ai-report            — AI calculation report
    GET/POST /api/plaxis/calculations     — Saved calculation history
    GET  /api/plaxis/calculations/<id>    — Get a specific calculation
    POST /api/plaxis/calculations/<id>/rerun — Re-run via job queue
"""

import json
from datetime import datetime
from typing import Any, Dict

from flask import Blueprint, jsonify, request

from config import PLAXIS_HOST
from core.database import get_db_session
from core.models import PlaxisCalculation, PlaxisJob
from activities.plaxis.script_builder import (
    build_connect_script,
    build_run_script,
    build_parametric_script,
    build_water_sensitivity_script,
    build_sensitivity_script,
)

plaxis_bp = Blueprint('plaxis', __name__, url_prefix='/api/plaxis')


# ---------------------------------------------------------------------------
# Azure OpenAI helper
# ---------------------------------------------------------------------------

def _get_ai_client():
    """Return an Azure OpenAI client."""
    from openai import AzureOpenAI
    from config import AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY, AZURE_OPENAI_API_VERSION
    return AzureOpenAI(
        azure_endpoint=AZURE_OPENAI_ENDPOINT,
        api_key=AZURE_OPENAI_API_KEY,
        api_version=AZURE_OPENAI_API_VERSION,
    )


def _get_deployment():
    from config import AZURE_OPENAI_DEPLOYMENT
    return AZURE_OPENAI_DEPLOYMENT or 'gpt-4o'


# ---------------------------------------------------------------------------
# AI-assisted features
# ---------------------------------------------------------------------------

@plaxis_bp.route('/ai-quality-check', methods=['POST'])
def ai_quality_check():
    """AI quality check of the connected Plaxis model."""
    data = request.get_json() or {}
    model_data = data.get('model_data', {})

    structures = model_data.get('structures', {})
    phases     = model_data.get('phases', [])
    geometry   = model_data.get('geometry', {})
    layers     = geometry.get('soil_layers', [])

    parts = ["=== PLAXIS 2D MODELL ===\n"]
    parts.append("JORDPROFIL:")
    for l in layers:
        parts.append(f"  {l.get('material','?')}: topp={l.get('top')}, bunn={l.get('bottom')}")
    parts.append(f"Vannstand: {geometry.get('water_head', '?')} m")
    parts.append(f"Modellgrenser: x=[{geometry.get('xmin')}, {geometry.get('xmax')}], "
                 f"y=[{geometry.get('ymin')}, {geometry.get('ymax')}]")

    parts.append("\nSTRUKTURER:")
    for pl in structures.get('plates', []):
        mat = pl.get('material', {})
        parts.append(
            f"  Plate: {pl['name']}, ({pl.get('x1')},{pl.get('y1')}) til ({pl.get('x2')},{pl.get('y2')}), "
            f"Material: {mat.get('name','?')}, EA={mat.get('EA1','?')}, EI={mat.get('EI','?')}, d={mat.get('d','?')}"
        )
    for anc in structures.get('node_to_node_anchors', []) + structures.get('fixed_end_anchors', []):
        mat = anc.get('material', {})
        parts.append(f"  Anker: {anc.get('name','?')}, Material: {mat.get('name','?')}, EA={mat.get('EA','?')}")
    for eb in structures.get('embedded_beams', []):
        parts.append(f"  EmbeddedBeam: {eb.get('name','?')}")

    parts.append("\nFASER:")
    for ph in phases:
        parts.append(f"  {ph.get('number','-')}. {ph['name']} (Type: {ph.get('calc_type','?')}, Forrige: {ph.get('previous','\u2014')})")

    model_description = "\n".join(parts)

    system_prompt = (
        "Du er en erfaren geoteknisk ingeni\u00f8r som gjennomg\u00e5r Plaxis 2D-modeller. "
        "Gj\u00f8r en grundig kvalitetssjekk av modellen. Vurder:\n"
        "1. **Geometri og randbetingelser**: Er modellgrensene store nok? Jordlag logisk ordnet?\n"
        "2. **Materialegenskaper**: Er verdier realistiske for norske grunnforhold? Mangler noe?\n"
        "3. **Strukturer**: Er spuntlengde rimelig ift. utgraving? Mangler interfaces?\n"
        "4. **Faser**: Er faserekkef\u00f8lgen logisk? Mangler sikkerhetsfase (phi/c-reduksjon)?\n"
        "5. **Vannforhold**: Er vannstand realistisk?\n\n"
        "Bruk ikoner: \u2705 OK, \u26a0\ufe0f advarsel, \u274c feil.\n"
        "Skriv p\u00e5 norsk. Referer til de faktiske verdiene i modellen.\n"
        "Formater som Markdown med overskrifter."
    )

    try:
        client = _get_ai_client()
        response = client.chat.completions.create(
            model=_get_deployment(),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": model_description},
            ],
        )
        return jsonify({'success': True, 'report': response.choices[0].message.content})
    except Exception as exc:
        return jsonify({'success': False, 'error': str(exc)}), 500


@plaxis_bp.route('/ai-report', methods=['POST'])
def ai_report():
    """Generate a professional AI calculation report from results."""
    data = request.get_json() or {}
    calc_type  = data.get('calc_type', 'unknown')
    config     = data.get('config', {})
    results    = data.get('results', [])
    model_data = data.get('model_data', {})

    structures = model_data.get('structures', {})
    geometry   = model_data.get('geometry', {})

    parts = ["=== BEREGNINGSRESULTATER ===\n"]
    parts.append(f"Beregningstype: {calc_type}")

    if calc_type == 'parametric_spunt':
        parts.append(f"KS-jordlag: {config.get('ks_soil','?')}")
        parts.append(f"Spunt: {config.get('plate','?')}")
        parts.append(f"Su-verdier: {config.get('su_values','?')}")
    elif calc_type == 'water_sensitivity':
        parts.append(f"Spunt: {config.get('plate','?')}")
        parts.append(f"Vannstander: {config.get('water_values','?')}")

    parts.append(f"\nAntall kj\u00f8ringer: {len(results)}")
    parts.append("\nRESULTATTABELL:")
    for row in results[:30]:
        parts.append(f"  {row}")

    plates = structures.get('plates', [])
    if plates:
        pl = plates[0]
        mat = pl.get('material', {})
        parts.append(f"\nSPUNTPROFIL: {mat.get('name','?')}, EA={mat.get('EA1','?')}, "
                     f"EI={mat.get('EI','?')}, d={mat.get('d','?')}")
    layers = geometry.get('soil_layers', [])
    if layers:
        parts.append("JORDLAG: " + ", ".join(
            f"{l.get('material','?')} ({l.get('top')}\u2192{l.get('bottom')})" for l in layers))
    parts.append(f"Vannstand: {geometry.get('water_head','?')} m")

    context = "\n".join(parts)

    system_prompt = (
        "Du er en erfaren geoteknisk r\u00e5dgiver som skriver profesjonelle beregningsrapporter "
        "for spuntkonstruksjoner i Norge. Basert p\u00e5 resultatene nedenfor, skriv en "
        "beregningsrapport med f\u00f8lgende struktur:\n\n"
        "## 1. Innledning\nKort beskrivelse av beregningen og form\u00e5let.\n\n"
        "## 2. Modellbeskrivelse\nGeometri, materialer, jordprofil, vannstand.\n\n"
        "## 3. Resultater\nOppsummer resultatene. Fremhev kritiske verdier (laveste FoS, "
        "maksimale deformasjoner og krefter). Bruk tabellformat.\n\n"
        "## 4. Vurdering\nSammenlign med Eurokode 7 / NS-EN (FoS \u2265 1.4 for ULS). "
        "Vurder deformasjonsniv\u00e5 og spuntkapasitet.\n\n"
        "## 5. Konklusjon og anbefalinger\nKlare anbefalinger basert p\u00e5 resultatene.\n\n"
        "Skriv p\u00e5 norsk. Bruk fagterminologi. V\u00e6r presis med tall. Formater som Markdown."
    )

    try:
        client = _get_ai_client()
        response = client.chat.completions.create(
            model=_get_deployment(),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": context},
            ],
        )
        return jsonify({'success': True, 'report': response.choices[0].message.content})
    except Exception as exc:
        return jsonify({'success': False, 'error': str(exc)}), 500


# ---------------------------------------------------------------------------
# Calculation history
# ---------------------------------------------------------------------------

@plaxis_bp.route('/calculations', methods=['GET', 'POST'])
def calculations():
    """GET: list saved calculations.  POST: save a new calculation record."""
    if request.method == 'POST':
        return _save_calculation()
    return _list_calculations()


def _save_calculation():
    """Persist a completed calculation (parametric / water-sensitivity / extraction)."""
    data = request.get_json() or {}

    activity_name = data.get('activity_name', 'Plaxis-beregning')
    username      = data.get('username', 'default')
    project_id    = data.get('project_id')
    calc_type     = data.get('calc_type', 'unknown')         # parametric_spunt | water_sensitivity | extract_results
    config_json   = data.get('config')                       # full input config
    results_json  = data.get('results')                      # list of result rows

    summary = data.get('summary', '')

    db = get_db_session()
    try:
        calc = PlaxisCalculation(
            project_id=project_id,
            username=username,
            activity_name=activity_name,
            status='completed',
            input_port=data.get('input_port'),
            output_port=data.get('output_port'),
            results_json=json.dumps({
                'calc_type': calc_type,
                'config':    config_json,
                'rows':      results_json,
                'summary':   summary,
            }),
        )
        calc.completed_at = datetime.utcnow()
        db.add(calc)
        db.commit()
        return jsonify({'success': True, 'calculation_id': calc.id, 'calculation': calc.to_dict()})
    except Exception as exc:
        db.rollback()
        return jsonify({'success': False, 'error': str(exc)}), 500
    finally:
        db.close()


def _list_calculations():
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

        host = data.get('host') or PLAXIS_HOST
        code = build_run_script(
            host, int(input_port), input_password,
            output_port, output_password or input_password,
            job,
        )
        plaxis_job = PlaxisJob(
            session_id=session_id,
            job_type='run',
            code=code,
            status='pending',
        )
        db.add(plaxis_job)
        db.commit()
        return jsonify({
            'success': True,
            'job_id': plaxis_job.id,
            'status': 'pending',
            'message': 'Re-run submitted to PlaxisWorker job queue.',
        })

    except Exception as exc:
        db.rollback()
        return jsonify({'error': str(exc)}), 500
    finally:
        try:
            db.close()
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Job queue  (PlaxisWorker communication)
# ---------------------------------------------------------------------------

# Map from frontend job_type to a script-builder call
_BUILDERS = {
    'connect':           lambda d: build_connect_script(
                             d['host'], int(d['port']), d['password']),
    'run':               lambda d: build_run_script(
                             d['host'], int(d['port']), d['password'],
                             d.get('output_port'), d.get('output_password'),
                             d['job']),
    'parametric':        lambda d: build_parametric_script(
                             d['host'], int(d['port']), d['password'],
                             d.get('output_port'), d.get('output_password'),
                             d['ks_soil'], d['plate'], float(d['su']),
                             d.get('depth'), d.get('fos_phase'),
                             d.get('disp_phase'), d.get('cap_phase')),
    'water_sensitivity': lambda d: build_water_sensitivity_script(
                             d['host'], int(d['port']), d['password'],
                             d.get('output_port'), d.get('output_password'),
                             float(d['water_level']), d.get('plate'),
                             d.get('fos_phase'), d.get('disp_phase'),
                             d.get('cap_phase')),
    'sensitivity':       lambda d: build_sensitivity_script(
                             d['host'], int(d['port']), d['password'],
                             d.get('output_port'), d.get('output_password'),
                             d['param_type'], float(d['param_value']),
                             d.get('soil_name'), d.get('plate'),
                             d.get('fos_phase'), d.get('disp_phase'),
                             d.get('cap_phase')),
}


@plaxis_bp.route('/jobs', methods=['POST'])
def submit_job():
    """Frontend submits a job. Backend generates the script and inserts it into the DB."""
    data = request.get_json() or {}
    job_type   = data.get('job_type')
    session_id = data.get('session_id', 'default')

    if not job_type or job_type not in _BUILDERS:
        return jsonify({'error': f'Invalid job_type. Must be one of: {list(_BUILDERS)}'}), 400

    try:
        code = _BUILDERS[job_type](data)
    except KeyError as exc:
        return jsonify({'error': f'Missing required parameter: {exc}'}), 400

    db = get_db_session()
    try:
        job = PlaxisJob(
            session_id=session_id,
            job_type=job_type,
            code=code,
            status='pending',
        )
        db.add(job)
        db.commit()
        return jsonify({'success': True, 'job_id': job.id, 'status': 'pending'})
    except Exception as exc:
        db.rollback()
        return jsonify({'error': str(exc)}), 500
    finally:
        db.close()


@plaxis_bp.route('/jobs/<int:job_id>', methods=['GET'])
def get_job(job_id: int):
    """Frontend polls for job status / result."""
    db = get_db_session()
    try:
        job = db.query(PlaxisJob).filter(PlaxisJob.id == job_id).first()
        if not job:
            return jsonify({'error': 'Job not found'}), 404
        return jsonify({'success': True, 'job': job.to_dict()})
    finally:
        db.close()


@plaxis_bp.route('/jobs/poll', methods=['GET'])
def poll_job():
    """PlaxisWorker polls for the next pending job. Returns oldest pending job."""
    db = get_db_session()
    try:
        job = (db.query(PlaxisJob)
               .filter(PlaxisJob.status == 'pending')
               .order_by(PlaxisJob.created_at.asc())
               .first())
        if not job:
            return jsonify({'success': True, 'job': None})
        # Mark as running
        job.status = 'running'
        db.commit()
        return jsonify({
            'success': True,
            'job': {
                'id': job.id,
                'job_type': job.job_type,
                'code': job.code,
            },
        })
    except Exception as exc:
        db.rollback()
        return jsonify({'error': str(exc)}), 500
    finally:
        db.close()


@plaxis_bp.route('/jobs/<int:job_id>/complete', methods=['POST'])
def complete_job(job_id: int):
    """PlaxisWorker submits the result of a job."""
    data = request.get_json() or {}
    db = get_db_session()
    try:
        job = db.query(PlaxisJob).filter(PlaxisJob.id == job_id).first()
        if not job:
            return jsonify({'error': 'Job not found'}), 404

        result = data.get('result')
        error  = data.get('error')

        if error:
            job.status = 'failed'
            job.error  = str(error)
        else:
            job.status      = 'done'
            job.result_json = json.dumps(result) if result else None
        job.completed_at = datetime.utcnow()
        db.commit()
        return jsonify({'success': True})
    except Exception as exc:
        db.rollback()
        return jsonify({'error': str(exc)}), 500
    finally:
        db.close()

