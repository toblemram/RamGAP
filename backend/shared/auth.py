# -*- coding: utf-8 -*-
"""
Authentication Helpers
======================
Utilities for identifying the current user and handling basic
session/access control checks.

Note: Full auth (Azure AD / JWT) should be added here when required.
"""


def get_username_from_request(request) -> str:
    """
    Extract the username from a Flask request.
    Checks query params, then JSON body, then falls back to 'anonymous'.
    """
    username = request.args.get("username") or (
        request.get_json(silent=True) or {}
    ).get("username", "")
    return username.strip() or "anonymous"
