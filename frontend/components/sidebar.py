# -*- coding: utf-8 -*-
"""
Sidebar Component
=================
Renders the shared navigation sidebar shown on every page.
Must match the sidebar in app.py exactly.
"""

import os
import streamlit as st


def _get_username() -> str:
    try:
        return os.getlogin()
    except OSError:
        return os.environ.get("USERNAME", os.environ.get("USER", "User"))


def render_sidebar():
    """Render the navigation sidebar — identical to app.py."""
    from components.api_client import APIClient

    username = _get_username()
    api = APIClient()

    with st.sidebar:
        st.markdown("### 🏗️ RamGAP")
        st.divider()

        nav_items = [
            ('home',             '🏠', 'Prosjekter'),
            ('geogpt',           '🤖', 'GeoGPT'),
            ('standarder',       '📚', 'Standarder'),
            ('excel_ark',        '📊', 'Excel-ark'),
            ('ramgap_endringer', '🔄', 'Endringer og versjoner'),
            ('opplaering',       '🎓', 'Opplæring'),
            ('project_setup',    '⚙️', 'Prosjekt innstillinger'),
        ]

        if 'current_page' not in st.session_state:
            st.session_state.current_page = 'home'

        cur = st.session_state.current_page
        for page_key, icon, label in nav_items:
            btn_type = 'primary' if cur == page_key else 'secondary'
            if st.button(
                f"{icon}  {label}",
                key=f"nav_{page_key}",
                use_container_width=True,
                type=btn_type,
            ):
                st.session_state.current_page = page_key
                st.session_state.selected_project = None
                st.switch_page("app.py")

        st.divider()
        st.caption(f"👤 **{username}**")
        try:
            if api.is_healthy():
                st.success("✅ Backend OK", icon=None)
            else:
                st.warning("⚠️ Backend utilgjengelig")
        except Exception:
            st.warning("⚠️ Backend utilgjengelig")
