# -*- coding: utf-8 -*-
"""Prosjekt innstillinger — opprettelse og administrasjon av prosjekter."""

import streamlit as st
from components.auth import require_username
from components.api_client import APIClient

USERNAME = require_username()
api = APIClient()


@st.cache_data(ttl=30)
def _cached_projects(username: str) -> list:
    return api.get_projects(username)


st.subheader("⚙️ Prosjekt innstillinger")
st.markdown("---")

st.markdown("### Opprett nytt prosjekt")

with st.form("create_project_form"):
    project_name = st.text_input("Prosjektnavn *")
    project_description = st.text_area("Beskrivelse")
    project_folder = st.text_input(
        "Prosjektmappe",
        help="Filsti til prosjektmappen, f.eks. P:\\1234 Prosjektnavn",
    )
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
            new_folder = st.text_input(
                "Endre prosjektmappe",
                value=project.get('folder_path') or '',
                key=f"folder_{project['id']}",
            )
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
