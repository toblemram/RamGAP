# -*- coding: utf-8 -*-
"""
RamGAP Streamlit Frontend
User interface for RamGAP application
"""

import streamlit as st
import requests
import os
from datetime import datetime

# Page config - må være først
st.set_page_config(
    page_title="RamGAP",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Configuration
BACKEND_URL = "http://localhost:5050"

# Get Windows username
def get_username():
    """Get the current Windows username"""
    try:
        return os.getlogin()
    except OSError:
        return os.environ.get('USERNAME', os.environ.get('USER', 'Ukjent'))

USERNAME = get_username()

# Page configuration
st.set_page_config(
    page_title="RamGAP",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
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
        margin-bottom: 1rem;
    }
    .status-box {
        padding: 2rem;
        border-radius: 10px;
        background-color: #E3F2FD;
        text-align: center;
        margin: 2rem 0;
    }
    .status-text {
        font-size: 1.5rem;
        color: #1565C0;
        font-weight: 500;
    }
    .project-card {
        padding: 1rem;
        border-radius: 8px;
        background-color: #f8f9fa;
        border-left: 4px solid #1E88E5;
        margin-bottom: 0.5rem;
    }
    .activity-item {
        padding: 0.5rem;
        border-bottom: 1px solid #eee;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_data(ttl=30)  # Cache i 30 sekunder
def check_backend_health():
    """Check if backend is running"""
    try:
        response = requests.get(f"{BACKEND_URL}/api/health", timeout=1)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False


@st.cache_data(ttl=10)  # Cache i 10 sekunder
def get_user_projects_cached(username):
    """Get projects for current user"""
    try:
        response = requests.get(
            f"{BACKEND_URL}/api/projects",
            params={'username': username},
            timeout=3
        )
        if response.status_code == 200:
            return response.json().get('projects', [])
    except requests.exceptions.RequestException:
        pass
    return []


def get_user_projects():
    """Wrapper for cached function"""
    return get_user_projects_cached(USERNAME)


@st.cache_data(ttl=10)  # Cache i 10 sekunder
def get_recent_activity_cached(username):
    """Get recent activity for current user"""
    try:
        response = requests.get(
            f"{BACKEND_URL}/api/activity",
            params={'username': username, 'limit': 5},
            timeout=3
        )
        if response.status_code == 200:
            return response.json().get('activities', [])
    except requests.exceptions.RequestException:
        pass
    return []


def get_recent_activity():
    """Wrapper for cached function"""
    return get_recent_activity_cached(USERNAME)


@st.cache_data(ttl=5)  # Cache i 5 sekunder
def get_plaxis_calculations_cached(project_id=None, limit=10):
    """Get Plaxis calculations, optionally filtered by project"""
    try:
        params = {'limit': limit}
        if project_id:
            params['project_id'] = project_id
        
        response = requests.get(
            f"{BACKEND_URL}/api/plaxis/calculations",
            params=params,
            timeout=3
        )
        if response.status_code == 200:
            return response.json().get('calculations', [])
    except requests.exceptions.RequestException:
        pass
    return []


def get_plaxis_calculations(project_id=None, limit=10):
    """Wrapper for cached function"""
    return get_plaxis_calculations_cached(project_id, limit)


def rerun_plaxis_calculation(calc_id, input_password, output_password=None):
    """Re-run a previous Plaxis calculation"""
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/plaxis/calculations/{calc_id}/rerun",
            json={
                'session_id': USERNAME,
                'input_password': input_password,
                'output_password': output_password or input_password
            },
            timeout=300
        )
        return response.json()
    except requests.exceptions.RequestException as e:
        return {'success': False, 'error': str(e)}


def create_project(name, description, allowed_users):
    """Create a new project"""
    # Clear project cache when creating new
    get_user_projects_cached.clear()
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/projects",
            json={
                'name': name,
                'description': description,
                'created_by': USERNAME,
                'allowed_users': allowed_users
            },
            timeout=3
        )
        return response.status_code == 201, response.json()
    except requests.exceptions.RequestException as e:
        return False, {'error': str(e)}


def log_activity(activity_type, activity_name):
    """Log user activity"""
    try:
        requests.post(
            f"{BACKEND_URL}/api/activity",
            json={
                'username': USERNAME,
                'activity_type': activity_type,
                'activity_name': activity_name
            },
            timeout=2
        )
    except:
        pass


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
        
        # Get Plaxis calculations for this project
        calculations = get_plaxis_calculations(project_id=project['id'], limit=10)
        
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
                                    result = rerun_plaxis_calculation(calc['id'], rerun_pwd)
                                    if result.get('success'):
                                        st.success("✅ Beregning fullført!")
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
        
        # Plaxis automation - opens the full workflow
        if st.button("🔧 Plaxis automatisering", use_container_width=True, key="btn_plaxis"):
            st.session_state.current_page = 'plaxis_automation'
            st.session_state.plaxis_level = 1
            log_project_activity(project['id'], 'Plaxis', 'Plaxis automatisering startet')
            st.rerun()
        
        if st.button("📊 Regneark", use_container_width=True, key="btn_regneark"):
            log_project_activity(project['id'], 'Regneark', 'Regneark åpnet')
            st.success("Regneark åpnet! (Demo)")
            st.rerun()
        
        if st.button("🏗️ Modellering", use_container_width=True, key="btn_modellering"):
            log_project_activity(project['id'], 'Modellering', 'Modellering startet')
            st.success("Modellering startet! (Demo)")
            st.rerun()
        
        if st.button("📄 Rapport", use_container_width=True, key="btn_rapport"):
            log_project_activity(project['id'], 'Rapport', 'Rapport generering startet')
            st.success("Rapport generering startet! (Demo)")
            st.rerun()
    
    # Project info
    st.markdown("---")
    with st.expander("ℹ️ Prosjektinformasjon"):
        st.write(f"**Opprettet av:** {project.get('created_by')}")
        st.write(f"**Opprettet:** {project.get('created_at', '')[:10] if project.get('created_at') else 'Ukjent'}")
        allowed = project.get('allowed_users', [])
        if allowed:
            st.write(f"**Brukere med tilgang:** {', '.join(allowed)}")


@st.cache_data(ttl=5)  # Cache i 5 sekunder
def get_project_activities(project_id):
    """Get activities for a specific project"""
    try:
        response = requests.get(
            f"{BACKEND_URL}/api/projects/{project_id}/activities",
            params={'limit': 10},
            timeout=3
        )
        if response.status_code == 200:
            return response.json().get('activities', [])
    except requests.exceptions.RequestException:
        pass
    return []


def log_project_activity(project_id, activity_type, activity_name):
    """Log activity for a project"""
    # Clear cache when logging new activity
    get_project_activities.clear()
    get_plaxis_calculations_cached.clear()
    try:
        requests.post(
            f"{BACKEND_URL}/api/projects/{project_id}/activities",
            json={
                'username': USERNAME,
                'activity_type': activity_type,
                'activity_name': activity_name
            },
            timeout=2
        )
    except:
        pass


# ==================== PLAXIS AUTOMATION ====================

def plaxis_connect(port, password):
    """Connect to Plaxis server"""
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/plaxis/connect",
            json={'port': port, 'password': password, 'session_id': USERNAME},
            timeout=10
        )
        return response.json()
    except requests.exceptions.RequestException as e:
        return {'success': False, 'error': str(e)}


def plaxis_get_model_info():
    """Get model info from Plaxis"""
    try:
        response = requests.get(
            f"{BACKEND_URL}/api/plaxis/model-info",
            params={'session_id': USERNAME},
            timeout=30
        )
        return response.json()
    except requests.exceptions.RequestException as e:
        return {'success': False, 'error': str(e)}


def show_plaxis_automation():
    """Show Plaxis automation multi-level workflow"""
    project = st.session_state.selected_project
    
    # Back button
    col_back, col_title = st.columns([1, 4])
    with col_back:
        if st.button("← Tilbake til prosjekt"):
            st.session_state.current_page = 'project_view'
            st.session_state.plaxis_level = 1
            st.session_state.plaxis_connected = False
            st.session_state.plaxis_model_data = None
            st.rerun()
    
    with col_title:
        st.subheader("🔧 Plaxis Automatisering - Uttak av spuntberegninger")
    
    # Progress indicator
    levels = ["1. Tilkobling", "2. Funksjon", "3. Spunt/Ankere", "4. Faser", "5. Output"]
    current_level = st.session_state.plaxis_level
    
    # Level progress bar
    progress_cols = st.columns(5)
    for i, (col, level_name) in enumerate(zip(progress_cols, levels)):
        with col:
            if i + 1 < current_level:
                st.success(f"✓ {level_name}")
            elif i + 1 == current_level:
                st.info(f"→ {level_name}")
            else:
                st.caption(level_name)
    
    st.markdown("---")
    
    # Show current level
    if current_level == 1:
        show_plaxis_level1()
    elif current_level == 2:
        show_plaxis_level2()
    elif current_level == 3:
        show_plaxis_level3()
    elif current_level == 4:
        show_plaxis_level4()
    elif current_level == 5:
        show_plaxis_level5()


def show_plaxis_level1():
    """Level 1: Connect to Plaxis and load model"""
    st.markdown("### Nivå 1 – Innlesing av Plaxis-modell")
    st.markdown("Koble til en åpen Plaxis-modell for å hente ut strukturer og faser.")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        # Activity name - required
        st.markdown("#### Aktivitetsnavn")
        activity_name = st.text_input(
            "Gi aktiviteten et navn",
            value=st.session_state.plaxis_activity_name,
            placeholder="F.eks. 'Spuntberegning fase 1'",
            help="Navn som vises i aktivitetslisten"
        )
        st.session_state.plaxis_activity_name = activity_name
        
        st.markdown("---")
        st.markdown("#### Plaxis Input (modell)")
        
        # Port input - remember value
        port = st.number_input(
            "Input Port",
            min_value=1000,
            max_value=65535,
            value=st.session_state.plaxis_port,
            help="Plaxis Input server port (vanligvis 10000)"
        )
        
        # Password input - remember value
        password = st.text_input(
            "Input Passord",
            value=st.session_state.plaxis_password,
            type="password",
            help="Plaxis Input server passord"
        )
        
        st.markdown("---")
        st.markdown("#### Plaxis Output (resultater)")
        
        # Output port
        output_port = st.number_input(
            "Output Port",
            min_value=1000,
            max_value=65535,
            value=st.session_state.plaxis_output_port,
            help="Plaxis Output server port (vanligvis 10001)"
        )
        
        # Output password
        output_password = st.text_input(
            "Output Passord",
            value=st.session_state.plaxis_output_password,
            type="password",
            help="Plaxis Output server passord"
        )
        
        # Save values to session
        st.session_state.plaxis_port = port
        st.session_state.plaxis_password = password
        st.session_state.plaxis_output_port = output_port
        st.session_state.plaxis_output_password = output_password
        
        # Validation - require activity name
        if not activity_name.strip():
            st.warning("⚠️ Du må gi aktiviteten et navn for å fortsette")
        
        # Connect button
        if st.button("🔌 Koble til Plaxis", type="primary", use_container_width=True, disabled=not activity_name.strip()):
            with st.spinner("Kobler til Plaxis..."):
                result = plaxis_connect(port, password)
                
                if result.get('success'):
                    st.session_state.plaxis_connected = True
                    st.session_state.plaxis_demo_mode = result.get('demo_mode', False)
                    
                    # Load model info
                    model_result = plaxis_get_model_info()
                    if model_result.get('success'):
                        st.session_state.plaxis_model_data = model_result
                        st.session_state.plaxis_demo_mode = model_result.get('demo_mode', False)
                        st.success("✅ Tilkoblet! Modelldata lastet.")
                        st.rerun()
                    else:
                        st.error(f"Feil ved lasting av modell: {model_result.get('error')}")
                elif result.get('demo_mode'):
                    # Demo mode - use mock data
                    st.session_state.plaxis_connected = True
                    st.session_state.plaxis_demo_mode = True
                    model_result = plaxis_get_model_info()
                    st.session_state.plaxis_model_data = model_result
                    st.warning("⚠️ Demo-modus: plxscripting ikke tilgjengelig. Viser eksempeldata.")
                    st.rerun()
                else:
                    st.error(f"Tilkoblingsfeil: {result.get('error')}")
    
    with col2:
        st.markdown("#### Modellstatus")
        
        if st.session_state.plaxis_connected and st.session_state.plaxis_model_data:
            model = st.session_state.plaxis_model_data
            
            if st.session_state.plaxis_demo_mode:
                st.info("🎭 Demo-modus aktiv")
            else:
                st.success("✅ Tilkoblet til Plaxis")
            
            structures = model.get('structures', {})
            phases = model.get('phases', [])
            
            # Summary
            st.markdown("**Strukturer funnet:**")
            st.write(f"- Plater (spunt): {len(structures.get('plates', []))}")
            st.write(f"- Embedded beams: {len(structures.get('embedded_beams', []))}")
            st.write(f"- N2N-ankere: {len(structures.get('node_to_node_anchors', []))}")
            st.write(f"- Fixed-end ankere: {len(structures.get('fixed_end_anchors', []))}")
            st.write(f"- Geogrids: {len(structures.get('geogrids', []))}")
            
            st.markdown(f"**Antall faser:** {len(phases)}")
            
            # Show phases
            with st.expander("Vis alle faser"):
                for phase in phases:
                    st.write(f"- {phase['name']}")
            
            # Next button
            st.markdown("---")
            if st.button("Neste → Velg funksjon", type="primary", use_container_width=True):
                st.session_state.plaxis_level = 2
                st.rerun()
        else:
            st.info("Koble til Plaxis for å se modellinformasjon")


def show_plaxis_level2():
    """Level 2: Select function"""
    st.markdown("### Nivå 2 – Valg av funksjon")
    st.markdown("Velg hvilken type analyse som skal utføres.")
    
    functions = [
        {
            'id': 'optimize_depth',
            'name': 'Optimalisering av spuntdybde',
            'description': 'Endring av underkant spunt for å optimalisere design',
            'enabled': False
        },
        {
            'id': 'optimize_ks',
            'name': 'Optimalisering av KS-stab',
            'description': 'Endring av materialparametere og spuntdybde',
            'enabled': False
        },
        {
            'id': 'extract_results',
            'name': 'Uttak av spuntberegninger',
            'description': 'Hent ut resultater for kapasitetssjekk, Msf, og deformasjoner',
            'enabled': True
        }
    ]
    
    selected = st.session_state.plaxis_selected_function
    
    for func in functions:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"**{func['name']}**")
            st.caption(func['description'])
        with col2:
            if func['enabled']:
                if st.button(
                    "Velg" if selected != func['id'] else "✓ Valgt",
                    key=f"func_{func['id']}",
                    type="primary" if selected == func['id'] else "secondary",
                    use_container_width=True
                ):
                    st.session_state.plaxis_selected_function = func['id']
                    st.rerun()
            else:
                st.button("Kommer snart", disabled=True, key=f"func_{func['id']}_disabled")
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Forrige", use_container_width=True):
            st.session_state.plaxis_level = 1
            st.rerun()
    with col2:
        if st.button("Neste →", type="primary", use_container_width=True, disabled=not selected):
            st.session_state.plaxis_level = 3
            st.rerun()


def show_plaxis_level3():
    """Level 3: Select sheet pile and anchors"""
    st.markdown("### Nivå 3 – Valg av spunt og avstivninger")
    st.markdown("Velg hvilken spunt som skal analyseres og tilhørende avstivninger.")
    
    model = st.session_state.plaxis_model_data
    if not model:
        st.error("Ingen modelldata tilgjengelig")
        return
    
    structures = model.get('structures', {})
    
    # Get all potential sheet piles (plates and embedded beams)
    spunts = structures.get('plates', []) + structures.get('embedded_beams', [])
    anchors = structures.get('node_to_node_anchors', []) + structures.get('fixed_end_anchors', [])
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Velg spunt(er)")
        
        spunt_options = {s['name']: s for s in spunts}
        selected_spunt_names = st.multiselect(
            "Velg spunt(er) som skal analyseres",
            options=list(spunt_options.keys()),
            default=st.session_state.plaxis_selected_spunts,
            help="Velg en eller flere spunter"
        )
        st.session_state.plaxis_selected_spunts = selected_spunt_names
        
        # Show selected spunts info
        if selected_spunt_names:
            st.markdown("**Valgte spunter:**")
            for name in selected_spunt_names:
                spunt = spunt_options[name]
                st.write(f"- {spunt['display_name']}")
    
    with col2:
        st.markdown("#### Velg avstivninger")
        
        anchor_options = {a['name']: a for a in anchors}
        selected_anchor_names = st.multiselect(
            "Velg ankere/avstivninger",
            options=list(anchor_options.keys()),
            default=st.session_state.plaxis_selected_anchors,
            help="Velg ankere som tilhører valgt(e) spunt(er)"
        )
        st.session_state.plaxis_selected_anchors = selected_anchor_names
        
        # Show selected anchors info
        if selected_anchor_names:
            st.markdown("**Valgte ankere:**")
            for name in selected_anchor_names:
                anchor = anchor_options[name]
                st.write(f"- {anchor['display_name']}")
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Forrige", use_container_width=True):
            st.session_state.plaxis_level = 2
            st.rerun()
    with col2:
        if st.button("Neste →", type="primary", use_container_width=True, 
                     disabled=len(selected_spunt_names) == 0):
            st.session_state.plaxis_level = 4
            st.rerun()


def show_plaxis_level4():
    """Level 4: Select phases and analysis types"""
    st.markdown("### Nivå 4 – Valg av faser og analysetype")
    st.markdown("Velg hvilke faser som skal analyseres og hvilke resultater som skal hentes ut.")
    
    model = st.session_state.plaxis_model_data
    if not model:
        st.error("Ingen modelldata tilgjengelig")
        return
    
    phases = model.get('phases', [])
    
    # Initialize phase selections if needed
    if not st.session_state.plaxis_selected_phases:
        st.session_state.plaxis_selected_phases = {
            phase['name']: {'msf': False, 'ux': False, 'capacity': False}
            for phase in phases
        }
    
    st.markdown("For hver fase, velg hvilke analyser som skal kjøres:")
    
    # Header row
    col_name, col_msf, col_ux, col_cap = st.columns([3, 1, 1, 1])
    with col_name:
        st.markdown("**Fase**")
    with col_msf:
        st.markdown("**Msf**")
    with col_ux:
        st.markdown("**Ux**")
    with col_cap:
        st.markdown("**Kapasitet**")
    
    st.markdown("---")
    
    # Phase rows
    for phase in phases:
        phase_name = phase['name']
        
        # Initialize if not exists
        if phase_name not in st.session_state.plaxis_selected_phases:
            st.session_state.plaxis_selected_phases[phase_name] = {'msf': False, 'ux': False, 'capacity': False}
        
        col_name, col_msf, col_ux, col_cap = st.columns([3, 1, 1, 1])
        
        with col_name:
            st.write(phase_name)
        
        with col_msf:
            msf = st.checkbox(
                "Msf",
                value=st.session_state.plaxis_selected_phases[phase_name].get('msf', False),
                key=f"msf_{phase_name}",
                label_visibility="collapsed"
            )
            st.session_state.plaxis_selected_phases[phase_name]['msf'] = msf
        
        with col_ux:
            ux = st.checkbox(
                "Ux",
                value=st.session_state.plaxis_selected_phases[phase_name].get('ux', False),
                key=f"ux_{phase_name}",
                label_visibility="collapsed"
            )
            st.session_state.plaxis_selected_phases[phase_name]['ux'] = ux
        
        with col_cap:
            cap = st.checkbox(
                "Kapasitet",
                value=st.session_state.plaxis_selected_phases[phase_name].get('capacity', False),
                key=f"cap_{phase_name}",
                label_visibility="collapsed"
            )
            st.session_state.plaxis_selected_phases[phase_name]['capacity'] = cap
    
    st.markdown("---")
    
    # Quick select buttons
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Velg alle Msf", use_container_width=True):
            for phase_name in st.session_state.plaxis_selected_phases:
                st.session_state.plaxis_selected_phases[phase_name]['msf'] = True
            st.rerun()
    with col2:
        if st.button("Velg alle Ux", use_container_width=True):
            for phase_name in st.session_state.plaxis_selected_phases:
                st.session_state.plaxis_selected_phases[phase_name]['ux'] = True
            st.rerun()
    with col3:
        if st.button("Velg alle Kapasitet", use_container_width=True):
            for phase_name in st.session_state.plaxis_selected_phases:
                st.session_state.plaxis_selected_phases[phase_name]['capacity'] = True
            st.rerun()
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Forrige", use_container_width=True):
            st.session_state.plaxis_level = 3
            st.rerun()
    with col2:
        # Check if any phase is selected
        any_selected = any(
            any(v for v in phase_sel.values())
            for phase_sel in st.session_state.plaxis_selected_phases.values()
        )
        if st.button("Neste →", type="primary", use_container_width=True, disabled=not any_selected):
            st.session_state.plaxis_level = 5
            st.rerun()


def show_plaxis_level5():
    """Level 5: Output settings and run"""
    st.markdown("### Nivå 5 – Output og resultater")
    st.markdown("Velg lagringsmappe og kjør beregningen.")
    
    # Summary of selections
    st.markdown("#### Oppsummering av valg")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Valgte spunter:**")
        for spunt in st.session_state.plaxis_selected_spunts:
            st.write(f"- {spunt}")
        
        st.markdown("**Valgte ankere:**")
        if st.session_state.plaxis_selected_anchors:
            for anchor in st.session_state.plaxis_selected_anchors:
                st.write(f"- {anchor}")
        else:
            st.write("- Ingen valgt")
    
    with col2:
        st.markdown("**Faser med analyser:**")
        for phase_name, selections in st.session_state.plaxis_selected_phases.items():
            active = [k for k, v in selections.items() if v]
            if active:
                st.write(f"- {phase_name}: {', '.join(active)}")
    
    st.markdown("---")
    
    # Output settings
    st.markdown("#### Output-innstillinger")
    
    output_path = st.text_input(
        "Lagringsmappe",
        value=os.path.expanduser("~/Documents/RamGAP_Results"),
        help="Mappe hvor resultater lagres"
    )
    
    output_format = st.selectbox(
        "Output-format",
        options=["Kun kritisk fase", "Alle valgte faser", "Kritisk snitt"],
        index=1
    )
    
    generate_excel = st.checkbox("Generer Excel spuntark", value=True)
    generate_report = st.checkbox("Generer beregningsrapport", value=False)
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Forrige", use_container_width=True):
            st.session_state.plaxis_level = 4
            st.rerun()
    
    with col2:
        if st.button("🚀 Kjør beregning", type="primary", use_container_width=True):
            run_plaxis_calculation(output_path, generate_excel)


def run_plaxis_calculation(output_path, generate_excel):
    """Run the actual Plaxis calculation via backend API"""
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Build job configuration
    status_text.text("Forbereder beregningsjobb...")
    progress_bar.progress(5)
    
    # Build structures for job
    model_data = st.session_state.plaxis_model_data or {}
    structures = model_data.get('structures', {})
    
    # Map selected names to structure categories
    job_structures = {
        "plates": [],
        "embedded_beams": [],
        "node_to_node_anchors": [],
        "fixed_end_anchors": [],
        "geogrids": []
    }
    
    # Add selected spunts
    for spunt_name in st.session_state.plaxis_selected_spunts:
        for plate in structures.get('plates', []):
            if plate['name'] == spunt_name:
                job_structures['plates'].append(spunt_name)
        for eb in structures.get('embedded_beams', []):
            if eb['name'] == spunt_name:
                job_structures['embedded_beams'].append(spunt_name)
    
    # Add selected anchors
    for anchor_name in st.session_state.plaxis_selected_anchors:
        for n2n in structures.get('node_to_node_anchors', []):
            if n2n['name'] == anchor_name:
                job_structures['node_to_node_anchors'].append(anchor_name)
        for fea in structures.get('fixed_end_anchors', []):
            if fea['name'] == anchor_name:
                job_structures['fixed_end_anchors'].append(anchor_name)
    
    # Build analysis config from phase selections
    capacity_phases = []
    msf_phases = []
    displacement_phases = []
    
    for phase_name, selections in st.session_state.plaxis_selected_phases.items():
        if selections.get('capacity'):
            capacity_phases.append(phase_name)
        if selections.get('msf'):
            msf_phases.append(phase_name)
        if selections.get('ux'):
            displacement_phases.append(phase_name)
    
    job = {
        "structures": job_structures,
        "analysis": {
            "capacity_check": {
                "enabled": len(capacity_phases) > 0,
                "phases": capacity_phases
            },
            "msf": {
                "enabled": len(msf_phases) > 0,
                "phases": msf_phases
            },
            "displacement": {
                "enabled": len(displacement_phases) > 0,
                "phases": displacement_phases,
                "component": "Ux"
            }
        },
        "resultsPath": {
            "path": output_path
        }
    }
    
    status_text.text("Sender beregning til Plaxis...")
    progress_bar.progress(15)
    
    # Get project_id if available
    project_id = None
    if st.session_state.selected_project:
        project_id = st.session_state.selected_project.get('id')
    
    # Call backend API
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/plaxis/run",
            json={
                'session_id': USERNAME,
                'job': job,
                'project_id': project_id,
                'activity_name': st.session_state.plaxis_activity_name or 'Plaxis beregning',
                'input_port': st.session_state.plaxis_port,
                'input_password': st.session_state.plaxis_password,
                'output_port': st.session_state.plaxis_output_port,
                'output_password': st.session_state.plaxis_output_password
            },
            timeout=300  # 5 minutes timeout for calculation
        )
        
        result = response.json()
        
        if result.get('success'):
            progress_bar.progress(100)
            status_text.text("Ferdig!")
            
            # Log activity
            if st.session_state.selected_project:
                log_project_activity(
                    st.session_state.selected_project['id'],
                    'Plaxis',
                    f"Spuntberegning fullført: {', '.join(st.session_state.plaxis_selected_spunts)}"
                )
            
            st.success("✅ Beregning fullført!")
            
            if result.get('demo_mode'):
                st.info("🎭 Demo-modus: Viser eksempelresultater")
            
            output_file = result.get('output_file')
            if output_file and output_file != 'Demo - ingen fil generert':
                st.info(f"📁 Resultater lagret i: {output_file}")
            
            # Show results
            st.markdown("---")
            st.markdown("#### Resultater")
            
            results = result.get('results', {})
            
            # MSF results
            msf_results = results.get('msf', {})
            if msf_results:
                st.markdown("**Msf-verdier:**")
                msf_data = {'Fase': list(msf_results.keys()), 'Msf': list(msf_results.values())}
                st.table(msf_data)
            
            # Displacement results
            displacement = results.get('displacement', {})
            if displacement:
                st.markdown("**Maks horisontal deformasjon:**")
                for struct_type, objects in displacement.items():
                    for obj_name, phases in objects.items():
                        ux_data = {'Fase': list(phases.keys()), f'{obj_name} Ux (mm)': list(phases.values())}
                        st.table(ux_data)
            
            # Capacity results
            capacity = results.get('capacity', {})
            if capacity:
                st.markdown("**Tverrsnittskrefter:**")
                for struct_type, objects in capacity.items():
                    if struct_type in ['plates', 'embedded_beams']:
                        for obj_name, phases in objects.items():
                            st.markdown(f"*{obj_name}:*")
                            cap_rows = []
                            for phase_name, forces in phases.items():
                                cap_rows.append({
                                    'Fase': phase_name,
                                    'Nx (kN/m)': forces.get('Nx'),
                                    'Q (kN/m)': forces.get('Q'),
                                    'M (kNm/m)': forces.get('M')
                                })
                            if cap_rows:
                                st.table(cap_rows)
        else:
            progress_bar.progress(0)
            st.error(f"❌ Feil: {result.get('error', 'Ukjent feil')}")
            
    except requests.exceptions.Timeout:
        st.error("⏱️ Tidsavbrudd: Beregningen tok for lang tid")
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Nettverksfeil: {str(e)}")


def show_project_setup():
    """Show project setup page"""
    st.subheader("🛠️ Prosjektsetup")
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
                
                success, result = create_project(project_name, project_description, allowed_users)
                
                if success:
                    st.success(f"✅ Prosjekt '{project_name}' opprettet!")
                    log_activity('project', f'Opprettet: {project_name}')
                    st.rerun()
                else:
                    st.error(f"Feil: {result.get('error', 'Ukjent feil')}")
    
    # List existing projects
    st.markdown("---")
    st.markdown("### Dine prosjekter")
    
    projects = get_user_projects()
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
    """Show home page"""
    # Greeting
    st.markdown(f'<div class="greeting">Hei, {USERNAME}! 👋</div>', unsafe_allow_html=True)
    
    # Status
    st.markdown("""
    <div class="status-box">
        <div class="status-text">🚀 Klar til videre utvikling</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Two columns: Projects and Recent Activity
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📁 Dine prosjekter")
        
        projects = get_user_projects()
        if projects:
            for project in projects:
                # Make project clickable
                if st.button(
                    f"📁 {project['name']}",
                    key=f"project_{project['id']}",
                    use_container_width=True,
                    help=project.get('description') or 'Klikk for å åpne prosjektet'
                ):
                    st.session_state.selected_project = project
                    st.session_state.current_page = 'project_view'
                    log_activity('project', f"Åpnet: {project['name']}")
                    st.rerun()
                st.caption(project.get('description') or 'Ingen beskrivelse')
        else:
            st.info("Ingen prosjekter ennå. Gå til 'Prosjektsetup' for å opprette et nytt prosjekt.")
    
    with col2:
        st.subheader("🕐 Siste aktivitet")
        
        activities = get_recent_activity()
        if activities:
            for activity in activities:
                timestamp = activity.get('timestamp', '')[:10] if activity.get('timestamp') else ''
                st.markdown(f"""
                <div class="activity-item">
                    <strong>{activity.get('activity_name', '')}</strong><br>
                    <small>{activity.get('activity_type', '')} • {timestamp}</small>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.caption("Ingen aktivitet registrert ennå")


def main():
    """Main application"""
    
    # Header
    st.markdown('<div class="main-header">RamGAP</div>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("Navigasjon")
        
        # Navigation buttons - uten logging for hastighet
        if st.button("🏠 Hjem", use_container_width=True):
            st.session_state.current_page = 'home'
            st.rerun()
        
        if st.button("🛠️ Prosjektsetup", use_container_width=True):
            st.session_state.current_page = 'project_setup'
            st.rerun()
        
        st.divider()
        
        # User info
        st.subheader("👤 Bruker")
        st.write(f"Innlogget som: **{USERNAME}**")
        
        # Backend status - bruker cached versjon
        st.divider()
        st.subheader("System Status")
        backend_healthy = check_backend_health()
        if backend_healthy:
            st.success("✅ Backend tilkoblet")
        else:
            st.warning("⚠️ Backend ikke tilgjengelig")
            st.caption("Start backend med: python backend/app.py")
    
    # Main content based on current page
    if st.session_state.current_page == 'project_setup':
        show_project_setup()
    elif st.session_state.current_page == 'project_view':
        show_project_view()
    elif st.session_state.current_page == 'plaxis_automation':
        show_plaxis_automation()
    else:
        show_home()
    
    # Footer
    st.divider()
    st.caption("RamGAP - Utviklingsversjon")


if __name__ == "__main__":
    main()
