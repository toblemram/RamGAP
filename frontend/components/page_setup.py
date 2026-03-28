# -*- coding: utf-8 -*-
"""
Page Setup
==========
Shared boilerplate that every Streamlit page should call once at the top.
Handles: sys.path, page config, CSS (hide auto-nav), auth, sidebar.
"""

import sys
import os
import streamlit as st

# Ensure frontend/ root is importable when Streamlit runs pages/ directly
_FRONTEND_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _FRONTEND_ROOT not in sys.path:
    sys.path.insert(0, _FRONTEND_ROOT)


# Common CSS injected on every page
_HIDE_NAV_CSS = """
<style>
    [data-testid="stSidebarNav"] { display: none !important; }
</style>
"""


def setup_page(
    *,
    page_icon: str = "🏗️",
    current_page: str = "",
) -> str:
    """
    One-call page bootstrap.  Returns the authenticated username.

    Must be called **before any other st.* call** in the page script
    (because it calls ``st.set_page_config``).
    """
    st.set_page_config(
        page_title="RamGAP",
        page_icon=page_icon,
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.markdown(_HIDE_NAV_CSS, unsafe_allow_html=True)

    # Late imports to avoid circular deps (sidebar imports bug_report etc.)
    from components.auth import require_username
    from components.sidebar import render_sidebar

    username = require_username()
    render_sidebar(username, current_page=current_page)
    return username
