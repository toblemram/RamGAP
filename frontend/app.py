# -*- coding: utf-8 -*-
"""
RamGAP Frontend - Main Entry Point
====================================
Home page, project list, project view, and project setup.
Plaxis automation (pages/plaxis.py) and GeoTolk (pages/geotolk.py)
are separate pages, navigated to via st.switch_page().
"""

import sys
import os
import threading
import streamlit as st

# Ensure frontend/ root is importable from both app.py and pages/
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from components.api_client import APIClient

# Page config — must be the first Streamlit call
st.set_page_config(
    page_title="RamGAP",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded",
)


def _get_username() -> str:
    try:
        return os.getlogin()
    except OSError:
        return os.environ.get("USERNAME", os.environ.get("USER", "User"))


USERNAME = _get_username()
api = APIClient()

# Custom CSS
st.markdown("""
<style>
    /* Hide Streamlit's auto-generated pages navigation */
    [data-testid="stSidebarNav"] { display: none !important; }

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
    .project-shortcut {
        padding: 1rem 1.2rem;
        border-radius: 10px;
        background-color: #f0f4ff;
        border-left: 5px solid #1E88E5;
        margin-bottom: 0.6rem;
        cursor: pointer;
        transition: background 0.15s;
    }
    .project-shortcut:hover { background-color: #dce8ff; }
    .project-title {
        font-size: 1.1rem;
        font-weight: 600;
        color: #1E88E5;
    }
    .project-desc {
        font-size: 0.85rem;
        color: #666;
        margin-top: 2px;
    }
    .activity-item {
        padding: 0.5rem 0;
        border-bottom: 1px solid #eee;
    }
    .project-card {
        background: #f8faff;
        border: 1px solid #dce8ff;
        border-radius: 10px;
        padding: 1rem 1.2rem;
        margin-bottom: 1rem;
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


@st.cache_data(ttl=60)
def _cached_calculations(project_id, limit):
    return api.get_plaxis_calculations(project_id=project_id, limit=limit)


@st.cache_data(ttl=30)
def _cached_projects(username: str) -> list:
    return api.get_projects(username)


@st.cache_data(ttl=15)
def _cached_health() -> bool:
    return api.is_healthy()


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


# Initialize session state
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'home'
if 'selected_project' not in st.session_state:
    st.session_state.selected_project = None

# Plaxis session state
if 'plaxis_connected' not in st.session_state:
    st.session_state.plaxis_connected = False
if 'plaxis_port' not in st.session_state:
    st.session_state.plaxis_port = 10000
if 'plaxis_password' not in st.session_state:
    st.session_state.plaxis_password = ''
if 'plaxis_output_port' not in st.session_state:
    st.session_state.plaxis_output_port = 10001
if 'plaxis_output_password' not in st.session_state:
    st.session_state.plaxis_output_password = ''
if 'plaxis_level' not in st.session_state:
    st.session_state.plaxis_level = 1
if 'plaxis_model_data' not in st.session_state:
    st.session_state.plaxis_model_data = None
if 'plaxis_selected_function' not in st.session_state:
    st.session_state.plaxis_selected_function = None
if 'plaxis_selected_spunts' not in st.session_state:
    st.session_state.plaxis_selected_spunts = []
if 'plaxis_selected_anchors' not in st.session_state:
    st.session_state.plaxis_selected_anchors = []
if 'plaxis_selected_phases' not in st.session_state:
    st.session_state.plaxis_selected_phases = {}
if 'plaxis_demo_mode' not in st.session_state:
    st.session_state.plaxis_demo_mode = False
if 'plaxis_activity_name' not in st.session_state:
    st.session_state.plaxis_activity_name = ''

# GeoTolk session state
if 'geotolk_step' not in st.session_state:
    st.session_state.geotolk_step = 1
if 'geotolk_activity_name' not in st.session_state:
    st.session_state.geotolk_activity_name = ''
if 'geotolk_session_id' not in st.session_state:
    st.session_state.geotolk_session_id = None
if 'geotolk_files' not in st.session_state:
    st.session_state.geotolk_files = []  # List of {filename, content, parsed_data}
if 'geotolk_current_file' not in st.session_state:
    st.session_state.geotolk_current_file = 0
if 'geotolk_layers' not in st.session_state:
    st.session_state.geotolk_layers = []  # Current file's layers


def show_project_view():
    """Show project detail view"""
    project = st.session_state.selected_project
    if not project:
        st.session_state.current_page = 'home'
        st.rerun()
        return
    
    # Back button
    if st.button("← Tilbake til oversikt"):
        st.session_state.selected_project = None
        st.session_state.current_page = 'home'
        st.rerun()
    
    st.subheader(f"📁 {project['name']}")
    st.caption(project.get('description') or 'Ingen beskrivelse')
    st.markdown("---")
    
    # Two columns: Activities and New Activity
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### 📋 Aktiviteter")
        
        calculations = _cached_calculations(project['id'], 10)
        
        if calculations:
            for calc in calculations:
                status = calc.get('status', 'unknown')
                
                # Map status to Norwegian
                status_text = {
                    'started': 'Påbegynt',
                    'running': 'Pågår',
                    'completed': 'Fullført',
                    'failed': 'Feilet'
                }.get(status, 'Ukjent')
                
                status_icon = {
                    'started': '🔄',
                    'running': '⏳',
                    'completed': '✅',
                    'failed': '❌'
                }.get(status, '❓')
                
                activity_name = calc.get('activity_name', 'Plaxis beregning')
                timestamp = calc.get('started_at', '')[:10] if calc.get('started_at') else ''
                
                with st.expander(f"{status_icon} {activity_name} - {status_text}"):
                    st.caption(f"Dato: {timestamp}")
                    
                    # Show structures
                    structures = calc.get('structures', {})
                    spunts = structures.get('spunts', [])
                    anchors = structures.get('anchors', [])
                    
                    if spunts or anchors:
                        st.markdown("**Strukturer:**")
                        if spunts:
                            st.write(f"• Spunter: {', '.join(spunts)}")
                        if anchors:
                            st.write(f"• Ankere: {', '.join(anchors)}")
                    
                    # Show phases
                    phases = calc.get('phases', {})
                    if phases.get('capacity') or phases.get('msf') or phases.get('displacement'):
                        st.markdown("**Analyser:**")
                        if phases.get('capacity'):
                            st.write(f"• Kapasitet: {', '.join(phases['capacity'])}")
                        if phases.get('msf'):
                            st.write(f"• MSF: {', '.join(phases['msf'])}")
                        if phases.get('displacement'):
                            st.write(f"• Deformasjon: {', '.join(phases['displacement'])}")
                    
                    # Show results summary if completed
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
                    
                    # Re-run button
                    st.markdown("---")
                    col_pwd, col_btn = st.columns([2, 1])
                    with col_pwd:
                        rerun_pwd = st.text_input(
                            "Plaxis passord",
                            type="password",
                            key=f"rerun_pwd_{calc['id']}",
                            help="Oppgi passord for å kjøre på nytt"
                        )
                    with col_btn:
                        if st.button("🔄 Kjør på nytt", key=f"rerun_btn_{calc['id']}", use_container_width=True):
                            if rerun_pwd:
                                with st.spinner("Kjører beregning på nytt..."):
                                    result = api.rerun_plaxis_calculation(
                                        calc['id'], rerun_pwd, session_id=USERNAME)
                                    if result.get('success'):
                                        st.success("✅ Beregning fullført!")
                                        _cached_calculations.clear()
                                        st.rerun()
                                    else:
                                        st.error(f"Feil: {result.get('error', 'Ukjent feil')}")
                            else:
                                st.warning("Oppgi passord først")
        else:
            st.info("Ingen Plaxis-aktiviteter ennå.")

        # --- Modeling activities ---
        st.markdown("### 🏗️ Modellering-aktiviteter")
        modeling_acts = api.get_modeling_activities(project['id'])
        if modeling_acts:
            for mact in modeling_acts:
                m_status = mact.get('status', 'active')
                m_icon = {'active': '🟡', 'has_excel': '🟠', 'has_results': '🟢'}.get(m_status, '❓')
                m_label = {'active': 'Ingen filer', 'has_excel': 'Excel lastet opp', 'has_results': 'Resultater klar'}.get(m_status, m_status)
                m_name = mact.get('name', '')
                m_ts = (mact.get('created_at') or '')[:10]

                with st.expander(f"{m_icon} {m_name} — {m_label}"):
                    st.caption(f"Dato: {m_ts}")
                    if mact.get('has_excel'):
                        st.write(f"📊 Excel: {mact.get('excel_filename', '')}")
                    if mact.get('has_ifc'):
                        st.write(f"📐 IFC: {mact.get('ifc_filename', '')}")
                    if mact.get('has_results'):
                        st.success("✅ Optimeringsresultater tilgjengelig")
                    if st.button("Åpne i Modellering →", key=f"open_mod_{mact['id']}", use_container_width=True):
                        st.session_state.modeling_activity_id = mact['id']
                        st.switch_page("pages/modellering.py")
        else:
            st.info("Ingen modellering-aktiviteter ennå.")
    
    with col2:
        st.markdown("### 🚀 Start ny aktivitet")
        
        st.markdown("Velg type aktivitet:")
        
        # Navigate to separate Plaxis page
        if st.button("🔧 Plaxis automatisering", use_container_width=True, key="btn_plaxis"):
            st.session_state.plaxis_level = 1
            st.session_state.plaxis_connected = False
            st.session_state.plaxis_model_data = None
            _log_project(project['id'], 'Plaxis', 'Plaxis automatisering startet')
            st.switch_page("pages/plaxis.py")

        # Navigate to separate GeoTolk page
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
    
    # Recent activity log (all types: Plaxis, GeoTolk, Modellering, etc.)
    st.markdown("---")
    st.markdown("### 📋 Siste aktiviteter")
    recent_activities = _cached_project_activities(project['id'], 10)
    if recent_activities:
        type_icons = {
            'Plaxis': '🔧', 'GeoTolk': '🗺️',
            'project': '📁', 'Regneark': '📊',
            'Modellering': '🏗️', 'Rapport': '📄',
        }
        for act in recent_activities:
            ts   = (act.get('timestamp') or '')[:16]
            icon = type_icons.get(act.get('activity_type', ''), '📌')
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

    # Project info
    st.markdown("---")
    with st.expander("ℹ️ Prosjektinformasjon"):
        st.write(f"**Opprettet av:** {project.get('created_by')}")
        st.write(f"**Opprettet:** {project.get('created_at', '')[:10] if project.get('created_at') else 'Ukjent'}")
        allowed = project.get('allowed_users', [])
        if allowed:
            st.write(f"**Brukere med tilgang:** {', '.join(allowed)}")


# Plaxis and GeoTolk workflows have been moved to separate Streamlit pages:
#   frontend/pages/plaxis.py
#   frontend/pages/geotolk.py


# ---------------------------------------------------------------------------
# Dummy module pages
# ---------------------------------------------------------------------------

def show_geogpt():
    """GeoGPT — placeholder page"""
    st.title("🤖 GeoGPT")
    st.markdown("---")
    st.info(
        "**GeoGPT** er en AI-assistent spesialisert for geoteknikk.\n\n"
        "Her vil du kunne stille spørsmål om geotekniske standarder, "
        "tolke grunnundersøkelser, og få hjelp med beregninger.\n\n"
        "_Funksjonalitet er under utvikling._"
    )
    st.markdown("#### Planlagte funksjoner")
    st.markdown("""
    - 💬 Chat-grensesnitt for geotekniske spørsmål  
    - 📄 Opplasting og analyse av rapporter  
    - 🔗 Kobling mot prosjektdata i RamGAP  
    - 📚 Søk i standarder og normer  
    """)


def show_standarder():
    """Standarder — placeholder page"""
    st.title("📚 Standarder")
    st.markdown("---")
    st.info(
        "Her finner du relevante tekniske standarder og normer for geoteknikk og peling.\n\n"
        "_Funksjonalitet er under utvikling._"
    )
    st.markdown("#### Planlagte standarder")
    st.markdown("""
    - NS-EN 1997 (Eurocode 7) — Geoteknisk prosjektering  
    - NS-EN 12699 — Utførelse av spesielle geotekniske arbeider  
    - NS-EN 14199 — Mikropeler  
    - NGF-veiledninger  
    """)


def show_excel_ark():
    """Excel-ark — placeholder page"""
    st.title("📊 Excel-ark")
    st.markdown("---")
    st.info(
        "Her finner du standardiserte Excel-ark for beregninger og dokumentasjon.\n\n"
        "_Funksjonalitet er under utvikling._"
    )
    st.markdown("#### Planlagte regneark")
    st.markdown("""
    - 🏗️ Ramme- og pelekapasitet  
    - 📐 Setningsberegning  
    - 🔩 Forankringskapasitet  
    - 📋 Grunnundersøkelses-sammenstilling  
    """)


def show_ramgap_endringer():
    """RamGAP endringer og versjoner — placeholder page"""
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


def show_opplaering():
    """Opplæring — placeholder page"""
    st.title("🎓 Opplæring")
    st.markdown("---")
    st.info(
        "Kurs og opplæringsmateriell for bruk av RamGAP.\n\n"
        "_Innhold er under utvikling._"
    )
    st.markdown("#### Planlagte moduler")
    st.markdown("""
    - 🟢 Kom i gang med RamGAP  
    - 🔧 Plaxis-automatisering trinn for trinn  
    - 🗺️ GeoTolk — tolking av sonderinger  
    - 🤖 Bruk av GeoGPT  
    """)


# ---------------------------------------------------------------------------


def show_project_setup():
    """Show project setup page"""
    if st.button("← Tilbake til oversikt"):
        st.session_state.current_page = 'home'
        st.rerun()

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
                st.error("Prosjektnavn er påkrevd")
            else:
                # Parse allowed users
                allowed_users = [u.strip() for u in allowed_users_input.split(',') if u.strip()]
                
                result = api.create_project(project_name, project_description, USERNAME, allowed_users)
                
                if result.get('id') or result.get('project'):
                    st.success(f"✅ Prosjekt '{project_name}' opprettet!")
                    _cached_projects.clear()
                    _log_activity('project', f'Opprettet: {project_name}')
                    st.rerun()
                else:
                    st.error(f"Feil: {result.get('error', 'Ukjent feil')}")
    
    # List existing projects
    st.markdown("---")
    st.markdown("### Dine prosjekter")
    
    projects = _cached_projects(USERNAME)
    if projects:
        for project in projects:
            with st.expander(f"📁 {project['name']}", expanded=False):
                st.write(f"**Beskrivelse:** {project.get('description') or 'Ingen beskrivelse'}")
                st.write(f"**Opprettet av:** {project.get('created_by')}")
                st.write(f"**Opprettet:** {project.get('created_at', '')[:10] if project.get('created_at') else 'Ukjent'}")
                
                allowed = project.get('allowed_users', [])
                if allowed:
                    st.write(f"**Brukere med tilgang:** {', '.join(allowed)}")
    else:
        st.info("Ingen prosjekter ennå. Opprett ditt første prosjekt ovenfor!")



def show_home():
    """Show home page — all projects with description and 3 last activities"""
    st.markdown(f'<div class="greeting">Hei, {USERNAME}! 👋</div>', unsafe_allow_html=True)
    st.markdown("")
    st.subheader("📁 Mine prosjekter")

    projects = _cached_projects(USERNAME)
    if not projects:
        st.info("Ingen prosjekter ennå. Gå til **Prosjekt innstillinger** i menyen for å opprette et.")
        return

    for project in projects:
        with st.container():
            col_info, col_btn = st.columns([5, 1])
            with col_info:
                st.markdown(f"**📁 {project['name']}**")
                st.caption(project.get('description') or 'Ingen beskrivelse')

                activities = _cached_project_activities(project['id'], 3)
                if activities:
                    type_icons = {
                        'Plaxis': '🔧', 'GeoTolk': '🗺️',
                        'project': '📁', 'Regneark': '📊',
                        'Modellering': '🏗️',
                    }
                    for act in activities:
                        ts   = (act.get('timestamp') or '')[:10]
                        icon = type_icons.get(act.get('activity_type', ''), '📌')
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
                    st.session_state.current_page = 'project_view'
                    _log_activity('project', f"Åpnet: {project['name']}")
                    st.rerun()
        st.divider()


def main():
    """Main application"""
    
    # Header
    st.markdown('<div class="main-header">RamGAP</div>', unsafe_allow_html=True)
    
    # Sidebar — persistent navigation
    with st.sidebar:
        st.markdown("### 🏗️ RamGAP")
        st.divider()

        nav_items = [
            ('home',             '🏠', 'Prosjekter'),
            ('geogpt',           '🤖', 'GeoGPT'),
            ('standarder',       '📚', 'Standarder'),
            ('excel_ark',        '📊', 'Excel-ark'),
            ('ramgap_endringer', '🔄', 'Endringer og versjoner'),
            ('opplaering',       '🎓', 'Opplæring'),
            ('project_setup',    '⚙️', 'Prosjekt innstillinger'),
        ]
        cur = st.session_state.current_page
        for page_key, icon, label in nav_items:
            btn_type = 'primary' if cur == page_key else 'secondary'
            if st.button(
                f"{icon}  {label}",
                key=f"nav_{page_key}",
                use_container_width=True,
                type=btn_type,
            ):
                st.session_state.current_page = page_key
                st.session_state.selected_project = None
                st.rerun()

        st.divider()
        st.caption(f"👤 **{USERNAME}**")
        if _cached_health():
            st.success("✅ Backend OK", icon=None)
        else:
            st.warning("⚠️ Backend utilgjengelig")

    # Route to the correct page
    page = st.session_state.current_page
    if page == 'project_setup':
        show_project_setup()
    elif page == 'project_view':
        show_project_view()
    elif page == 'geogpt':
        show_geogpt()
    elif page == 'standarder':
        show_standarder()
    elif page == 'excel_ark':
        show_excel_ark()
    elif page == 'ramgap_endringer':
        show_ramgap_endringer()
    elif page == 'opplaering':
        show_opplaering()
    else:
        show_home()
    
    # Footer
    st.divider()
    st.caption("RamGAP - Utviklingsversjon")


if __name__ == "__main__":
    main()
else:
    main()
