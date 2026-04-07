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

from config import PLAXIS_HOST
from core.database import get_db_session
from core.models import PlaxisCalculation
from activities.plaxis.runner.runner import run_plaxis_extraction

plaxis_bp = Blueprint('plaxis', __name__, url_prefix='/api/plaxis')

# In-process session store (one entry per user session).
# Replace with Redis or a DB table when multi-worker deployment is needed.
_plaxis_sessions: Dict[str, Any] = {}


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
# Connection
# ---------------------------------------------------------------------------

@plaxis_bp.route('/connect', methods=['POST'])
def connect():
    """Connect to a running Plaxis Input server."""
    data       = request.get_json() or {}
    port       = data.get('port')
    password   = data.get('password')
    host       = data.get('host') or PLAXIS_HOST
    session_id = data.get('session_id', 'default')

    if not port or not password:
        return jsonify({'error': 'port and password are required'}), 400

    try:
        port = int(port)
    except ValueError:
        return jsonify({'error': 'port must be a number'}), 400

    try:
        from plxscripting.easy import new_server
        s_i, g_i = new_server(host, port, password=password)
        _plaxis_sessions[session_id] = {
            'port': port, 'password': password, 'host': host,
            's_i': s_i, 'g_i': g_i, 'connected': True,
        }
        return jsonify({'success': True, 'message': f'Connected to Plaxis at {host}:{port}.', 'session_id': session_id})
    except ImportError:
        return jsonify({'success': False, 'error': 'plxscripting is not installed on the server. Install it with: pip install plxscripting'}), 500
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
    """Return structures and phases from the open Plaxis model."""
    session_id = request.args.get('session_id', 'default')
    session    = _plaxis_sessions.get(session_id)

    if not session or not session.get('g_i'):
        return jsonify({
            'success': False,
            'error': 'Not connected to Plaxis. Connect first via the connection panel.',
        }), 400

    g_i = session['g_i']
    try:
        from activities.plaxis.extraction.model_info import extract_model_info
        info = extract_model_info(g_i)
        info.update({'success': True})
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
    host           = data.get('host') or session.get('host') or PLAXIS_HOST

    if not input_port or not input_password:
        return jsonify({'error': 'Plaxis port and password are required. Connect first.'}), 400

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

    try:
        calc.status = 'running'
        db.commit()

        results = run_plaxis_extraction(
            host=host,
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
# Parametric run (single iteration)
# ---------------------------------------------------------------------------

@plaxis_bp.route('/parametric-run', methods=['POST'])
def parametric_run():
    """Execute one iteration of a parametric study.

    Modifies the KS soil's Su (and optionally gamma), optionally moves the
    sheet pile bottom, runs calculations, and extracts FoS / displacement /
    capacity for the requested phases.  Returns a single-row result dict.

    The endpoint is stateless per-call — the frontend loops over combos and
    calls this endpoint once per combination.
    """
    data = request.get_json() or {}

    session_id = data.get('session_id', 'default')
    session    = _plaxis_sessions.get(session_id, {})
    g_i = session.get('g_i')

    if not g_i:
        return jsonify({'success': False, 'error': 'Not connected to Plaxis. Connect first.'}), 400
    host = data.get('host') or session.get('host') or PLAXIS_HOST

    ks_soil   = data.get('ks_soil')
    plate     = data.get('plate')
    su_val    = data.get('su')
    depth     = data.get('depth')
    fos_phase = data.get('fos_phase')
    disp_phase = data.get('disp_phase')
    cap_phase  = data.get('cap_phase')

    try:
        from activities.plaxis.parametric.runner import run_single_parametric
        result = run_single_parametric(
            g_i=g_i,
            s_i=session.get('s_i'),
            ks_soil_name=ks_soil,
            plate_name=plate,
            su=su_val,
            depth=depth,
            fos_phase=fos_phase,
            disp_phase=disp_phase,
            cap_phase=cap_phase,
            output_port=data.get('output_port'),
            output_password=data.get('output_password'),
            host=host,
        )
        return jsonify(result)
    except Exception as exc:
        return jsonify({'success': False, 'error': str(exc)}), 500


# ---------------------------------------------------------------------------
# Water-level sensitivity (single iteration)
# ---------------------------------------------------------------------------

@plaxis_bp.route('/water-sensitivity-run', methods=['POST'])
def water_sensitivity_run():
    """Execute one iteration of a water-level sensitivity study.

    Sets the borehole water head to the requested level, runs calculations,
    and extracts FoS / displacement / capacity for the requested phases.
    """
    data = request.get_json() or {}

    session_id = data.get('session_id', 'default')
    session    = _plaxis_sessions.get(session_id, {})
    g_i = session.get('g_i')
    host = data.get('host') or session.get('host') or PLAXIS_HOST

    water_level = data.get('water_level')
    if water_level is None:
        return jsonify({'error': 'water_level is required'}), 400

    if not g_i:
        return jsonify({'success': False, 'error': 'Not connected to Plaxis. Connect first.'}), 400
    try:
        from activities.plaxis.parametric.water_sensitivity import run_single_water_level
        result = run_single_water_level(
            g_i=g_i,
            s_i=session.get('s_i'),
            water_level=float(water_level),
            plate_name=data.get('plate'),
            fos_phase=data.get('fos_phase'),
            disp_phase=data.get('disp_phase'),
            cap_phase=data.get('cap_phase'),
            output_port=data.get('output_port'),
            output_password=data.get('output_password'),
            host=host,
        )
        return jsonify(result)
    except Exception as exc:
        return jsonify({'success': False, 'error': str(exc)}), 500


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

