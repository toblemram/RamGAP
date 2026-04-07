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

# Session state for folder picker
if "new_project_folder" not in st.session_state:
    st.session_state.new_project_folder = ""

st.text_input(
    "Prosjektmappe",
    key="new_project_folder",
    help="Filsti til prosjektmappen, f.eks. P:\\1234 Prosjektnavn",
    placeholder="P:\\1234 Prosjektnavn",
)

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
        pid = project['id']
        is_owner = (project.get('project_owner') or project.get('created_by', '')) == USERNAME or project.get('created_by') == USERNAME

        with st.expander(f"📁 {project['name']}", expanded=False):
            st.write(f"**Beskrivelse:** {project.get('description') or 'Ingen beskrivelse'}")
            st.write(f"**Prosjektmappe:** {project.get('folder_path') or 'Ikke satt'}")
            st.write(f"**Prosjektansvarlig:** {project.get('project_owner') or project.get('created_by')}")
            st.write(f"**Opprettet av:** {project.get('created_by')}")
            st.write(
                f"**Opprettet:** {project.get('created_at', '')[:10] if project.get('created_at') else 'Ukjent'}"
            )
            allowed = project.get("allowed_users", [])
            if allowed:
                st.write(f"**Brukere med tilgang:** {', '.join(allowed)}")

            if not is_owner:
                st.caption("Bare prosjektansvarlig kan redigere prosjektet.")
                continue

            # ── Rediger prosjekt ──────────────────────────────────────
            st.markdown("---")
            st.markdown("#### ✏️ Rediger prosjekt")

            # Navn
            new_name = st.text_input(
                "Prosjektnavn",
                value=project['name'],
                key=f"edit_name_{pid}",
            )

            # Beskrivelse
            new_desc = st.text_area(
                "Beskrivelse",
                value=project.get('description') or '',
                key=f"edit_desc_{pid}",
            )

            # Prosjektansvarlig
            new_owner = st.text_input(
                "Prosjektansvarlig",
                value=project.get('project_owner') or project.get('created_by', ''),
                key=f"edit_owner_{pid}",
            )

            # Prosjektmappe
            folder_key = f"edit_folder_{pid}"
            if folder_key not in st.session_state:
                st.session_state[folder_key] = project.get('folder_path') or ''
            new_folder = st.text_input(
                "Prosjektmappe",
                key=folder_key,
            )

            if st.button("💾 Lagre endringer", key=f"save_project_{pid}", type="primary"):
                updates = {}
                if new_name != project['name']:
                    updates['name'] = new_name
                if new_desc != (project.get('description') or ''):
                    updates['description'] = new_desc
                if new_owner != (project.get('project_owner') or project.get('created_by', '')):
                    updates['project_owner'] = new_owner
                if new_folder != (project.get('folder_path') or ''):
                    updates['folder_path'] = new_folder
                if updates:
                    res = api.update_project(pid, USERNAME, **updates)
                    if res.get('success'):
                        st.success("Prosjekt oppdatert!")
                        _cached_projects.clear()
                        st.rerun()
                    else:
                        st.error(res.get('error', 'Kunne ikke oppdatere'))
                else:
                    st.info("Ingen endringer å lagre.")

            # ── Administrer brukere ───────────────────────────────────
            st.markdown("---")
            st.markdown("#### 👥 Brukertilgang")

            # Legg til bruker
            ac1, ac2 = st.columns([3, 1])
            with ac1:
                new_user = st.text_input(
                    "Legg til bruker (brukernavn)",
                    key=f"add_user_{pid}",
                    placeholder="f.eks. ola.nordmann",
                )
            with ac2:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("➕ Legg til", key=f"btn_add_user_{pid}", use_container_width=True):
                    if new_user.strip():
                        res = api.add_project_access(pid, new_user.strip(), USERNAME)
                        if res.get('success') or res.get('message'):
                            st.success(f"Tilgang gitt til {new_user.strip()}")
                            _cached_projects.clear()
                            st.rerun()
                        else:
                            st.error(res.get('error', 'Kunne ikke legge til bruker'))
                    else:
                        st.warning("Skriv inn et brukernavn.")

            # Fjern brukere
            current_users = project.get('allowed_users', [])
            if current_users:
                user_to_remove = st.selectbox(
                    "Fjern bruker",
                    options=current_users,
                    key=f"remove_user_select_{pid}",
                )
                if st.button("🗑️ Fjern valgt bruker", key=f"btn_remove_user_{pid}"):
                    res = api.remove_project_access(pid, user_to_remove, USERNAME)
                    if res.get('success'):
                        st.success(f"Tilgang fjernet for {user_to_remove}")
                        _cached_projects.clear()
                        st.rerun()
                    else:
                        st.error(res.get('error', 'Kunne ikke fjerne bruker'))

            # ── Slett prosjekt ────────────────────────────────────────
            st.markdown("---")
            st.markdown("#### 🗑️ Slett prosjekt")
            st.warning(
                f'For å slette **{project["name"]}**, skriv "slett" i feltet under og trykk knappen.'
            )
            confirm_text = st.text_input(
                "Bekreft sletting",
                key=f"delete_confirm_{pid}",
                placeholder='Skriv "slett" for å bekrefte',
            )
            if st.button("🗑️ Slett prosjekt permanent", key=f"btn_delete_{pid}", type="secondary"):
                if confirm_text.strip().lower() == "slett":
                    res = api.delete_project(pid, USERNAME, "SLETT")
                    if res.get('success'):
                        st.success(f"Prosjekt '{project['name']}' er slettet.")
                        _cached_projects.clear()
                        st.rerun()
                    else:
                        st.error(res.get('error', 'Kunne ikke slette prosjektet'))
                else:
                    st.error('Du må skrive "slett" for å bekrefte sletting.')
else:
    st.info("Ingen prosjekter ennå. Opprett ditt første prosjekt ovenfor!")
