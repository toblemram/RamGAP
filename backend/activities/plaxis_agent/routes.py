# -*- coding: utf-8 -*-
"""
GAPI (Plaxis Agent) Routes
============================
Flask Blueprint exposing REST endpoints for the AI-powered Plaxis agent.

All code execution goes through the PlaxisWorker job queue so that the
backend never needs a direct connection to Plaxis — the worker runs on the
user's local machine next to Plaxis.

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
"""

import json
import time
import traceback

from flask import Blueprint, jsonify, request

from core.database import get_db_session
from core.models import PlaxisJob
from activities.plaxis_agent.service import (
    chat_and_execute,
    execute_via_worker,
    generate_code,
)
from activities.plaxis_agent.knowledge import ensure_loaded, extract_pdf_text
from activities.plaxis.script_builder import (
    build_agent_test_script,
    build_agent_exec_script,
)

plaxis_agent_bp = Blueprint("plaxis_agent", __name__, url_prefix="/api/plaxis-agent")

# ---------------------------------------------------------------------------
# In-memory session storage — connection params per session
# ---------------------------------------------------------------------------
_agent_sessions: dict = {}  # session_id -> {host, port, password, output_port, output_password}


def _get_session(session_id: str) -> dict | None:
    return _agent_sessions.get(session_id)


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
        _agent_sessions[session_id] = {
            "host": host,
            "port": port,
            "password": password,
            "output_port": output_port,
            "output_password": output_password or password,
        }
        project = result.get("project", "")
        return jsonify({
            "success": True,
            "message": f"Tilkoblet PLAXIS på port {port}"
                       + (f" — prosjekt: {project}" if project else ""),
        })
    else:
        error = result.get("error", "Tilkobling feilet")
        return jsonify({"success": False, "error": error}), 500
