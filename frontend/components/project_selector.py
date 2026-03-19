# -*- coding: utf-8 -*-
"""
Project Selector Component
===========================
Reusable Streamlit widget that fetches the user's projects from the backend
and renders a selectbox. Returns the selected project dict.
"""

import streamlit as st
import requests
from config import BACKEND_URL, REQUEST_TIMEOUT


def project_selector(username: str) -> dict | None:
    """
    Render a project selectbox and return the selected project.

    Args:
        username: The current user's login name.

    Returns:
        The selected project dict, or None if no projects exist.
    """
    try:
        resp = requests.get(
            f"{BACKEND_URL}/api/projects",
            params={"username": username},
            timeout=REQUEST_TIMEOUT,
        )
        projects = resp.json().get("projects", []) if resp.ok else []
    except requests.RequestException:
        projects = []

    if not projects:
        st.info("No projects found. Create one first.")
        return None

    names = [p["name"] for p in projects]
    choice = st.selectbox("Project", names)
    return next(p for p in projects if p["name"] == choice)
