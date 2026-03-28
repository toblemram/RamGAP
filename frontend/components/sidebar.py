# -*- coding: utf-8 -*-
"""
Shared Sidebar
==============
Renders the standard RamGAP sidebar used across all pages:
navigation links, feedback button, user info, and backend status.
"""

import streamlit as st
from components.api_client import APIClient
from components.bug_report import show_feedback_dialog

_api = APIClient()


def render_sidebar(username: str, current_page: str = ""):
    """
    Render the shared sidebar. Call inside ``with st.sidebar:`` or at
    module level (Streamlit places sidebar widgets automatically).

    Parameters
    ----------
    username : str
        The authenticated user's display name.
    current_page : str
        Key of the currently active page (used to highlight the nav button).
    """
    with st.sidebar:
        st.markdown("### 🏗️ RamGAP")
        st.divider()

        nav_items = [
            ("app",              "🏠", "Prosjekter"),
            ("geogpt",           "🤖", "GeoGPT"),
            ("standarder",       "📚", "Standarder"),
            ("excel_ark",        "📊", "Excel-ark"),
            ("ramgap_endringer", "🔄", "Endringer og versjoner"),
            ("opplaering",       "🎓", "Opplæring"),
            ("project_setup",    "⚙️", "Prosjekt innstillinger"),
        ]

        # Map page keys to their Streamlit page file paths
        _page_files = {
            "app":              "app.py",
            "geogpt":           "pages/geogpt.py",
            "standarder":       "pages/standarder.py",
            "excel_ark":        "pages/excel_ark.py",
            "ramgap_endringer": "pages/ramgap_endringer.py",
            "opplaering":       "pages/opplaering.py",
            "project_setup":    "pages/project_setup.py",
        }

        for page_key, icon, label in nav_items:
            btn_type = "primary" if current_page == page_key else "secondary"
            if st.button(
                f"{icon}  {label}",
                key=f"nav_{page_key}",
                use_container_width=True,
                type=btn_type,
            ):
                st.switch_page(_page_files[page_key])

        st.divider()
        show_feedback_dialog(username)
        st.divider()
        st.caption(f"👤 **{username}**")

        try:
            if _api.is_healthy():
                st.success("✅ Backend OK", icon=None)
            else:
                st.warning("⚠️ Backend utilgjengelig")
        except Exception:
            st.warning("⚠️ Backend utilgjengelig")
