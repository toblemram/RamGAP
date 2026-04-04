# -*- coding: utf-8 -*-
"""
Home Page — Prosjektoversikt
==============================
Project list and project detail view with 4 tabs:
  Oversikt  – Map (2D/3D) with boreholes from SND files + NADAG
  Data      – Borehole data tables and sounding diagrams
  Aktiviteter – Project activities and launch tools
  Logg      – Activity log
"""

import threading
import streamlit as st
from streamlit_folium import st_folium
from components.auth import require_username
from components.api_client import APIClient
from components.project_map import (
    load_snd_project,
    query_nadag_for_project,
    build_project_map,
    build_sounding_figure,
    build_3d_figure,
    build_terrain_grid,
    scan_project_folder,
    get_graph_data,
)

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


@st.cache_data(ttl=30)
def _cached_geotolk_sessions(project_id: int, limit: int = 10) -> list:
    return api.get_geotolk_project_sessions(project_id, limit)


@st.cache_data(ttl=30)
def _cached_modeling_activities(project_id: int) -> list:
    return api.get_modeling_activities(project_id)


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


def _rerun_saved_calculation(calc_type: str, config: dict):
    """Load a saved calculation's config into session state and navigate to Plaxis Level 3."""
    st.session_state.plaxis_selected_function = calc_type
    st.session_state.plaxis_level = 3
    st.session_state.plaxis_connected = True  # assume still connected

    if calc_type == "parametric_spunt":
        st.session_state.para_ks_soil = config.get("ks_soil")
        st.session_state.para_spunt_plate = config.get("plate")
        st.session_state.para_soil_params = {
            "su_values": config.get("su_values", ""),
            "gamma_values": config.get("gamma_values", ""),
        }
        st.session_state.para_spunt_range = config.get("spunt_range", {})
        st.session_state.para_phases_config = config.get("phases", {})
        st.session_state.para_results = None
        st.session_state.pop("para_saved_id", None)

    elif calc_type == "water_sensitivity":
        st.session_state.ws_water_values = config.get("water_values", "")
        st.session_state.ws_plate = config.get("plate")
        st.session_state.ws_phases_config = config.get("phases", {})
        st.session_state.ws_results = None
        st.session_state.pop("ws_saved_id", None)

    _cached_calculations.clear()
    st.switch_page("pages/plaxis.py")


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
# Auto-load project geo data (SND files + NADAG)
# ---------------------------------------------------------------------------

def _ensure_project_geo_loaded(project: dict) -> None:
    """Load SND boreholes from project folder and query NADAG on first open."""
    pid = project["id"]
    cache_key = f"_geo_loaded_{pid}"

    if st.session_state.get(cache_key):
        return  # Already loaded

    folder = project.get("folder_path")
    if not folder:
        st.session_state[cache_key] = True
        return

    # Load SND project from folder
    snd_key = f"_snd_project_{pid}"
    nadag_key = f"_nadag_df_{pid}"

    if snd_key not in st.session_state:
        with st.spinner("Laster borehull fra prosjektmappe…"):
            snd_data = load_snd_project(folder)
            st.session_state[snd_key] = snd_data

            # Query NADAG for the project area
            if snd_data and snd_data.get("boreholes"):
                nadag_df = query_nadag_for_project(snd_data["boreholes"])
                st.session_state[nadag_key] = nadag_df
            else:
                st.session_state[nadag_key] = None

    st.session_state[cache_key] = True


# ---------------------------------------------------------------------------
# Tab: Oversikt (Map 2D/3D)
# ---------------------------------------------------------------------------

def _tab_oversikt(project: dict):
    pid = project["id"]
    snd_data = st.session_state.get(f"_snd_project_{pid}")
    nadag_df = st.session_state.get(f"_nadag_df_{pid}")

    if not snd_data or not snd_data.get("boreholes"):
        folder = project.get("folder_path")
        if not folder:
            st.info("Ingen prosjektmappe er satt. Gå til **Prosjektinnstillinger** for å legge til en mappe med SND-filer.")
        else:
            st.warning(f"Fant ingen SND-filer i prosjektmappen: `{folder}`")
            if snd_data and snd_data.get("errors"):
                with st.expander("⚠️ Feil ved lasting"):
                    for err in snd_data["errors"]:
                        st.caption(f"• {err}")
        return

    boreholes = snd_data["boreholes"]
    polygon = snd_data.get("polygon")
    project_name = snd_data.get("project_name", project["name"])
    errors = snd_data.get("errors", [])

    # Summary
    col_s1, col_s2, col_s3 = st.columns(3)
    col_s1.metric("Borehull", len(boreholes))
    nadag_count = len(nadag_df) if nadag_df is not None and not nadag_df.empty else 0
    col_s2.metric("NADAG (NGU)", nadag_count)
    col_s3.metric("CRS", f"EPSG:{snd_data.get('epsg', '?')}")

    if errors:
        with st.expander(f"⚠️ {len(errors)} feil ved lasting", expanded=False):
            for err in errors:
                st.caption(f"• {err}")

    # 2D / 3D toggle
    view_mode = st.radio("Visning", ["2D Kart", "3D Modell"], horizontal=True, key=f"view_mode_{pid}")

    if view_mode == "2D Kart":
        m = build_project_map(boreholes, nadag_df, polygon, project_name)
        map_data = st_folium(m, height=550, use_container_width=True, key=f"map_{pid}")

        # Handle click on borehole marker
        clicked_popup = None
        if map_data and map_data.get("last_object_clicked_popup"):
            clicked_popup = map_data["last_object_clicked_popup"]

        if clicked_popup and "<b" in str(clicked_popup):
            # Extract point_id from popup HTML
            import re
            match = re.search(r'<b[^>]*>([^<]+)</b>', str(clicked_popup))
            if match:
                clicked_id = match.group(1).strip()
                # Find matching borehole
                for bh in boreholes:
                    if bh["point_id"] == clicked_id:
                        st.markdown(f"### 📊 {clicked_id}")
                        fig = build_sounding_figure(bh, project_name)
                        st.plotly_chart(fig, use_container_width=True)
                        break

    else:  # 3D Modell
        terrain_key = f"_terrain_{pid}"
        folder = project.get("folder_path", "")

        # Load / generate terrain (cached to disk)
        if terrain_key not in st.session_state:
            with st.spinner("Henter terrengdata fra Kartverket (lagres for neste gang)…"):
                st.session_state[terrain_key] = build_terrain_grid(boreholes, folder)

        terrain_grid = st.session_state[terrain_key]
        fig_3d = build_3d_figure(boreholes, nadag_df, project_name, terrain_grid)
        st.plotly_chart(fig_3d, use_container_width=True)


# ---------------------------------------------------------------------------
# Tab: Data (borehole table + sounding diagrams)
# ---------------------------------------------------------------------------

def _tab_data(project: dict):
    pid = project["id"]
    folder = project.get("folder_path", "")
    snd_data = st.session_state.get(f"_snd_project_{pid}")

    # --- Project folder overview ---
    st.markdown("### 📂 Prosjektmappe")
    if not folder:
        st.info("Ingen prosjektmappe er satt.")
    else:
        scan = scan_project_folder(folder)
        if not scan.get("exists"):
            st.warning(f"Mappen finnes ikke: `{folder}`")
        else:
            import pandas as pd
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                st.metric("Totalt filer", scan.get("total_files", 0))
            with col_f2:
                st.metric("Undermapper", len(scan.get("subfolders", [])))

            # Subfolders
            subfolders = scan.get("subfolders", [])
            if subfolders:
                st.markdown("**Undermapper:**")
                for sf in subfolders:
                    st.caption(f"📁 {sf['name']}  ({sf['count']} elementer)")

            # File types
            file_groups = scan.get("file_groups", {})
            if file_groups:
                st.markdown("**Filtyper:**")
                rows = []
                for ext, files in sorted(file_groups.items()):
                    rows.append({"Type": ext, "Antall": len(files), "Eksempler": ", ".join(files[:3]) + ("…" if len(files) > 3 else "")})
                st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    st.markdown("---")

    # --- Borehole data ---
    if not snd_data or not snd_data.get("boreholes"):
        st.info("Ingen SND-borehulldata funnet i prosjektmappen.")
        return

    boreholes = snd_data["boreholes"]
    project_name = snd_data.get("project_name", project["name"])

    st.markdown("### 📋 Borehull")

    import pandas as pd
    df = pd.DataFrame([
        {
            "Punkt-ID": bh["point_id"],
            "Metode": bh.get("method_name", "Ukjent"),
            "Dybde (m)": round(bh["max_depth"], 1),
            "Terrengkvote (m)": round(bh["elevation"], 1),
            "Dato": bh.get("date", "–"),
        }
        for bh in boreholes
    ])
    st.dataframe(df, use_container_width=True, hide_index=True)

    # Sounding diagrams
    st.markdown("### 📊 Sonderingsdiagram")
    selected_ids = st.multiselect(
        "Velg borehull",
        [bh["point_id"] for bh in boreholes],
        default=[boreholes[0]["point_id"]] if boreholes else [],
        key=f"sel_bh_{pid}",
    )

    cols = st.columns(min(len(selected_ids), 3)) if selected_ids else []
    for i, pid_sel in enumerate(selected_ids):
        bh = next((b for b in boreholes if b["point_id"] == pid_sel), None)
        if bh:
            with cols[i % len(cols)]:
                fig = build_sounding_figure(bh, project_name)
                st.plotly_chart(fig, use_container_width=True)

    # NADAG data
    nadag_df = st.session_state.get(f"_nadag_df_{pid}")
    if nadag_df is not None and not nadag_df.empty:
        st.markdown("### 🌍 NADAG-data (NGU)")
        display_cols = [c for c in ["borenr", "geotekniskmetodetekst", "boretlengde", "hoeyde", "_lat", "_lon"]
                        if c in nadag_df.columns]
        st.dataframe(nadag_df[display_cols] if display_cols else nadag_df, use_container_width=True, hide_index=True)


# ---------------------------------------------------------------------------
# Tab: Aktiviteter (launch tools + calculations)
# ---------------------------------------------------------------------------

def _tab_aktiviteter(project: dict):
    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("### 📋 Beregninger")

        # --- Plaxis calculations ---
        calculations = _cached_calculations(project['id'], 10)

        if calculations:
            import pandas as pd
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

                # Detect new-style calculations (parametric / water_sensitivity)
                res_data = calc.get('results') or {}
                calc_type = res_data.get('calc_type')  # set by new save endpoint
                config    = res_data.get('config', {})
                rows      = res_data.get('rows', [])

                type_labels = {
                    'parametric_spunt': '🔧 Parametrisk spunt',
                    'water_sensitivity': '💧 Vannstandssensitivitet',
                    'extract_results': '📊 Resultatuttak',
                }
                type_label = type_labels.get(calc_type, '')
                header = f"{status_icon} {activity_name}"
                if type_label:
                    header += f" — {type_label}"
                header += f" ({timestamp})"

                with st.expander(header):
                    st.caption(f"ID: {calc.get('id')} | Status: {status_text}")

                    if calc_type and rows:
                        # New-style: show results table
                        df = pd.DataFrame(rows)
                        st.dataframe(df, hide_index=True, use_container_width=True)

                        # Summary line
                        if calc_type == 'parametric_spunt':
                            ks = config.get('ks_soil', '?')
                            plate = config.get('plate', '?')
                            su_vals = config.get('su_values', '')
                            st.caption(f"KS-lag: {ks} | Spunt: {plate} | Su: {su_vals}")
                        elif calc_type == 'water_sensitivity':
                            wv = config.get('water_values', '')
                            plate = config.get('plate', '?')
                            st.caption(f"Spunt: {plate} | Vannstander: {wv}")

                        # Rerun button
                        if st.button("🔄 Kjør på nytt", key=f"rerun_home_{calc.get('id')}"):
                            _rerun_saved_calculation(calc_type, config)

                    else:
                        # Old-style: show structures / MSF
                        structures = calc.get('structures', {})
                        spunts = structures.get('spunts', [])
                        anchors = structures.get('anchors', [])
                        if spunts or anchors:
                            st.markdown("**Strukturer:**")
                            if spunts:
                                st.write(f"• Spunter: {', '.join(spunts)}")
                            if anchors:
                                st.write(f"• Ankere: {', '.join(anchors)}")

                        if status == 'completed' and res_data.get('msf'):
                            st.markdown("**Resultater:**")
                            for phase, value in res_data['msf'].items():
                                st.write(f"• MSF {phase}: {value:.2f}" if value else f"• MSF {phase}: -")

                    if status == 'failed':
                        st.error(f"Feil: {calc.get('error_message', 'Ukjent feil')}")

        # --- GeoTolk sessions ---
        geotolk_sessions = _cached_geotolk_sessions(project['id'], 10)
        if geotolk_sessions:
            for gs in geotolk_sessions:
                gs_status = gs.get('status', 'active')
                gs_icon = '✅' if gs_status == 'completed' else '🔄'
                gs_name = gs.get('activity_name', 'GeoTolk')
                gs_ts   = (gs.get('created_at') or '')[:10]
                gs_done = gs.get('completed_files', 0)
                gs_total = gs.get('total_files', 0)
                gs_user = gs.get('username', '')

                interp_files = gs.get('interpreted_files', [])
                file_names = ', '.join(f['filename'] for f in interp_files[:5])
                if len(interp_files) > 5:
                    file_names += f' +{len(interp_files) - 5}'

                header = f"{gs_icon} 🗺️ {gs_name} — {gs_done}/{gs_total} filer ({gs_ts})"
                with st.expander(header):
                    st.caption(f"ID: {gs.get('id')} | Bruker: {gs_user} | Status: {gs_status}")
                    if interp_files:
                        st.markdown("**Tolkede filer:**")
                        for fi in interp_files:
                            st.caption(f"• {fi['filename']} — {fi.get('num_layers', '?')} lag")

                    if st.button("🗺️ Gjenåpne tolkning", key=f"resume_gt_{gs['id']}",
                                 use_container_width=True):
                        st.session_state.geotolk_resume_session_id = gs['id']
                        _cached_geotolk_sessions.clear()
                        st.switch_page("pages/geotolk.py")

        # --- Modeling activities ---
        modeling_activities = _cached_modeling_activities(project['id'])
        if modeling_activities:
            for ma in modeling_activities:
                ma_status = ma.get('status', 'unknown')
                ma_icon = '✅' if ma.get('has_results') else '🔄'
                ma_name = ma.get('name', 'Modellering')
                ma_ts = (ma.get('created_at') or '')[:10]
                has_params = ma.get('has_tormur_params', False)
                has_res = ma.get('has_results', False)

                info_parts = []
                if has_params:
                    info_parts.append('parametre satt')
                if has_res:
                    info_parts.append('resultater')
                info_str = ', '.join(info_parts) if info_parts else 'ny'

                header = f"{ma_icon} 🏗️ {ma_name} — {info_str} ({ma_ts})"
                with st.expander(header):
                    st.caption(f"ID: {ma.get('id')} | Status: {ma_status}")

                    if has_res:
                        results = api.get_modeling_results(ma['id'])
                        report = results.get('run_report', {})
                        n_sections = len(report.get('Sections', []))
                        all_ok = report.get('Config', {}).get('AllOk', False)
                        vol = report.get('Config', {}).get('TotalVolume_m3')
                        ok_icon = '✅' if all_ok else '⚠️'
                        st.markdown(f"**{ok_icon} {n_sections} seksjoner** | "
                                    f"Volum: {vol:.1f} m³" if vol else
                                    f"**{ok_icon} {n_sections} seksjoner**")

                    if st.button("🏗️ Åpne modellering", key=f"open_mod_{ma['id']}",
                                 use_container_width=True):
                        st.session_state.modeling_activity_id = ma['id']
                        _cached_modeling_activities.clear()
                        st.switch_page("pages/modellering.py")

        if not calculations and not geotolk_sessions and not modeling_activities:
            st.info("Ingen beregninger ennå. Start en ny aktivitet til høyre!")

    with col2:
        st.markdown("### 🚀 Start ny aktivitet")

        if st.button("🔧 Plaxis automatisering", use_container_width=True, key="btn_plaxis"):
            _log_project(project['id'], 'Plaxis', 'Plaxis automatisering startet')
            st.switch_page("pages/plaxis.py")

        if st.button("🗺️ GeoTolk", use_container_width=True, key="btn_geotolk"):
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


# ---------------------------------------------------------------------------
# Tab: Logg (activity log + project info)
# ---------------------------------------------------------------------------

def _tab_logg(project: dict):
    st.markdown("### 📋 Siste aktiviteter")
    recent_activities = _cached_project_activities(project['id'], 20)
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
        folder = project.get('folder_path')
        if folder:
            st.write(f"**Prosjektmappe:** {folder}")
        allowed = project.get('allowed_users', [])
        if allowed:
            st.write(f"**Brukere med tilgang:** {', '.join(allowed)}")


# ---------------------------------------------------------------------------
# Project detail view — 4 tabs
# ---------------------------------------------------------------------------

def show_project_view():
    """Show project detail view with tabs."""
    project = st.session_state.selected_project
    if not project:
        st.rerun()
        return

    # Auto-load geo data
    _ensure_project_geo_loaded(project)

    if st.button("← Tilbake til oversikt"):
        st.session_state.selected_project = None
        st.rerun()

    st.subheader(f"📁 {project['name']}")
    st.caption(project.get('description') or 'Ingen beskrivelse')

    tab_oversikt, tab_data, tab_aktiviteter, tab_logg = st.tabs(
        ["🗺️ Oversikt", "📊 Data", "🚀 Aktiviteter", "📋 Logg"]
    )

    with tab_oversikt:
        _tab_oversikt(project)

    with tab_data:
        _tab_data(project)

    with tab_aktiviteter:
        _tab_aktiviteter(project)

    with tab_logg:
        _tab_logg(project)


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
