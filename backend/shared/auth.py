# -*- coding: utf-8 -*-
"""
Authentication Helpers
======================
Utilities for identifying the current user and handling basic
session/access control checks.

Note: Full auth (Azure AD / JWT) should be added here when required.
"""

import os
from functools import wraps
from flask import request, jsonify

_API_KEY = os.getenv('API_KEY', '')


def require_api_key(f):
    """
    Decorator that enforces X-API-Key header when API_KEY env var is set.
    If API_KEY is not configured (e.g. local dev), all requests are allowed.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        if _API_KEY and request.headers.get('X-API-Key') != _API_KEY:
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated


def init_api_key_middleware(app):
    """
    Register a before_request hook that validates X-API-Key on all /api/ routes.
    Call this once from app.py after creating the Flask app.
    """
    @app.before_request
    def _check_api_key():
        if not _API_KEY:
            return  # Not configured — allow all (local dev)
        if request.path.startswith('/api/'):
            if request.headers.get('X-API-Key') != _API_KEY:
                return jsonify({'error': 'Unauthorized'}), 401


def get_username_from_request(request) -> str:
    """
    Extract the username from a Flask request.
    Checks query params, then JSON body, then falls back to 'anonymous'.
    """
    username = request.args.get("username") or (
        request.get_json(silent=True) or {}
    ).get("username", "")
    return username.strip() or "anonymous"
