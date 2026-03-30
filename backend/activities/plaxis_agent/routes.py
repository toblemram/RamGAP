# -*- coding: utf-8 -*-
"""
Plaxis Agent Routes
====================
Flask Blueprint exposing REST endpoints for the AI-powered Plaxis agent.

Endpoints
---------
POST /api/plaxis-agent/chat
    Accept a user message, generate Plaxis code, optionally execute it, and
    return the result.

POST /api/plaxis-agent/execute
    Execute previously generated code against a connected Plaxis session.

POST /api/plaxis-agent/upload-pdf
    Upload a PDF and extract its text for use as extra context.

GET  /api/plaxis-agent/status
    Check whether the knowledge base is available.
"""

import traceback

from flask import Blueprint, jsonify, request

from shared.auth import get_username_from_request
from activities.plaxis_agent.service import (
    chat_and_execute,
    execute_code,
    generate_code,
)
from activities.plaxis_agent.knowledge import ensure_loaded, extract_pdf_text

plaxis_agent_bp = Blueprint("plaxis_agent", __name__, url_prefix="/api/plaxis-agent")

# ---------------------------------------------------------------------------
# In-memory Plaxis sessions — shared with the existing plaxis activity
# From activities/plaxis/routes.py pattern
# ---------------------------------------------------------------------------
_plaxis_sessions: dict = {}


def _get_plaxis_globals(session_id: str) -> dict:
    """Return the Plaxis namespace {g, s, g_o, s_o} for a session, or empty."""
    sess = _plaxis_sessions.get(session_id, {})
    return {
        "g": sess.get("g_i"),
        "s": sess.get("s_i"),
        "g_o": sess.get("g_o"),
        "s_o": sess.get("s_o"),
    }


# ---------------------------------------------------------------------------
# POST /chat  — main agent endpoint
# ---------------------------------------------------------------------------

@plaxis_agent_bp.route("/chat", methods=["POST"])
def chat():
    """
    Body::

        {
            "message":     str,          # user's natural-language request
            "session_id":  str,          # Plaxis session identifier
            "history":     list | null,  # previous conversation turns
            "pdf_text":    str | null,   # previously extracted PDF text
            "auto_execute": bool         # true → also run the code in Plaxis
        }

    Response::

        {
            "code":      str,
            "output":    str,
            "success":   bool,
            "error":     str | null,
            "attempts":  int,
            "docs_used": list[str]
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
    selected_context = data.get("selected_context")  # user-selected findings

    try:
        if auto_execute:
            plaxis_globals = _get_plaxis_globals(session_id)
            if not plaxis_globals.get("g"):
                # Try importing from the existing plaxis routes sessions
                try:
                    from activities.plaxis.routes import _sessions
                    sess = _sessions.get(session_id, {})
                    plaxis_globals = {
                        "g": sess.get("g_i"),
                        "s": sess.get("s_i"),
                        "g_o": sess.get("g_o"),
                        "s_o": sess.get("s_o"),
                    }
                except (ImportError, AttributeError):
                    pass

            if not plaxis_globals.get("g"):
                return jsonify({
                    "error": "Ikke tilkoblet PLAXIS.  Koble til via Plaxis-siden først.",
                }), 400

            result = chat_and_execute(
                user_message=message,
                plaxis_globals=plaxis_globals,
                history=history,
                pdf_text=pdf_text,
                selected_context=selected_context,
                max_retries=2,
            )
        else:
            # Code generation only (no execution)
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

    Response::

        {"success": bool, "output": str, "error": str | null}
    """
    data = request.get_json(silent=True) or {}
    code = (data.get("code") or "").strip()
    session_id = data.get("session_id", "default")

    if not code:
        return jsonify({"error": "Ingen kode oppgitt."}), 400

    # Look for Plaxis sessions
    plaxis_globals = _get_plaxis_globals(session_id)
    if not plaxis_globals.get("g"):
        try:
            from activities.plaxis.routes import _sessions
            sess = _sessions.get(session_id, {})
            plaxis_globals = {
                "g": sess.get("g_i"),
                "s": sess.get("s_i"),
                "g_o": sess.get("g_o"),
                "s_o": sess.get("s_o"),
            }
        except (ImportError, AttributeError):
            pass

    if not plaxis_globals.get("g"):
        return jsonify({"error": "Ikke tilkoblet PLAXIS."}), 400

    result = execute_code(code, plaxis_globals)
    return jsonify(result)


# ---------------------------------------------------------------------------
# POST /upload-pdf  — extract text from an uploaded PDF
# ---------------------------------------------------------------------------

@plaxis_agent_bp.route("/upload-pdf", methods=["POST"])
def upload_pdf():
    """
    Accepts multipart/form-data with a ``file`` field.
    Returns ``{"text": str}``.
    """
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
    """Check if the knowledge base is loaded and ready."""
    try:
        ensure_loaded()
        from activities.plaxis_agent.knowledge import get_all_commands
        cmds = get_all_commands()
        return jsonify({
            "ready": True,
            "docs_count": len(cmds),
        })
    except Exception as exc:
        return jsonify({"ready": False, "error": str(exc)})


# ---------------------------------------------------------------------------
# POST /connect  — connect to Plaxis from the agent page
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

    try:
        from plxscripting.easy import new_server
    except ImportError:
        return jsonify({"error": "plxscripting er ikke installert."}), 500

    from config import PLAXIS_HOST

    try:
        s_i, g_i = new_server(PLAXIS_HOST, port, password=password)
        # Verify connection
        _ = g_i.Project
        session = {"s_i": s_i, "g_i": g_i, "s_o": None, "g_o": None}

        # Also connect to output if port given
        if output_port:
            s_o, g_o = new_server(PLAXIS_HOST, int(output_port),
                                  password=output_password or password)
            session["s_o"] = s_o
            session["g_o"] = g_o

        _plaxis_sessions[session_id] = session

        # Also register in main plaxis routes if possible
        try:
            from activities.plaxis.routes import _sessions
            _sessions[session_id] = session
        except (ImportError, AttributeError):
            pass

        return jsonify({"success": True, "message": f"Tilkoblet PLAXIS på port {port}"})

    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500
