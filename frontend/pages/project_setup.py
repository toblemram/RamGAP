# -*- coding: utf-8 -*-
"""Prosjekt innstillinger — opprettelse og administrasjon av prosjekter."""

import streamlit as st
from components.auth import require_username
from components.api_client import APIClient


def _pick_folder(initial_dir: str = "") -> str:
    """Open a native Windows folder-picker dialog and return the chosen path."""
    import os
    import tkinter as tk
    from tkinter import filedialog
    root = tk.Tk()
    root.withdraw()
    root.wm_attributes("-topmost", 1)
    kwargs = {}
    if initial_dir and os.path.isdir(initial_dir):
        kwargs["initialdir"] = initial_dir
    folder = filedialog.askdirectory(**kwargs)
    root.destroy()
    if folder:
        return os.path.normpath(folder)
    return ""


USERNAME = require_username()
api = APIClient()


@st.cache_data(ttl=30)
def _cached_projects(username: str) -> list:
    return api.get_projects(username)


st.subheader("⚙️ Prosjekt innstillinger")
st.markdown("---")

st.markdown("### Opprett nytt prosjekt")

# Session state for folder picker (outside form)
if "new_project_folder" not in st.session_state:
    st.session_state.new_project_folder = ""

# Handle pending browse result before widget renders
if st.session_state.get("_browse_new_pending"):
    st.session_state.new_project_folder = st.session_state.pop("_browse_new_pending")

col_folder, col_browse = st.columns([4, 1])
with col_folder:
    folder_display = st.text_input(
        "Prosjektmappe",
        key="new_project_folder",
        help="Filsti til prosjektmappen, f.eks. P:\\1234 Prosjektnavn",
    )
with col_browse:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("📂 Bla gjennom…", key="browse_new_folder", use_container_width=True):
        chosen = _pick_folder(st.session_state.new_project_folder)
        if chosen:
            st.session_state["_browse_new_pending"] = chosen
            st.rerun()

with st.form("create_project_form"):
    project_name = st.text_input("Prosjektnavn *")
    project_description = st.text_area("Beskrivelse")
    allowed_users_input = st.text_input(
        "Brukernavn med tilgang (kommaseparert)",
        help="Skriv inn Windows-brukernavn separert med komma. Du får automatisk tilgang.",
    )
    submitted = st.form_submit_button("Opprett prosjekt", type="primary")

    if submitted:
        if not project_name:
            st.error("Prosjektnavn er påkrevd")
        else:
            allowed_users = [u.strip() for u in allowed_users_input.split(",") if u.strip()]
            project_folder = st.session_state.new_project_folder

            result = api.create_project(project_name, project_description, USERNAME, allowed_users, project_folder)

            if result.get("id") or result.get("project"):
                st.success(f"✅ Prosjekt '{project_name}' opprettet!")
                _cached_projects.clear()
                st.rerun()
            else:
                st.error(f"Feil: {result.get('error', 'Ukjent feil')}")

st.markdown("---")
st.markdown("### Dine prosjekter")

projects = _cached_projects(USERNAME)
if projects:
    for project in projects:
        with st.expander(f"📁 {project['name']}", expanded=False):
            st.write(f"**Beskrivelse:** {project.get('description') or 'Ingen beskrivelse'}")
            st.write(f"**Prosjektmappe:** {project.get('folder_path') or 'Ikke satt'}")
            st.write(f"**Opprettet av:** {project.get('created_by')}")
            st.write(
                f"**Opprettet:** {project.get('created_at', '')[:10] if project.get('created_at') else 'Ukjent'}"
            )
            allowed = project.get("allowed_users", [])
            if allowed:
                st.write(f"**Brukere med tilgang:** {', '.join(allowed)}")

            # Rediger prosjektmappe
            st.markdown("---")
            folder_key = f"folder_{project['id']}"
            pending_key = f"_browse_edit_pending_{project['id']}"
            if folder_key not in st.session_state:
                st.session_state[folder_key] = project.get('folder_path') or ''
            if st.session_state.get(pending_key):
                st.session_state[folder_key] = st.session_state.pop(pending_key)
            fc, bc = st.columns([4, 1])
            with fc:
                new_folder = st.text_input(
                    "Endre prosjektmappe",
                    key=folder_key,
                )
            with bc:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("📂", key=f"browse_folder_{project['id']}", use_container_width=True):
                    chosen = _pick_folder(st.session_state.get(folder_key, ''))
                    if chosen:
                        st.session_state[pending_key] = chosen
                        st.rerun()
            if st.button("💾 Lagre mappe", key=f"save_folder_{project['id']}"):
                res = api.update_project(project['id'], USERNAME, folder_path=new_folder)
                if res.get('success'):
                    st.success("Prosjektmappe oppdatert!")
                    _cached_projects.clear()
                    st.rerun()
                else:
                    st.error(res.get('error', 'Kunne ikke oppdatere'))
else:
    st.info("Ingen prosjekter ennå. Opprett ditt første prosjekt ovenfor!")
