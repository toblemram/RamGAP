# -*- coding: utf-8 -*-
"""
Auth Utilities
==============
Provides get_username() that works both locally and on Azure App Service.

Locally:  Uses os.getlogin() / USERNAME environment variable.
Azure:    1) EasyAuth header  2) Simple name prompt stored in session
"""

import os
import streamlit as st


def get_username() -> str:
    """
    Return the current user's display name.

    Priority:
    1. Azure EasyAuth header (X-Ms-Client-Principal-Name)
    2. os.getlogin() — works on Windows desktop
    3. USERNAME / USER env var
    4. Session-stored name (user prompted once on Azure)
    """
    # 1. Azure App Service EasyAuth
    try:
        headers = st.context.headers
        azure_user = headers.get("X-Ms-Client-Principal-Name", "")
        if azure_user:
            name = azure_user.split("@")[0] if "@" in azure_user else azure_user
            st.session_state["_username"] = name
            return name
    except Exception:
        pass

    # 2. Local: os.getlogin()
    try:
        name = os.getlogin()
        if name and name.lower() not in ("nobody", "root", "appuser"):
            return name
    except OSError:
        pass

    # 3. Environment variable (Windows)
    env_user = os.environ.get("USERNAME", os.environ.get("USER", ""))
    if env_user and env_user.lower() not in ("nobody", "root", "appuser", ""):
        return env_user

    # 4. Already entered this session
    if st.session_state.get("_username"):
        return st.session_state["_username"]

    # 5. Prompt user for name (Azure without EasyAuth)
    return ""


def require_username() -> str:
    """
    Returns the username, showing a blocking prompt if unknown.
    Call this at the top of pages that need a username.
    """
    name = get_username()
    if name:
        return name

    st.info("👋 Skriv inn navnet ditt for å komme i gang.")
    entered = st.text_input("Ditt navn / brukernavn", key="_username_input")
    if entered and entered.strip():
        st.session_state["_username"] = entered.strip()
        st.rerun()

    st.stop()
    return ""  # unreachable, st.stop() halts execution
