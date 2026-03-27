# -*- coding: utf-8 -*-
"""
Auth Utilities
==============
Provides get_username() that works both locally and on Azure App Service.

Locally:  Uses os.getlogin() / USERNAME environment variable.
Azure:    Uses EasyAuth header X-Ms-Client-Principal-Name injected by
          Azure App Service Authentication.
"""

import os
import streamlit as st


def get_username() -> str:
    """
    Return the current user's display name.

    Priority:
    1. Azure EasyAuth header (X-Ms-Client-Principal-Name) — works on App Service
    2. os.getlogin() — works on Windows desktop
    3. USERNAME / USER env var — fallback
    4. "User" — last resort
    """
    # 1. Azure App Service EasyAuth
    try:
        headers = st.context.headers
        azure_user = headers.get("X-Ms-Client-Principal-Name", "")
        if azure_user:
            # EasyAuth returns email — take the part before @
            return azure_user.split("@")[0] if "@" in azure_user else azure_user
    except Exception:
        pass

    # 2. Local: os.getlogin()
    try:
        return os.getlogin()
    except OSError:
        pass

    # 3. Environment variable
    return os.environ.get("USERNAME", os.environ.get("USER", "User"))
