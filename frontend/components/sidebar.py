# -*- coding: utf-8 -*-
"""
Sidebar Component
=================
Renders the shared navigation sidebar shown on every page.
Displays the application name, the logged-in username, backend
connection status, and navigation links.
"""

import streamlit as st


def render_sidebar():
    """Render the navigation sidebar."""
    with st.sidebar:
        st.markdown("## RamGAP")
        st.markdown("---")
        st.markdown("**Navigation**")
        st.page_link("app.py",             label="Home",    icon="🏠")
        st.page_link("pages/plaxis.py",   label="Plaxis",  icon="📊")
        st.page_link("pages/geotolk.py",  label="GeoTolk", icon="🔬")
        st.markdown("---")
        # TODO: show username and backend health badge
