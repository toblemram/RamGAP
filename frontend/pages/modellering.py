# -*- coding: utf-8 -*-
"""
Modellering — Grasshopper-optimalisering
=========================================
Side for modeling-aktiviteter koblet til Grasshopper-plugin.
Støtter: oppretting av aktivitet, Excel-opplasting, visning av
optimeringsresultater (run-report.json) og nedlasting av Excel/IFC.
"""

import json
import os
import sys

import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st

_HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from components.api_client import APIClient
from components.sidebar import render_sidebar

st.set_page_config(
    page_title='RamGAP',
    page_icon='🏗️',
    layout='wide',
    initial_sidebar_state='expanded',
)

# Hide Streamlit's auto-generated pages navigation
st.markdown("""
<style>
    [data-testid="stSidebarNav"] { display: none !important; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

BACKEND_URL = os.getenv('BACKEND_URL', 'http://localhost:5050')


def _username() -> str:
    return os.environ.get('USERNAME', os.environ.get('USER', 'User'))


def _api() -> APIClient:
    return APIClient()


def _project() -> dict | None:
    return st.session_state.get('selected_project')


def _go_home():
    st.switch_page('app.py')


# ---------------------------------------------------------------------------
# Visualization helpers
# ---------------------------------------------------------------------------

def _build_summary_cards(report: dict):
    sections = report.get('Sections', [])
    n_total  = len(sections)
    n_failed = sum(1 for s in sections if not s.get('Checks', {}).get('AllOk', True))
    factors  = [s['Checks'] for s in sections]
    min_slide = min((f.get('SlidingFactor', 0) for f in factors), default=0)
    min_overt = min((f.get('OverturningFactor', 0) for f in factors), default=0)
    min_bear  = min((f.get('BearingFactor', 0) for f in factors), default=0)
    total_len = report.get('TotalLength', n_total)

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric('Seksjoner totalt', n_total)
    c2.metric('Totallengde', f'{total_len:.1f} m')
    c3.metric('Min glidning', f'{min_slide:.2f}',
              delta=f'Min {report.get("Config", {}).get("SlidingMin", 1.5)}',
              delta_color='normal')
    c4.metric('Min velting', f'{min_overt:.2f}',
              delta=f'Min {report.get("Config", {}).get("OverturningMin", 2.0)}',
              delta_color='normal')
    c5.metric('Feilede seks.', n_failed,
              delta_color='inverse')


def _build_charts(report: dict):
    sections = report.get('Sections', [])
    if not sections:
        st.info('Ingen seksjoner i rapporten.')
        return

    df = pd.DataFrame([{
        'Stasjon':       s.get('Station', 0),
        'Høyde':         s.get('Height', 0),
        'Topp-bredde':   s.get('SmoothedTopWidth', s.get('TopWidth', 0)),
        'Bunn-bredde':   s.get('SmoothedBottomWidth', s.get('BottomWidth', 0)),
        'Vinkel (°)':    s.get('SmoothedFaceAngleDeg', s.get('FaceAngleDeg', 0)),
        'Glidning SF':   s.get('Checks', {}).get('SlidingFactor', 0),
        'Velting SF':    s.get('Checks', {}).get('OverturningFactor', 0),
        'Bæreevne SF':   s.get('Checks', {}).get('BearingFactor', 0),
        'Godkjent':      s.get('Checks', {}).get('AllOk', False),
    } for s in sections])

    tab1, tab2, tab3, tab4 = st.tabs(
        ['📐 Geometri', '🔒 Sikkerhetsfaktorer', '📊 Tverrsnitt', '📋 Tabell']
    )

    with tab1:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df['Stasjon'], y=df['Høyde'], mode='lines+markers',
            name='Høyde', line=dict(color='steelblue', width=2),
        ))
        fig.update_layout(
            title='Høyde langs vegg', xaxis_title='Stasjon (m)',
            yaxis_title='Høyde (m)', height=350,
        )
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        cfg   = report.get('Config', {})
        s_min = cfg.get('SlidingMin', 1.5)
        o_min = cfg.get('OverturningMin', 2.0)
        b_min = cfg.get('BearingMin', 3.0)

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df['Stasjon'], y=df['Glidning SF'],
                                  mode='lines', name='Glidning SF',
                                  line=dict(color='blue')))
        fig.add_trace(go.Scatter(x=df['Stasjon'], y=df['Velting SF'],
                                  mode='lines', name='Velting SF',
                                  line=dict(color='green')))
        fig.add_trace(go.Scatter(x=df['Stasjon'], y=df['Bæreevne SF'],
                                  mode='lines', name='Bæreevne SF',
                                  line=dict(color='orange')))
        # Min-linjer
        for val, name, color in [
            (s_min, f'Min glidning ({s_min})', 'blue'),
            (o_min, f'Min velting ({o_min})', 'green'),
            (b_min, f'Min bæreevne ({b_min})', 'orange'),
        ]:
            fig.add_hline(y=val, line_dash='dash', line_color=color,
                          annotation_text=name, annotation_position='right')
        fig.update_layout(
            title='Sikkerhetsfaktorer langs vegg',
            xaxis_title='Stasjon (m)', yaxis_title='SF (−)',
            height=400,
        )
        st.plotly_chart(fig, use_container_width=True)

    with tab3:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df['Stasjon'], y=df['Topp-bredde'],
                                  mode='lines', name='Topp-bredde',
                                  line=dict(color='teal')))
        fig.add_trace(go.Scatter(x=df['Stasjon'], y=df['Bunn-bredde'],
                                  mode='lines', name='Bunn-bredde',
                                  line=dict(color='coral')))
        fig.update_layout(
            title='Tverrsnittsdimensjoner langs vegg',
            xaxis_title='Stasjon (m)', yaxis_title='Bredde (m)',
            height=350,
        )
        st.plotly_chart(fig, use_container_width=True)

    with tab4:
        display = df[['Stasjon', 'Høyde', 'Topp-bredde', 'Bunn-bredde',
                       'Vinkel (°)', 'Glidning SF', 'Velting SF',
                       'Bæreevne SF', 'Godkjent']].copy()
        display['Status'] = display['Godkjent'].map(
            {True: '✅', False: '❌'})
        st.dataframe(
            display.drop(columns='Godkjent').style.applymap(
                lambda v: 'color: red' if v == '❌' else 'color: green',
                subset=['Status'],
            ),
            use_container_width=True,
            hide_index=True,
        )


# ---------------------------------------------------------------------------
# Main page
# ---------------------------------------------------------------------------

def main():
    st.title('🏗️ Modellering')
    render_sidebar()
    st.markdown('---')

    project = _project()
    if not project:
        st.warning('Velg et prosjekt fra forsiden først.')
        if st.button('← Til forsiden'):
            _go_home()
        return

    st.markdown(f'**Prosjekt:** {project["name"]}')
    st.markdown('---')

    api      = _api()
    username = _username()

    # -----------------------------------------------------------------------
    # Initialiser session state
    # -----------------------------------------------------------------------
    if 'modeling_activity_id' not in st.session_state:
        st.session_state.modeling_activity_id = None

    # -----------------------------------------------------------------------
    # Layout: aktivitetsliste (venstre) + detalj (høyre)
    # -----------------------------------------------------------------------
    col_list, col_detail = st.columns([1, 2])

    with col_list:
        st.subheader('Aktiviteter')

        # Opprett ny
        with st.expander('➕ Ny aktivitet', expanded=False):
            new_name = st.text_input('Navn på aktivitet', key='new_activity_name')
            if st.button('Opprett', key='btn_create_activity'):
                if not new_name.strip():
                    st.warning('Skriv inn et navn.')
                else:
                    result = api.create_modeling_activity(
                        project['id'], new_name.strip(), username
                    )
                    if 'activity' in result:
                        st.session_state.modeling_activity_id = result['activity']['id']
                        api.log_project_activity(
                            project['id'], username,
                            'Modellering', f'Aktivitet opprettet: {new_name.strip()}'
                        )
                        st.success(f'Aktivitet "{new_name}" opprettet.')
                        st.rerun()
                    else:
                        st.error(result.get('error', 'Ukjent feil'))

        # Liste
        activities = api.get_modeling_activities(project['id'])
        if not activities:
            st.info('Ingen aktiviteter ennå.')
        for act in activities:
            label  = act['name']
            badges = ''
            if act.get('has_excel'):
                badges += ' 📊'
            if act.get('has_results'):
                badges += ' ✅'
            selected = st.session_state.modeling_activity_id == act['id']
            if st.button(
                f'{"▶ " if selected else ""}{label}{badges}',
                key=f'act_{act["id"]}',
                use_container_width=True,
            ):
                st.session_state.modeling_activity_id = act['id']
                st.rerun()

    with col_detail:
        act_id = st.session_state.modeling_activity_id
        if not act_id:
            st.info('Velg eller opprett en aktivitet til venstre.')
            st.stop()

        # Hent aktivitet
        activities = api.get_modeling_activities(project['id'])
        act = next((a for a in activities if a['id'] == act_id), None)
        if not act:
            st.warning('Aktiviteten ble ikke funnet.')
            st.stop()

        st.subheader(f'📁 {act["name"]}')

        status_map = {
            'active':      '🟡 Ingen filer',
            'has_excel':   '🟠 Excel lastet opp — venter på GH-resultater',
            'has_results': '🟢 Resultater tilgjengelig',
        }
        st.caption(status_map.get(act.get('status', ''), act.get('status', '')))

        # --- Excel-opplasting ---
        st.markdown('#### 📊 Excel-inputfil')
        if act.get('has_excel'):
            st.success(f'Fil lastet opp: `{act["excel_filename"]}`')
            dl = api.get_modeling_download_url(act_id, 'excel')
            if 'url' in dl:
                st.link_button('⬇ Last ned Excel', dl['url'])
        else:
            uploaded = st.file_uploader(
                'Last opp Excel-fil (.xlsx)',
                type=['xlsx', 'xls'],
                key=f'excel_upload_{act_id}',
            )
            if uploaded is not None:
                with st.spinner('Laster opp...'):
                    result = api.upload_modeling_excel(
                        act_id, uploaded.read(), uploaded.name
                    )
                if 'error' not in result:
                    st.success('Excel lastet opp!')
                    st.rerun()
                else:
                    st.error(result['error'])

        st.markdown('---')

        # --- Resultater ---
        st.markdown('#### 📈 GH-optimeringsresultater')

        if act.get('has_results'):
            results = api.get_modeling_results(act_id)
            if 'error' not in results:
                report  = results.get('run_report', {})
                summary = results.get('run_summary', '')

                # Sammendrag
                if summary:
                    with st.expander('📄 Kjøringssammendrag', expanded=True):
                        st.markdown(summary)

                # Nøkkeltall
                _build_summary_cards(report)
                st.markdown('---')

                # Grafer
                _build_charts(report)

                # IFC-nedlasting
                if act.get('has_ifc'):
                    st.markdown('---')
                    dl_ifc = api.get_modeling_download_url(act_id, 'ifc')
                    if 'url' in dl_ifc:
                        st.link_button('⬇ Last ned IFC-fil', dl_ifc['url'])
            else:
                st.error(f'Kunne ikke hente resultater: {results["error"]}')
        else:
            st.info(
                'Ingen resultater ennå.\n\n'
                'Send run-report.json og IFC-filen fra Grasshopper-plugin til:\n\n'
                f'`POST /api/modeling/activities/{act_id}/upload/results`'
            )

        # --- Slett aktivitet ---
        st.markdown('---')
        with st.expander('🗑 Slett aktivitet'):
            st.warning('Dette sletter aktiviteten og kan ikke angres.')
            if st.button('Slett', key=f'del_{act_id}', type='primary'):
                api.delete_modeling_activity(act_id)
                st.session_state.modeling_activity_id = None
                st.success('Aktivitet slettet.')
                st.rerun()

    # Tilbake-knapp
    st.markdown('---')
    if st.button('← Tilbake til prosjekt'):
        _go_home()


main()
