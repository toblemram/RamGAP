# -*- coding: utf-8 -*-
"""
RamGAP Frontend — Main Entry Point
====================================
Thin orchestrator that uses st.navigation() for multi-page routing.
All page content lives under pages/.  The sidebar is rendered once here
so it stays consistent across all pages without flashing.
"""

import sys
import os
import streamlit as st

# Ensure frontend/ root is importable from both app.py and pages/
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from components.auth import require_username
from components.bug_report import show_feedback_dialog
from components.api_client import APIClient
from components.sidebar import render_sidebar

st.set_page_config(
    page_title="RamGAP",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded",
)

USERNAME = require_username()

# Render custom sidebar once here (guards against double-render from setup_page())
st.session_state["_sidebar_rendered"] = False
render_sidebar(USERNAME)

# ---------------------------------------------------------------------------
# Navigation — all pages declared once here
# ---------------------------------------------------------------------------

pg = st.navigation(
    {
        "": [
            st.Page("pages/home.py", title="Prosjekter", icon="🏠", default=True),
        ],
        "Ressurser": [
            st.Page("pages/geogpt.py", title="GeoGPT", icon="🤖"),
            st.Page("pages/plaxis_agent.py", title="Plaxis Agent", icon="🤖"),
            st.Page("pages/standarder.py", title="Standarder", icon="📚"),
            st.Page("pages/excel_ark.py", title="Excel-ark", icon="📊"),
            st.Page("pages/opplaering.py", title="Opplæring", icon="🎓"),
        ],
        "_hidden": [
            st.Page("pages/plaxis.py", title="Plaxis automatisering", icon="🔧"),
            st.Page("pages/geotolk.py", title="GeoTolk", icon="🗺️"),
            st.Page("pages/modellering.py", title="Modellering", icon="🏗️"),
        ],
        "System": [
            st.Page("pages/project_setup.py", title="Prosjektinnstillinger", icon="⚙️"),
            st.Page("pages/prosjekt_endringer.py", title="Prosjekt endringer", icon="📝"),
            st.Page("pages/ramgap_endringer.py", title="Endringslogg", icon="🔄"),
        ],
    },
    position="hidden",
)

# ---------------------------------------------------------------------------
# Run the selected page
# ---------------------------------------------------------------------------

pg.run()
