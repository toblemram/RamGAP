import streamlit as st
import os
import datetime
from components.api_client import APIClient

api = APIClient()

from components.auth import require_username

USERNAME = require_username()

def main():
    if st.button("← Tilbake til oversikt"):
        st.switch_page("app.py")

    st.subheader("⚙️ Prosjekt innstillinger")
    st.markdown("---")
    st.markdown("### Opprett nytt prosjekt")
    with st.form("create_project_form"):
        project_name = st.text_input("Prosjektnavn *")
        project_description = st.text_area("Beskrivelse")
        allowed_users_input = st.text_input(
            "Brukernavn med tilgang (kommaseparert)",
            help="Skriv inn Windows-brukernavn separert med komma. Du får automatisk tilgang."
        )
        submitted = st.form_submit_button("Opprett prosjekt", type="primary")
        if submitted:
            if not project_name:
                st.warning("Prosjektnavn er påkrevd.")
            else:
                allowed_users = [u.strip() for u in allowed_users_input.split(",") if u.strip()]
                if USERNAME not in allowed_users:
                    allowed_users.append(USERNAME)
                api.create_project(project_name, project_description, allowed_users)
                st.success(f"Prosjekt '{project_name}' opprettet!")
    st.markdown("---")
    st.markdown("### Dine prosjekter")
    projects = api.get_projects(USERNAME)
    if projects:
        for project in projects:
            with st.expander(f"📁 {project['name']}", expanded=False):
                st.write(f"**Beskrivelse:** {project.get('description', '')}")
                st.write(f"**Opprettet av:** {project.get('created_by')}")
                st.write(f"**Opprettet:** {project.get('created_at', '')[:10] if project.get('created_at') else 'Ukjent'}")
                allowed = project.get('allowed_users', [])
                if allowed:
                    st.write(f"**Brukere med tilgang:** {', '.join(allowed)}")
    else:
        st.info("Ingen prosjekter ennå. Opprett ditt første prosjekt ovenfor!")

if __name__ == "__main__":
    main()
