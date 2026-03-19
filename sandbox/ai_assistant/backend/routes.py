# -*- coding: utf-8 -*-
"""
AI Assistant Routes
===================
Flask Blueprint with REST API endpoints for the AI assistant activity.

Endpoints:
    POST /api/ai/chat    — Send a user message and receive a Plaxis code reply
    POST /api/ai/execute — Execute LLM-generated code against a live Plaxis session
    GET  /api/ai/history — Retrieve conversation history
"""

from flask import Blueprint, request, jsonify

ai_bp = Blueprint("ai_assistant", __name__, url_prefix="/api/ai")


@ai_bp.route("/chat", methods=["POST"])
def chat():
    """Accept a natural-language prompt and return generated Plaxis Python code."""
    # TODO: implement using AIAssistantService
    return jsonify({"message": "Not yet implemented"}), 501


@ai_bp.route("/execute", methods=["POST"])
def execute():
    """Execute LLM-generated code against a connected Plaxis session."""
    # TODO: implement
    return jsonify({"message": "Not yet implemented"}), 501
