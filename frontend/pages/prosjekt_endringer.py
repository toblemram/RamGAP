# -*- coding: utf-8 -*-
"""
Prosjekt endringer — rediger prosjekt, medlemmer og prosjektansvarlig.
"""

import streamlit as st
from components.auth import require_username
from components.api_client import APIClient

USERNAME = require_username()
api = APIClient()


@st.cache_data(ttl=30)
def _cached_projects(username: str) -> list:
    return api.get_projects(username)


def _clear_cache():
    _cached_projects.clear()


st.subheader("📝 Prosjekt endringer")
st.markdown("---")

projects = _cached_projects(USERNAME)

if not projects:
    st.info("Du har ingen prosjekter. Opprett et prosjekt under **Prosjektinnstillinger**.")
    st.stop()

# --- Velg prosjekt ---
project_names = [p["name"] for p in projects]
selected_idx = st.selectbox(
    "Velg prosjekt",
    range(len(project_names)),
    format_func=lambda i: project_names[i],
    key="pe_project_select",
)
project = projects[selected_idx]
project_id = project["id"]
is_owner = (project.get("project_owner", project["created_by"]) == USERNAME)

st.markdown("---")

# =====================================================================
# 1. Rediger prosjektdetaljer
# =====================================================================
st.markdown("### ✏️ Rediger prosjekt")

if not is_owner:
    st.info("Bare prosjektansvarlig kan redigere prosjektet.")

with st.form("edit_project_form"):
    new_name = st.text_input("Prosjektnavn", value=project["name"], disabled=not is_owner)
    new_desc = st.text_area(
        "Beskrivelse",
        value=project.get("description") or "",
        disabled=not is_owner,
    )
    save_clicked = st.form_submit_button("Lagre endringer", type="primary", disabled=not is_owner)

    if save_clicked and is_owner:
        if not new_name.strip():
            st.error("Prosjektnavn kan ikke være tomt.")
        else:
            result = api.update_project(
                project_id, USERNAME,
                name=new_name.strip(),
                description=new_desc.strip(),
            )
            if result.get("success"):
                st.success("✅ Prosjekt oppdatert!")
                _clear_cache()
                st.rerun()
            else:
                st.error(f"Feil: {result.get('error', 'Ukjent feil')}")

st.markdown("---")

# =====================================================================
# 2. Prosjektansvarlig
# =====================================================================
st.markdown("### 👑 Prosjektansvarlig")

current_owner = project.get("project_owner", project["created_by"])
st.write(f"**Nåværende prosjektansvarlig:** {current_owner}")

if is_owner:
    all_members = [project["created_by"]] + project.get("allowed_users", [])
    unique_members = list(dict.fromkeys(all_members))  # preserve order, deduplicate

    with st.form("change_owner_form"):
        new_owner = st.selectbox(
            "Velg ny prosjektansvarlig",
            unique_members,
            index=unique_members.index(current_owner) if current_owner in unique_members else 0,
        )
        change_owner_clicked = st.form_submit_button("Endre prosjektansvarlig")

        if change_owner_clicked:
            result = api.update_project(project_id, USERNAME, project_owner=new_owner)
            if result.get("success"):
                st.success(f"✅ Prosjektansvarlig endret til {new_owner}")
                _clear_cache()
                st.rerun()
            else:
                st.error(f"Feil: {result.get('error', 'Ukjent feil')}")
else:
    st.info("Bare prosjektansvarlig kan endre denne innstillingen.")

st.markdown("---")

# =====================================================================
# 3. Medlemmer
# =====================================================================
st.markdown("### 👥 Medlemmer")

members = project.get("allowed_users", [])
creator = project["created_by"]

st.write(f"**Opprettet av:** {creator}")
if members:
    st.write("**Medlemmer med tilgang:**")
    for member in members:
        col1, col2 = st.columns([4, 1])
        col1.write(f"• {member}")
        if is_owner and member != current_owner:
            if col2.button("Fjern", key=f"remove_{member}_{project_id}"):
                result = api.remove_project_access(project_id, member, USERNAME)
                if result.get("success"):
                    st.success(f"✅ {member} fjernet fra prosjektet.")
                    _clear_cache()
                    st.rerun()
                else:
                    st.error(f"Feil: {result.get('error', 'Ukjent feil')}")
else:
    st.write("Ingen ekstra medlemmer.")

# Legg til medlem
if is_owner:
    st.markdown("#### Legg til medlem")
    with st.form("add_member_form"):
        new_member = st.text_input(
            "Brukernavn",
            placeholder="f.eks. OLAS",
            help="Windows-brukernavn til den du vil gi tilgang",
        )
        add_clicked = st.form_submit_button("Legg til")

        if add_clicked:
            name = new_member.strip()
            if not name:
                st.error("Brukernavn kan ikke være tomt.")
            else:
                result = api._post(f"/api/projects/{project_id}/access", {
                    "username": name,
                    "granted_by": USERNAME,
                })
                if result.get("success"):
                    st.success(f"✅ {name} lagt til i prosjektet.")
                    _clear_cache()
                    st.rerun()
                elif "already" in result.get("message", "").lower():
                    st.warning(f"{name} har allerede tilgang.")
                else:
                    st.error(f"Feil: {result.get('error', 'Ukjent feil')}")

st.markdown("---")

# =====================================================================
# 4. Slett prosjekt (kun prosjektansvarlig, med bekreftelse)
# =====================================================================
st.markdown("### 🗑️ Slett prosjekt")

if not is_owner:
    st.info("Bare prosjektansvarlig kan slette prosjektet.")
else:
    st.warning(
        "⚠️ **Advarsel:** Sletting av prosjektet kan ikke angres. "
        "All data knyttet til prosjektet vil bli fjernet."
    )
    with st.form("delete_project_form"):
        confirm_text = st.text_input(
            'Skriv **SLETT** for å bekrefte sletting',
            placeholder="SLETT",
        )
        delete_clicked = st.form_submit_button("Slett prosjekt", type="primary")

        if delete_clicked:
            if confirm_text.strip() != "SLETT":
                st.error('Du må skrive "SLETT" for å bekrefte.')
            else:
                result = api.delete_project(project_id, USERNAME, confirm="SLETT")
                if result.get("success"):
                    st.success("✅ Prosjektet er slettet.")
                    _clear_cache()
                    st.rerun()
                else:
                    st.error(f"Feil: {result.get('error', 'Ukjent feil')}")
