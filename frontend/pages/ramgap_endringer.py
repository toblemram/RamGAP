# -*- coding: utf-8 -*-
"""RamGAP endringer og versjoner."""

import streamlit as st

st.title("🔄 RamGAP endringer og versjoner")
st.markdown("---")
st.info(
    "Oversikt over endringer, fikser og nye funksjoner i RamGAP.\n\n"
    "_Full endringslogg kommer._"
)
st.markdown("#### Siste endringer")
with st.expander("v0.1 — Utviklingsversjon (2026)", expanded=True):
    st.markdown("""
    - ✅ Plaxis-automatisering (5 nivåer)  
    - ✅ GeoTolk SND-tolking  
    - ✅ Prosjektstyring med tilgangskontroll  
    - ✅ Aktivitetslogg per prosjekt  
    - 🚧 GeoGPT, Standarder, Excel-ark (kommer)  
    """)
