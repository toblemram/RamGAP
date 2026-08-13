# -*- coding: utf-8 -*-
"""
GAPI (Plaxis Agent) Routes
============================
Flask Blueprint exposing REST endpoints for the AI-powered Plaxis agent.

All code execution goes through the PlaxisWorker job queue so that the
backend never needs a direct connection to Plaxis — the worker runs on the
user's local machine next to Plaxis.

Additional endpoints for PLAXIS manual indexing and GAPI learnings.

Endpoints
---------
POST /api/plaxis-agent/chat
    Accept a user message, generate Plaxis code, optionally execute it via
    the PlaxisWorker, and return the result.

POST /api/plaxis-agent/execute
    Execute previously generated code via PlaxisWorker.

POST /api/plaxis-agent/upload-pdf
    Upload a PDF and extract its text for use as extra context.

GET  /api/plaxis-agent/status
    Check whether the knowledge base is available.

POST /api/plaxis-agent/connect
    Test the Plaxis connection through PlaxisWorker and store session params.

GET  /api/plaxis-agent/observer
    Get the current session observer log.
"""

import json
import time
import traceback
import threading

from flask import Blueprint, jsonify, request

from core.database import get_db_session
from core.models import PlaxisJob, GapiLearning
from activities.plaxis_agent.service import (
    chat_and_execute,
    execute_via_worker,
    generate_code,
    get_observer_log,
    run_pipeline_plan,
    run_pipeline_execute,
)
from activities.plaxis_agent.knowledge import ensure_loaded, extract_pdf_text
from activities.plaxis.script_builder import (
    build_agent_test_script,
    build_agent_exec_script,
    build_snapshot_script,
)

plaxis_agent_bp = Blueprint("plaxis_agent", __name__, url_prefix="/api/plaxis-agent")

# ---------------------------------------------------------------------------
# In-memory session storage — connection params + pending plan per session
# ---------------------------------------------------------------------------
_agent_sessions: dict = {}   # session_id -> {host, port, password, ...}
_pending_plans:  dict = {}   # session_id -> {plan, context, user_message, username}
_snapshot_inflight: set[str] = set()
_snapshot_lock = threading.Lock()


def _get_session(session_id: str) -> dict | None:
    return _agent_sessions.get(session_id)


def _start_snapshot_background(session_id: str, sess: dict) -> bool:
    """Kick off a background snapshot unless one is already running."""
    with _snapshot_lock:
        if session_id in _snapshot_inflight:
            return False
        _snapshot_inflight.add(session_id)

    def _bg_snapshot():
        try:
            snap_code = build_snapshot_script(
                host=sess["host"],
                port=sess["port"],
                password=sess["password"],
                output_port=sess.get("output_port"),
                output_password=sess.get("output_password"),
            )
            snap_result = _submit_and_wait(snap_code, session_id,
                                           job_type="agent_snapshot", timeout=180)
            if snap_result.get("success") and snap_result.get("snapshot"):
                _agent_sessions[session_id]["model_info"] = snap_result["snapshot"]
        except Exception as _e:
            print(f"Background snapshot error: {_e}")
        finally:
            with _snapshot_lock:
                _snapshot_inflight.discard(session_id)

    threading.Thread(target=_bg_snapshot, daemon=True).start()
    return True


# ---------------------------------------------------------------------------
# Helper: submit job to worker and wait for result
# ---------------------------------------------------------------------------

def _submit_and_wait(code: str, session_id: str, job_type: str = "agent",
                     timeout: int = 180, poll_interval: float = 1.0) -> dict:
    """Insert a PlaxisJob, wait for the worker to complete it, return result."""
    db = get_db_session()
    try:
        job = PlaxisJob(
            session_id=session_id,
            job_type=job_type,
            code=code,
            status="pending",
        )
        db.add(job)
        db.commit()
        job_id = job.id
    except Exception as exc:
        db.rollback()
        return {"success": False, "error": f"Kunne ikke opprette jobb: {exc}"}
    finally:
        db.close()

    # Poll until done / failed / timeout
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        time.sleep(poll_interval)
        db = get_db_session()
        try:
            job = db.query(PlaxisJob).filter(PlaxisJob.id == job_id).first()
            if not job:
                return {"success": False, "error": "Jobb forsvant fra databasen."}
            if job.status == "done":
                result = json.loads(job.result_json) if job.result_json else {}
                return result
            if job.status == "failed":
                return {"success": False, "error": job.error or "Jobb feilet i PlaxisWorker."}
            # still pending/running — keep waiting
        finally:
            db.close()

    return {"success": False, "error": f"Tidsavbrudd — PlaxisWorker svarte ikke innen {timeout}s. Kjører PlaxisWorker?"}


# ---------------------------------------------------------------------------
# POST /chat  — main agent endpoint
# ---------------------------------------------------------------------------

@plaxis_agent_bp.route("/chat", methods=["POST"])
def chat():
    """
    Body::

        {
            "message":     str,
            "session_id":  str,
            "history":     list | null,
            "pdf_text":    str | null,
            "auto_execute": bool,
            "selected_context": list | null,
        }
    """
    data = request.get_json(silent=True) or {}
    message = (data.get("message") or "").strip()
    if not message:
        return jsonify({"error": "Melding mangler."}), 400

    session_id = data.get("session_id", "default")
    history = data.get("history")
    pdf_text = data.get("pdf_text")
    auto_execute = data.get("auto_execute", False)
    selected_context = data.get("selected_context")

    try:
        if auto_execute:
            sess = _get_session(session_id)
            if not sess:
                return jsonify({
                    "error": "Ikke tilkoblet PLAXIS. Koble til først.",
                }), 400

            result = chat_and_execute(
                user_message=message,
                connection_params=sess,
                session_id=session_id,
                history=history,
                pdf_text=pdf_text,
                selected_context=selected_context,
                max_retries=2,
            )
        else:
            result = generate_code(
                message, history=history, pdf_text=pdf_text,
                selected_context=selected_context,
            )
            result.update({"output": "", "success": True, "error": None, "attempts": 0})

        return jsonify(result)

    except Exception as exc:
        traceback.print_exc()
        return jsonify({"error": str(exc)}), 500


# ---------------------------------------------------------------------------
# POST /execute  — execute previously generated code
# ---------------------------------------------------------------------------

@plaxis_agent_bp.route("/execute", methods=["POST"])
def execute():
    """
    Body::

        {"code": str, "session_id": str}
    """
    data = request.get_json(silent=True) or {}
    code = (data.get("code") or "").strip()
    session_id = data.get("session_id", "default")

    if not code:
        return jsonify({"error": "Ingen kode oppgitt."}), 400

    sess = _get_session(session_id)
    if not sess:
        return jsonify({"error": "Ikke tilkoblet PLAXIS."}), 400

    result = execute_via_worker(code, sess, session_id)
    return jsonify(result)


# ---------------------------------------------------------------------------
# POST /upload-pdf  — extract text from an uploaded PDF
# ---------------------------------------------------------------------------

@plaxis_agent_bp.route("/upload-pdf", methods=["POST"])
def upload_pdf():
    if "file" not in request.files:
        return jsonify({"error": "Ingen fil lastet opp."}), 400

    f = request.files["file"]
    if not f.filename or not f.filename.lower().endswith(".pdf"):
        return jsonify({"error": "Kun PDF-filer er støttet."}), 400

    pdf_bytes = f.read()
    text = extract_pdf_text(pdf_bytes)
    return jsonify({"text": text, "filename": f.filename})


# ---------------------------------------------------------------------------
# GET /status  — knowledge-base health
# ---------------------------------------------------------------------------

@plaxis_agent_bp.route("/status", methods=["GET"])
def status():
    try:
        ensure_loaded()
        from activities.plaxis_agent.knowledge import get_all_commands
        cmds = get_all_commands()
        return jsonify({"ready": True, "docs_count": len(cmds)})
    except Exception as exc:
        return jsonify({"ready": False, "error": str(exc)})


# ---------------------------------------------------------------------------
# POST /connect  — test connection via PlaxisWorker and store params
# ---------------------------------------------------------------------------

@plaxis_agent_bp.route("/connect", methods=["POST"])
def connect():
    """
    Body::

        {"port": int, "password": str, "session_id": str,
         "output_port": int | null, "output_password": str | null}
    """
    data = request.get_json(silent=True) or {}
    port = int(data.get("port", 10000))
    password = data.get("password", "")
    session_id = data.get("session_id", "default")
    output_port = data.get("output_port")
    output_password = data.get("output_password")

    from config import PLAXIS_HOST
    host = PLAXIS_HOST

    # Build a test script and run it through the worker
    code = build_agent_test_script(host, port, password)
    result = _submit_and_wait(code, session_id, job_type="agent_connect", timeout=30)

    if result.get("success"):
        session_params = {
            "host": host,
            "port": port,
            "password": password,
            "output_port": output_port,
            "output_password": output_password or password,
        }
        _agent_sessions[session_id] = session_params
        _start_snapshot_background(session_id, session_params)

        project = result.get("project", "")
        return jsonify({
            "success": True,
            "message": f"Tilkoblet PLAXIS på port {port}"
                       + (f" — prosjekt: {project}" if project else ""),
            "model_info": {},
            "pending": True,
        })
    else:
        error = result.get("error", "Tilkobling feilet")
        return jsonify({"success": False, "error": error}), 500


# ---------------------------------------------------------------------------
# GET /observer  — get the current session observer log
# ---------------------------------------------------------------------------

@plaxis_agent_bp.route("/observer", methods=["GET"])
def observer():
    """
    Query params: session_id (default: "default")

    Returns the current observer markdown log for the session.
    """
    session_id = request.args.get("session_id", "default")
    log = get_observer_log(session_id)
    return jsonify({"session_id": session_id, "observer_log": log})


# ---------------------------------------------------------------------------
# POST /snapshot  — full model snapshot (rich model_info)
# ---------------------------------------------------------------------------

@plaxis_agent_bp.route("/snapshot", methods=["POST"])
def snapshot():
    """
    Run a comprehensive model snapshot and cache result as model_info.

    Body::

        {"session_id": str}
    """
    data = request.get_json(silent=True) or {}
    session_id = data.get("session_id", "default")

    sess = _agent_sessions.get(session_id)
    if not sess:
        return jsonify({"error": "Ingen aktiv sesjon. Koble til PLAXIS først."}), 400

    try:
        _start_snapshot_background(session_id, sess)
        current_snapshot = sess.get("model_info") or {}
        return jsonify({
            "success": True,
            "pending": True,
            "snapshot": current_snapshot,
        })
    except Exception as exc:
        traceback.print_exc()
        return jsonify({"error": str(exc)}), 500


# ===================================================================
# PIPELINE Step 0+1 — gather context and create plan
# ===================================================================

@plaxis_agent_bp.route("/plan", methods=["POST"])
def pipeline_plan():
    """
    Steps 0+1: gather context and return a structured plan for user approval.

    Body::

        {
            "message":          str,
            "session_id":       str,
            "username":         str,
            "history":          list | null,
            "pdf_text":         str | null,
            "selected_context": list | null,
        }

    Returns::

        {
            "plan": {
                "forståelse": str,
                "steg": [{nr, beskrivelse, kommandoer, risiko, kan_automatiseres}],
                "standard_advarsler": [str],
                "modellerings_tips": [str],
                "manglende_info": [str],
                "ønsket_output": str,
            },
            "context_summary": {...},
        }
    """
    data = request.get_json(silent=True) or {}
    message = (data.get("message") or "").strip()
    if not message:
        return jsonify({"error": "Melding mangler."}), 400

    session_id = data.get("session_id", "default")
    username   = data.get("username", "default")
    history    = data.get("history")
    pdf_text   = data.get("pdf_text")
    selected   = data.get("selected_context")

    # Attach cached model_info from session
    sess = _agent_sessions.get(session_id, {})
    model_info = sess.get("model_info")

    try:
        result = run_pipeline_plan(
            user_message=message,
            session_id=session_id,
            username=username,
            model_info=model_info,
            pdf_text=pdf_text,
            selected_context=selected,
            history=history,
        )
        # Store plan + context in memory for the execute step
        _pending_plans[session_id] = {
            "plan":         result["plan"],
            "context":      result.pop("_context", None),
            "user_message": message,
            "username":     username,
        }
        return jsonify(result)
    except Exception as exc:
        traceback.print_exc()
        return jsonify({"error": str(exc)}), 500


# ===================================================================
# PIPELINE Step 3+4+5+6 — generate code, validate, execute, learn
# ===================================================================

@plaxis_agent_bp.route("/execute-plan", methods=["POST"])
def pipeline_execute():
    """
    Steps 3+4+5+6: generate code from approved plan, validate, execute,
    update learnings.

    Body::

        {
            "session_id":       str,
            "username":         str,
            "history":          list | null,
            "pdf_text":         str | null,
            "selected_context": list | null,
            "max_retries":      int   (default: 2)
        }

    The plan must have been created first via POST /plan and is stored
    in _pending_plans keyed by session_id.

    Returns::

        {
            "code":     str,
            "output":   str,
            "success":  bool,
            "error":    str | null,
            "docs_used": list,
            "attempts": int,
            "steps":    int,
        }
    """
    data = request.get_json(silent=True) or {}
    session_id  = data.get("session_id", "default")
    username    = data.get("username", "default")
    history     = data.get("history")
    pdf_text    = data.get("pdf_text")
    selected    = data.get("selected_context")
    max_retries = int(data.get("max_retries", 2))

    pending = _pending_plans.get(session_id)
    if not pending:
        return jsonify({"error": "Ingen godkjent plan funnet. Kjør /plan først."}), 400

    sess = _agent_sessions.get(session_id)
    if not sess:
        return jsonify({"error": "Ikke tilkoblet PLAXIS. Koble til først."}), 400

    try:
        result = run_pipeline_execute(
            user_message=pending["user_message"],
            plan=pending["plan"],
            connection_params=sess,
            session_id=session_id,
            username=username,
            context=pending.get("context"),
            pdf_text=pdf_text,
            selected_context=selected,
            history=history,
            max_retries=max_retries,
        )
        # Clear pending plan after execution
        _pending_plans.pop(session_id, None)
        return jsonify(result)
    except Exception as exc:
        traceback.print_exc()
        return jsonify({"error": str(exc)}), 500


# ===================================================================
# PLAXIS Manual Indexing  (Azure AI Search)
# ===================================================================

@plaxis_agent_bp.route("/manual/setup", methods=["POST"])
def manual_index_setup():
    """Create/update the PLAXIS manual search index + datasource + indexer."""
    import os
    blob_conn = os.getenv("AZURE_STORAGE_CONNECTION_STRING", "")
    container_name = os.getenv("GAPI_BLOB_CONTAINER", "gapi-plaxis-manual")

    # Ensure blob container exists before creating the Azure AI Search datasource
    if blob_conn:
        try:
            from azure.storage.blob import BlobServiceClient
            svc = BlobServiceClient.from_connection_string(blob_conn)
            svc.create_container(container_name)
        except Exception:
            pass  # Already exists

    try:
        from activities.plaxis_agent.indexer import full_setup
        results = full_setup()
        return jsonify({"success": True, "results": results})
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@plaxis_agent_bp.route("/manual/run", methods=["POST"])
def manual_index_run():
    """Trigger an immediate indexer run for the PLAXIS manual."""
    try:
        from activities.plaxis_agent.indexer import run_indexer
        result = run_indexer()
        return jsonify(result)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@plaxis_agent_bp.route("/manual/status", methods=["GET"])
def manual_index_status():
    """Return the current status of the PLAXIS manual indexer."""
    try:
        from activities.plaxis_agent.indexer import get_indexer_status
        return jsonify(get_indexer_status())
    except Exception as exc:
        return jsonify({"status": "feil", "error": str(exc)})


@plaxis_agent_bp.route("/manual/upload", methods=["POST"])
def manual_upload():
    """Upload a PDF to the PLAXIS manual blob container and trigger reindexing."""
    if "file" not in request.files:
        return jsonify({"error": "Ingen fil i forespørselen"}), 400

    file = request.files["file"]
    if not file.filename:
        return jsonify({"error": "Tomt filnavn"}), 400

    from werkzeug.utils import secure_filename
    filename = secure_filename(file.filename)
    data = file.read()

    try:
        from activities.plaxis_agent.indexer import upload_manual_blob, run_indexer
        upload_manual_blob(filename, data)
        # Trigger reindexing
        indexer_triggered = False
        try:
            run_indexer()
            indexer_triggered = True
        except Exception as exc:
            print(f"GAPI manual indexer trigger error: {exc}")
        return jsonify({
            "success": True,
            "filename": filename,
            "size": len(data),
            "indexer_triggered": indexer_triggered,
        })
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@plaxis_agent_bp.route("/manual/documents", methods=["GET"])
def manual_list_documents():
    """List all documents in the PLAXIS manual blob container."""
    try:
        from activities.plaxis_agent.indexer import list_manual_blobs
        return jsonify({"documents": list_manual_blobs()})
    except Exception as exc:
        return jsonify({"documents": [], "error": str(exc)})


@plaxis_agent_bp.route("/manual/search", methods=["POST"])
def manual_search():
    """
    Search the PLAXIS manual index.

    Body: {"query": str, "top": int}
    """
    body = request.get_json(silent=True) or {}
    query = (body.get("query") or "").strip()
    if not query:
        return jsonify({"error": "Ingen søkeord oppgitt"}), 400

    top = body.get("top", 5)
    try:
        from activities.plaxis_agent.indexer import search_manual
        docs, err = search_manual(query, top=top)
        return jsonify({"documents": docs, "error": err})
    except Exception as exc:
        return jsonify({"documents": [], "error": str(exc)})


# ===================================================================
# GAPI Learnings  (persistent learning log in database)
# ===================================================================

@plaxis_agent_bp.route("/learnings", methods=["GET"])
def list_learnings():
    """
    List learning entries.

    Query params:
        scope      — 'global' | 'project' | 'user' (default: all)
        scope_key  — filter by project_id or username
        limit      — max results (default: 50)
    """
    scope = request.args.get("scope")
    scope_key = request.args.get("scope_key")
    limit = int(request.args.get("limit", 50))

    db = get_db_session()
    try:
        q = db.query(GapiLearning)
        if scope:
            q = q.filter(GapiLearning.scope == scope)
        if scope_key:
            q = q.filter(GapiLearning.scope_key == scope_key)
        q = q.order_by(GapiLearning.updated_at.desc()).limit(limit)
        entries = [e.to_dict() for e in q.all()]
        return jsonify({"learnings": entries, "total": len(entries)})
    finally:
        db.close()


@plaxis_agent_bp.route("/learnings/<int:learning_id>", methods=["GET"])
def get_learning(learning_id: int):
    """Get a single learning entry by ID."""
    db = get_db_session()
    try:
        entry = db.query(GapiLearning).filter(GapiLearning.id == learning_id).first()
        if not entry:
            return jsonify({"error": "Ikke funnet"}), 404
        return jsonify(entry.to_dict())
    finally:
        db.close()


@plaxis_agent_bp.route("/learnings", methods=["POST"])
def create_learning():
    """
    Create a new learning entry.

    Body: {"scope": str, "scope_key": str|null, "session_id": str|null,
           "title": str|null, "content": str, "username": str}
    """
    body = request.get_json(silent=True) or {}
    content = (body.get("content") or "").strip()
    username = (body.get("username") or "").strip()

    if not content:
        return jsonify({"error": "Innhold er obligatorisk"}), 400
    if not username:
        return jsonify({"error": "Brukernavn er obligatorisk"}), 400

    db = get_db_session()
    try:
        entry = GapiLearning(
            scope=body.get("scope", "global"),
            scope_key=body.get("scope_key"),
            session_id=body.get("session_id"),
            title=body.get("title"),
            content=content,
            username=username,
        )
        db.add(entry)
        db.commit()
        return jsonify({"success": True, "learning": entry.to_dict()}), 201
    except Exception as exc:
        db.rollback()
        return jsonify({"error": str(exc)}), 500
    finally:
        db.close()


@plaxis_agent_bp.route("/learnings/<int:learning_id>", methods=["PUT"])
def update_learning(learning_id: int):
    """
    Update an existing learning entry (append or replace content).

    Body: {"content": str, "title": str|null, "username": str}
    """
    body = request.get_json(silent=True) or {}
    content = (body.get("content") or "").strip()

    if not content:
        return jsonify({"error": "Innhold er obligatorisk"}), 400

    db = get_db_session()
    try:
        entry = db.query(GapiLearning).filter(GapiLearning.id == learning_id).first()
        if not entry:
            return jsonify({"error": "Ikke funnet"}), 404

        entry.content = content
        if "title" in body:
            entry.title = body["title"]
        db.commit()
        return jsonify({"success": True, "learning": entry.to_dict()})
    except Exception as exc:
        db.rollback()
        return jsonify({"error": str(exc)}), 500
    finally:
        db.close()


@plaxis_agent_bp.route("/learnings/<int:learning_id>", methods=["DELETE"])
def delete_learning(learning_id: int):
    """Delete a learning entry."""
    db = get_db_session()
    try:
        entry = db.query(GapiLearning).filter(GapiLearning.id == learning_id).first()
        if not entry:
            return jsonify({"error": "Ikke funnet"}), 404
        db.delete(entry)
        db.commit()
        return jsonify({"success": True})
    except Exception as exc:
        db.rollback()
        return jsonify({"error": str(exc)}), 500
    finally:
        db.close()


@plaxis_agent_bp.route("/learnings/latest", methods=["GET"])
def get_latest_learnings():
    """
    Get the latest learning entry per scope for use as agent context.

    Query params:
        scope     — 'global' | 'project' | 'user'
        scope_key — filter value (project_id or username)

    Returns the single most recent entry matching the criteria.
    """
    scope = request.args.get("scope", "global")
    scope_key = request.args.get("scope_key")

    db = get_db_session()
    try:
        q = db.query(GapiLearning).filter(GapiLearning.scope == scope)
        if scope_key:
            q = q.filter(GapiLearning.scope_key == scope_key)
        entry = q.order_by(GapiLearning.updated_at.desc()).first()
        if not entry:
            return jsonify({"learning": None})
        return jsonify({"learning": entry.to_dict()})
    finally:
        db.close()
