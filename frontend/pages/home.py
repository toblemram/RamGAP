# -*- coding: utf-8 -*-
"""
Home Page — Prosjektoversikt
==============================
Project list and project detail view.
"""

import threading
import streamlit as st
from components.auth import require_username
from components.api_client import APIClient

USERNAME = require_username()
api = APIClient()

# Custom CSS for activity rows
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1E88E5;
        text-align: center;
        padding: 1rem 0;
    }
    .greeting {
        font-size: 1.8rem;
        color: #333;
        margin-bottom: 0.5rem;
    }
    .activity-row {
        font-size: 0.85rem;
        color: #444;
        padding: 2px 0;
        line-height: 1.6;
    }
    .act-user {
        color: #1E88E5;
        font-weight: 600;
    }
    .act-ts {
        color: #999;
        font-size: 0.78rem;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Cached helpers
# ---------------------------------------------------------------------------

@st.cache_data(ttl=60)
def _cached_calculations(project_id, limit):
    return api.get_plaxis_calculations(project_id=project_id, limit=limit)


@st.cache_data(ttl=30)
def _cached_projects(username: str) -> list:
    return api.get_projects(username)


@st.cache_data(ttl=30)
def _cached_project_activities(project_id: int, limit: int = 3) -> list:
    return api.get_project_activities(project_id, limit)


def _log_project(project_id: int, atype: str, aname: str):
    _cached_calculations.clear()
    threading.Thread(
        target=api.log_project_activity,
        args=(project_id, USERNAME, atype, aname),
        daemon=True,
    ).start()


def _log_activity(atype: str, aname: str):
    threading.Thread(
        target=api.log_activity,
        args=(USERNAME, atype, aname),
        daemon=True,
    ).start()


# ---------------------------------------------------------------------------
# Session state defaults
# ---------------------------------------------------------------------------

if 'selected_project' not in st.session_state:
    st.session_state.selected_project = None

_TYPE_ICONS = {
    'Plaxis': '🔧', 'GeoTolk': '🗺️',
    'project': '📁', 'Regneark': '📊',
    'Modellering': '🏗️', 'Rapport': '📄',
}


# ---------------------------------------------------------------------------
# Project detail view
# ---------------------------------------------------------------------------

def show_project_view():
    """Show project detail view."""
    project = st.session_state.selected_project
    if not project:
        st.rerun()
        return

    if st.button("← Tilbake til oversikt"):
        st.session_state.selected_project = None
        st.rerun()

    st.subheader(f"📁 {project['name']}")
    st.caption(project.get('description') or 'Ingen beskrivelse')
    st.markdown("---")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("### 📋 Aktiviteter")
        calculations = _cached_calculations(project['id'], 10)

        if calculations:
            for calc in calculations:
                status = calc.get('status', 'unknown')
                status_text = {
                    'started': 'Påbegynt', 'running': 'Pågår',
                    'completed': 'Fullført', 'failed': 'Feilet',
                }.get(status, 'Ukjent')
                status_icon = {
                    'started': '🔄', 'running': '⏳',
                    'completed': '✅', 'failed': '❌',
                }.get(status, '❓')

                activity_name = calc.get('activity_name', 'Plaxis beregning')
                timestamp = calc.get('started_at', '')[:10] if calc.get('started_at') else ''

                with st.expander(f"{status_icon} {activity_name} - {status_text}"):
                    st.caption(f"Dato: {timestamp}")

                    structures = calc.get('structures', {})
                    spunts = structures.get('spunts', [])
                    anchors = structures.get('anchors', [])
                    if spunts or anchors:
                        st.markdown("**Strukturer:**")
                        if spunts:
                            st.write(f"• Spunter: {', '.join(spunts)}")
                        if anchors:
                            st.write(f"• Ankere: {', '.join(anchors)}")

                    phases = calc.get('phases', {})
                    if phases.get('capacity') or phases.get('msf') or phases.get('displacement'):
                        st.markdown("**Analyser:**")
                        if phases.get('capacity'):
                            st.write(f"• Kapasitet: {', '.join(phases['capacity'])}")
                        if phases.get('msf'):
                            st.write(f"• MSF: {', '.join(phases['msf'])}")
                        if phases.get('displacement'):
                            st.write(f"• Deformasjon: {', '.join(phases['displacement'])}")

                    if status == 'completed':
                        results = calc.get('results', {})
                        if results and results.get('msf'):
                            st.markdown("**Resultater:**")
                            for phase, value in results['msf'].items():
                                st.write(f"• MSF {phase}: {value:.2f}" if value else f"• MSF {phase}: -")
                        output_file = calc.get('output_file')
                        if output_file:
                            st.success(f"📁 {output_file}")
                    elif status == 'failed':
                        st.error(f"Feil: {calc.get('error_message', 'Ukjent feil')}")

                    st.markdown("---")
                    col_pwd, col_btn = st.columns([2, 1])
                    with col_pwd:
                        rerun_pwd = st.text_input(
                            "Plaxis passord", type="password",
                            key=f"rerun_pwd_{calc['id']}",
                            help="Oppgi passord for å kjøre på nytt",
                        )
                    with col_btn:
                        if st.button("🔄 Kjør på nytt", key=f"rerun_btn_{calc['id']}", use_container_width=True):
                            if rerun_pwd:
                                with st.spinner("Kjører beregning på nytt..."):
                                    result = api.rerun_plaxis_calculation(calc['id'], rerun_pwd, session_id=USERNAME)
                                    if result.get('success'):
                                        st.success("✅ Beregning fullført!")
                                        _cached_calculations.clear()
                                        st.rerun()
                                    else:
                                        st.error(f"Feil: {result.get('error', 'Ukjent feil')}")
                            else:
                                st.warning("Oppgi passord først")
        else:
            st.info("Ingen aktiviteter ennå. Start en ny aktivitet til høyre!")

    with col2:
        st.markdown("### 🚀 Start ny aktivitet")
        st.markdown("Velg type aktivitet:")

        if st.button("🔧 Plaxis automatisering", use_container_width=True, key="btn_plaxis"):
            st.session_state.plaxis_level = 1
            st.session_state.plaxis_connected = False
            st.session_state.plaxis_model_data = None
            _log_project(project['id'], 'Plaxis', 'Plaxis automatisering startet')
            st.switch_page("pages/plaxis.py")

        if st.button("🗺️ GeoTolk", use_container_width=True, key="btn_geotolk"):
            st.session_state.geotolk_step = 1
            st.session_state.geotolk_files = []
            _log_project(project['id'], 'GeoTolk', 'GeoTolk startet')
            st.switch_page("pages/geotolk.py")

        if st.button("📊 Regneark", use_container_width=True, key="btn_regneark"):
            _log_project(project['id'], 'Regneark', 'Regneark åpnet')
            st.success("Regneark åpnet! (Demo)")

        if st.button("🏗️ Modellering", use_container_width=True, key="btn_modellering"):
            _log_project(project['id'], 'Modellering', 'Modellering startet')
            st.switch_page("pages/modellering.py")

        if st.button("📄 Rapport", use_container_width=True, key="btn_rapport"):
            _log_project(project['id'], 'Rapport', 'Rapport generering startet')
            st.success("Rapport generering startet! (Demo)")

    # Recent activity log
    st.markdown("---")
    st.markdown("### 📋 Siste aktiviteter")
    recent_activities = _cached_project_activities(project['id'], 10)
    if recent_activities:
        for act in recent_activities:
            ts   = (act.get('timestamp') or '')[:16]
            icon = _TYPE_ICONS.get(act.get('activity_type', ''), '📌')
            name = act.get('activity_name', '')
            user = act.get('username', '')
            st.markdown(
                f'<div class="activity-row">{icon} {name} '
                f'— <span class="act-user">{user}</span> '
                f'<span class="act-ts">{ts}</span></div>',
                unsafe_allow_html=True,
            )
    else:
        st.info("Ingen aktiviteter logget ennå.")

    st.markdown("---")
    with st.expander("ℹ️ Prosjektinformasjon"):
        st.write(f"**Opprettet av:** {project.get('created_by')}")
        st.write(f"**Opprettet:** {project.get('created_at', '')[:10] if project.get('created_at') else 'Ukjent'}")
        allowed = project.get('allowed_users', [])
        if allowed:
            st.write(f"**Brukere med tilgang:** {', '.join(allowed)}")


# ---------------------------------------------------------------------------
# Home page
# ---------------------------------------------------------------------------

def show_home():
    """Show home page — all projects with description and 3 last activities."""
    st.markdown(f'<div class="greeting">Hei, {USERNAME}! 👋</div>', unsafe_allow_html=True)
    st.markdown("")
    st.subheader("📁 Mine prosjekter")

    projects = _cached_projects(USERNAME)
    if not projects:
        st.info("Ingen prosjekter ennå. Gå til **Prosjektinnstillinger** i menyen for å opprette et.")
        return

    for project in projects:
        with st.container():
            col_info, col_btn = st.columns([5, 1])
            with col_info:
                st.markdown(f"**📁 {project['name']}**")
                st.caption(project.get('description') or 'Ingen beskrivelse')

                activities = _cached_project_activities(project['id'], 3)
                if activities:
                    for act in activities:
                        ts   = (act.get('timestamp') or '')[:10]
                        icon = _TYPE_ICONS.get(act.get('activity_type', ''), '📌')
                        name = act.get('activity_name', '')
                        user = act.get('username', '')
                        st.markdown(
                            f'<div class="activity-row">{icon} {name} '
                            f'— <span class="act-user">{user}</span> '
                            f'<span class="act-ts">{ts}</span></div>',
                            unsafe_allow_html=True,
                        )
                else:
                    st.caption('_Ingen aktivitet ennå_')

            with col_btn:
                st.markdown("&nbsp;", unsafe_allow_html=True)
                if st.button("Åpne →", key=f"open_{project['id']}", use_container_width=True):
                    st.session_state.selected_project = project
                    _log_activity('project', f"Åpnet: {project['name']}")
                    st.rerun()
        st.divider()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

st.markdown('<div class="main-header">RamGAP</div>', unsafe_allow_html=True)

if st.session_state.selected_project:
    show_project_view()
else:
    show_home()

st.divider()
st.caption("RamGAP - Utviklingsversjon")
