# -*- coding: utf-8 -*-
"""
Modellering — Grasshopper-optimalisering & Tørmur V220
=======================================================
Side for modeling-aktiviteter. Støtter:
  - Tørmur: parameterinnfylling → optimalisering → rapport → 3D-viewer
  - Generell GH-optimalisering: Excel-opplasting, visning av resultater, IFC
"""

import json
import os

import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st
import streamlit.components.v1 as st_components
from components.auth import require_username
from components.api_client import APIClient

USERNAME = require_username()
api = APIClient()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _project() -> dict | None:
    return st.session_state.get('selected_project')


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
# Tørmur V220 input schema (mirrors sandbox/tørmur/app.py INPUT_SECTIONS)
# ---------------------------------------------------------------------------

TORMUR_INPUT_SECTIONS = [
    {
        "title": "🏗️ Laster",
        "fields": [
            {"key": "qk", "label": "Nyttelast bak mur, qk", "unit": "kPa", "default": 5.0},
            {"key": "qQk", "label": "Boggilast bak mur, qQk", "unit": "kPa", "default": 16.8},
            {"key": "gammaQ_nyttelast", "label": "Lastfaktor, γQ nyttelast", "unit": "", "default": 1.3},
            {"key": "gammaQ_boggilast", "label": "Lastfaktor, γQ boggilast", "unit": "", "default": 1.15},
            {"key": "inv_tan_beta", "label": "Helning bak mur, 1/tan β", "unit": "", "default": 1.80},
            {"key": "PH", "label": "Horisontallast topp, PH", "unit": "kN/m", "default": 2.0},
            {"key": "PV", "label": "Vertikallast topp, PV", "unit": "kN/m", "default": 0.0},
            {"key": "yp", "label": "Høyde over mur for PH", "unit": "m", "default": 0.0},
            {"key": "xp", "label": "Avstand fra front for PV", "unit": "m", "default": 0.0},
            {"key": "gamma_mur", "label": "Tyngdetetthet mur, γmur", "unit": "kN/m³", "default": 23.0},
        ],
    },
    {
        "title": "🪨 Jordparametre",
        "fields": [
            {"key": "phi_bak", "label": "Friksjonsvinkel bak, φ", "unit": "°", "default": 42.0},
            {"key": "a_bak", "label": "Attraksjon bak, a", "unit": "kPa", "default": 0.0},
            {"key": "gamma_bak", "label": "Tyngdetetthet bak, γ'", "unit": "kN/m³", "default": 19.0},
            {"key": "phi_under", "label": "Friksjonsvinkel under/foran, φ", "unit": "°", "default": 37.0},
            {"key": "a_under", "label": "Attraksjon under/foran, a", "unit": "kPa", "default": 9.0},
            {"key": "gamma_under", "label": "Tyngdetetthet under, γ'", "unit": "kN/m³", "default": 9.0},
            {"key": "gamma_foran", "label": "Tyngdetetthet foran, γ'", "unit": "kN/m³", "default": 19.0},
        ],
    },
    {
        "title": "📐 Dimensjoner mur",
        "fields": [
            {"key": "H", "label": "Murhøyde, H", "unit": "m", "default": 4.0},
            {"key": "D", "label": "Fotdybde, D", "unit": "m", "default": 0.5},
            {"key": "bb", "label": "Bredde bunn, bb", "unit": "m", "default": 2.2},
            {"key": "bt", "label": "Bredde topp, bt", "unit": "m", "default": 2.2},
            {"key": "d_helning", "label": "Murens helning, d", "unit": "", "default": 5.0},
            {"key": "bx", "label": "Tillegg bredde bunn, bx", "unit": "m", "default": 0.0},
            {"key": "inv_tan_alpha", "label": "Terrenghelning foran, 1/tan α", "unit": "", "default": 0.0},
            {"key": "rv", "label": "Ruhet bak muren, rv", "unit": "", "default": 0.3},
            {"key": "stopt_saale", "label": "Støpt såle", "unit": "", "default": False, "kind": "bool"},
        ],
    },
    {
        "title": "⚙️ Beregning",
        "fields": [
            {"key": "gamma_m", "label": "Materialfaktor, γm", "unit": "", "default": 1.40},
            {"key": "inkluder_jordsug", "label": "Inkludere jordsug ved β>0", "unit": "", "default": False, "kind": "bool"},
        ],
    },
]


def _render_tormur_params(act_id: int) -> dict | None:
    """Render tørmur parameter form and return dict of values (or None if not submitted).

    bt and bb are greyed out (disabled) because they are determined by the
    optimiser via Grasshopper polylines.
    """
    # Load saved params
    if f'tormur_params_{act_id}' not in st.session_state:
        saved = api.get_tormur_params(act_id)
        st.session_state[f'tormur_params_{act_id}'] = saved.get('params', {})

    saved_params = st.session_state[f'tormur_params_{act_id}']
    params = {}

    DISABLED_KEYS = {'bt', 'bb'}

    for section in TORMUR_INPUT_SECTIONS:
        with st.expander(section["title"], expanded=True):
            cols = st.columns(2)
            for i, field in enumerate(section["fields"]):
                col = cols[i % 2]
                key = field["key"]
                default = saved_params.get(key, field["default"])
                label = f'{field["label"]} [{field["unit"]}]' if field["unit"] else field["label"]
                disabled = key in DISABLED_KEYS

                if field.get("kind") == "bool":
                    params[key] = col.checkbox(label, value=bool(default), key=f'tp_{act_id}_{key}',
                                               disabled=disabled)
                else:
                    params[key] = col.number_input(
                        label, value=float(default), format="%.3f",
                        key=f'tp_{act_id}_{key}',
                        disabled=disabled,
                    )
                    if disabled:
                        col.caption('Bestemmes av optimalisering')

    return params


def _render_tormur_check(params: dict):
    """Show live V220 check result for the current parameters."""
    res = api.tormur_check(params)

    col1, col2 = st.columns(2)
    f_ok = res.get('foundation_check', '?')
    b_ok = res.get('bearing_check', '?')

    col1.metric('Fundamentkontroll', f_ok,
                delta='OK' if f_ok == 'OK' else 'NEI',
                delta_color='normal' if f_ok == 'OK' else 'inverse')
    col2.metric('Bæreevnekontroll', b_ok,
                delta='OK' if b_ok == 'OK' else 'NEI',
                delta_color='normal' if b_ok == 'OK' else 'inverse')

    msgs = res.get('messages', {})
    for key in ('D46', 'I46'):
        msg = msgs.get(key, '')
        if msg:
            if 'NB' in msg or 'ikke' in msg.lower():
                st.warning(msg)
            else:
                st.success(msg)

    with st.expander('🔍 Detaljerte verdier', expanded=False):
        kv = res.get('key_values', {})
        detail_cols = st.columns(4)
        items = list(kv.items())
        for i, (k, v) in enumerate(items):
            c = detail_cols[i % 4]
            c.metric(k, f'{v:.3f}' if isinstance(v, float) else str(v))


# ---------------------------------------------------------------------------
# 3D Viewer (three.js — wall from section data)
# ---------------------------------------------------------------------------

_WALL_VIEWER_HTML = """
<!DOCTYPE html>
<html>
<head>
<style>body{margin:0;overflow:hidden}canvas{display:block}</style>
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
</head>
<body>
<script>
const sections = __SECTIONS__;
const scene = new THREE.Scene();
scene.background = new THREE.Color(0xf0f0f0);
const camera = new THREE.PerspectiveCamera(60, window.innerWidth/window.innerHeight, 0.1, 1000);
const renderer = new THREE.WebGLRenderer({antialias:true});
renderer.setSize(window.innerWidth, window.innerHeight);
document.body.appendChild(renderer.domElement);

// Lights
scene.add(new THREE.AmbientLight(0x404040, 2));
const dirLight = new THREE.DirectionalLight(0xffffff, 1);
dirLight.position.set(10, 20, 10);
scene.add(dirLight);

// Build wall geometry — symmetric trapezoid (both front and back inclined)
if (sections.length > 1) {
    const geom = new THREE.BufferGeometry();
    const vertices = [];
    const colors = [];
    const okColor = new THREE.Color(0x4CAF50);
    const failColor = new THREE.Color(0xf44336);

    for (let i = 0; i < sections.length - 1; i++) {
        const s0 = sections[i], s1 = sections[i+1];
        const z0 = s0.Station, z1 = s1.Station;
        const h0 = s0.Height, h1 = s1.Height;
        const bt0 = s0.SmoothedTopWidth || s0.TopWidth || 0.5;
        const bb0 = s0.SmoothedBottomWidth || s0.BottomWidth || 1.0;
        const bt1 = s1.SmoothedTopWidth || s1.TopWidth || 0.5;
        const bb1 = s1.SmoothedBottomWidth || s1.BottomWidth || 1.0;
        const c0 = (s0.Checks && s0.Checks.AllOk) ? okColor : failColor;
        const c1 = (s1.Checks && s1.Checks.AllOk) ? okColor : failColor;

        // Symmetric trapezoid: front and back both lean equally
        // half_diff = (bb - bt) / 2 = lean offset at bottom
        const hd0 = (bb0 - bt0) / 2, hd1 = (bb1 - bt1) / 2;

        // 4 corners per section (x = across wall, y = up, z = along wall)
        // Top: [0, h, z] to [bt, h, z]
        // Bottom (centered): [(bt-bb)/2, 0, z] to [(bt+bb)/2, 0, z]
        const bf0x = (bt0 - bb0) / 2;   // bottom-front x (negative when bb > bt)
        const bb0x = (bt0 + bb0) / 2;   // bottom-back x
        const bf1x = (bt1 - bb1) / 2;
        const bb1x = (bt1 + bb1) / 2;

        // Front face (P1-top → P4-bot, leaning)
        vertices.push(0,h0,z0, bf0x,0,z0, bf1x,0,z1);
        vertices.push(0,h0,z0, bf1x,0,z1, 0,h1,z1);
        // Back face (P2-top → P3-bot, leaning)
        vertices.push(bt0,h0,z0, bt1,h1,z1, bb1x,0,z1);
        vertices.push(bt0,h0,z0, bb1x,0,z1, bb0x,0,z0);
        // Top face
        vertices.push(0,h0,z0, bt0,h0,z0, bt1,h1,z1);
        vertices.push(0,h0,z0, bt1,h1,z1, 0,h1,z1);
        // Bottom face
        vertices.push(bf0x,0,z0, bf1x,0,z1, bb1x,0,z1);
        vertices.push(bf0x,0,z0, bb1x,0,z1, bb0x,0,z0);

        for (let t = 0; t < 24; t++) {
            const c = t < 12 ? c0 : c1;
            colors.push(c.r, c.g, c.b);
        }
    }

    geom.setAttribute('position', new THREE.Float32BufferAttribute(vertices, 3));
    geom.setAttribute('color', new THREE.Float32BufferAttribute(colors, 3));
    geom.computeVertexNormals();

    const mat = new THREE.MeshPhongMaterial({vertexColors: true, side: THREE.DoubleSide, flatShading: true});
    const mesh = new THREE.Mesh(geom, mat);
    scene.add(mesh);

    // Wireframe overlay
    const wire = new THREE.LineSegments(
        new THREE.WireframeGeometry(geom),
        new THREE.LineBasicMaterial({color: 0x333333, opacity: 0.15, transparent: true})
    );
    scene.add(wire);

    // Center camera
    const box = new THREE.Box3().setFromObject(mesh);
    const center = box.getCenter(new THREE.Vector3());
    const size = box.getSize(new THREE.Vector3());
    camera.position.set(center.x + size.x * 2, center.y + size.y * 1.5, center.z + size.z * 0.5);
    camera.lookAt(center);
}

// Ground grid
const grid = new THREE.GridHelper(50, 50, 0xcccccc, 0xeeeeee);
grid.rotation.x = Math.PI / 2;
scene.add(grid);

const controls = new THREE.OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;

function animate() { requestAnimationFrame(animate); controls.update(); renderer.render(scene, camera); }
animate();
window.addEventListener('resize', () => {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
});
</script>
</body>
</html>
"""


def _render_3d_viewer(report: dict):
    """Render an inline three.js viewer from section data."""
    sections = report.get('Sections', [])
    if not sections:
        st.info('Ingen seksjoner å vise.')
        return
    html = _WALL_VIEWER_HTML.replace('__SECTIONS__', json.dumps(sections))
    st_components.html(html, height=500, scrolling=False)


# ---------------------------------------------------------------------------
# Main page
# ---------------------------------------------------------------------------

def main():
    st.title('🏗️ Modellering')
    st.markdown('---')

    project = _project()
    if not project:
        st.warning('Velg et prosjekt fra forsiden først.')
        if st.button('← Til forsiden'):
            st.switch_page('pages/home.py')
        return

    st.markdown(f'**Prosjekt:** {project["name"]}')
    st.markdown('---')

    if 'modeling_activity_id' not in st.session_state:
        st.session_state.modeling_activity_id = None

    # -----------------------------------------------------------------------
    # Layout: aktivitetsliste (venstre) + detalj (høyre)
    # -----------------------------------------------------------------------
    col_list, col_detail = st.columns([1, 2])

    with col_list:
        st.subheader('Aktiviteter')

        # Opprett ny — choose model type
        with st.expander('➕ Ny aktivitet', expanded=False):
            model_type = st.selectbox(
                'Modelltype',
                ['🧱 Tørmur (V220)', '📊 Generell GH-optimalisering'],
                key='new_model_type',
            )
            new_name = st.text_input('Navn på aktivitet', key='new_activity_name')
            if st.button('Opprett', key='btn_create_activity'):
                if not new_name.strip():
                    st.warning('Skriv inn et navn.')
                else:
                    result = api.create_modeling_activity(
                        project['id'], new_name.strip(), USERNAME
                    )
                    if 'activity' in result:
                        act = result['activity']
                        st.session_state.modeling_activity_id = act['id']
                        # If tørmur, save default params immediately
                        if 'Tørmur' in model_type:
                            defaults = {}
                            for sec in TORMUR_INPUT_SECTIONS:
                                for f in sec['fields']:
                                    defaults[f['key']] = f['default']
                            api.save_tormur_params(act['id'], defaults)
                        api.log_project_activity(
                            project['id'], USERNAME,
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
            if act.get('has_tormur_params'):
                badges += ' 🧱'
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

        activities = api.get_modeling_activities(project['id'])
        act = next((a for a in activities if a['id'] == act_id), None)
        if not act:
            st.warning('Aktiviteten ble ikke funnet.')
            st.stop()

        st.subheader(f'📁 {act["name"]}')

        is_tormur = act.get('has_tormur_params', False)

        if is_tormur:
            _render_tormur_detail(act)
        else:
            _render_gh_detail(act)

        # --- Delete ---
        st.markdown('---')
        with st.expander('🗑 Slett aktivitet'):
            st.warning('Dette sletter aktiviteten og kan ikke angres.')
            if st.button('Slett', key=f'del_{act_id}', type='primary'):
                api.delete_modeling_activity(act_id)
                st.session_state.modeling_activity_id = None
                st.success('Aktivitet slettet.')
                st.rerun()

    st.markdown('---')
    if st.button('← Tilbake til prosjekt'):
        st.switch_page('pages/home.py')


# ---------------------------------------------------------------------------
# Section detail viewer
# ---------------------------------------------------------------------------

# Display labels for diagnostic keys
_DIAG_LABELS = {
    'EA': ('Jordtrykk EA', 'kN/m'),
    'T': ('Friksjon T', 'kN/m'),
    'Gvekt': ('Murvekt G', 'kN/m'),
    'RV': ('Resultant vertikal RV', 'kN/m'),
    'RH': ('Resultant horisontal RH', 'kN/m'),
    'e': ('Eksentrisitet e', 'm'),
    'qV': ('Fundamenttrykk qV', 'kPa'),
    'rb': ('Ruhet rb', ''),
    'rb_krav': ('Ruhet krav rb_krav', ''),
    'b0': ('Effektiv bredde b0', 'm'),
    'sigma_V': ('Bæreevne σ_V', 'kPa'),
    'Ng': ('Bæreevnefaktor Nγ', ''),
    'Nq': ('Bæreevnefaktor Nq', ''),
    'KA': ('Jordtrykkskoeffisient KA', ''),
    'KA_korr': ('Korrigert KA', ''),
    'K_delta': ('Korreksjonsfaktor Kδ', ''),
    'tan_rho_bak': ('tan ρ bak', ''),
    'tan_rho_under': ('tan ρ under', ''),
}


def _render_section_detail(sections: list):
    """Let user select a section and see its full V220 calculation."""
    options = [
        f'Seksjon {s.get("Index", i)} — st. {s.get("Station", 0):.1f} m  '
        f'(H={s.get("Height", 0):.2f} m)'
        for i, s in enumerate(sections)
    ]
    idx = st.selectbox('Velg seksjon', range(len(sections)),
                       format_func=lambda i: options[i],
                       key='section_detail_idx')
    sec = sections[idx]
    checks = sec.get('Checks', {})
    diag = sec.get('Diagnostics', {})

    # Header metrics
    c1, c2, c3, c4 = st.columns(4)
    c1.metric('Høyde', f'{sec.get("Height", 0):.2f} m')
    c2.metric('Topp-bredde bt', f'{sec.get("SmoothedTopWidth", 0):.3f} m')
    c3.metric('Bunn-bredde bb', f'{sec.get("SmoothedBottomWidth", 0):.3f} m')
    c4.metric('Volum/m', f'{sec.get("VolumePerMeter", 0):.3f} m³/m')

    # Safety factors
    st.markdown('#### Sikkerhetsfaktorer')
    sc1, sc2, sc3 = st.columns(3)
    sf_slide = checks.get('SlidingFactor', 0)
    sf_overt = checks.get('OverturningFactor', 0)
    sf_bear = checks.get('BearingFactor', 0)
    sc1.metric('Glidning', f'{sf_slide:.3f}',
               delta='OK' if checks.get('SlidingOk') else 'NEI',
               delta_color='normal' if checks.get('SlidingOk') else 'inverse')
    sc2.metric('Velting', f'{sf_overt:.3f}',
               delta='OK' if checks.get('OverturningOk') else 'NEI',
               delta_color='normal' if checks.get('OverturningOk') else 'inverse')
    sc3.metric('Bæreevne', f'{sf_bear:.3f}',
               delta='OK' if checks.get('BearingOk') else 'NEI',
               delta_color='normal' if checks.get('BearingOk') else 'inverse')

    governing = checks.get('GoverningCheck', '')
    all_ok = checks.get('AllOk', False)
    if all_ok:
        st.success(f'✅ Alle kontroller OK — styrende: **{governing}**')
    else:
        st.error(f'❌ Kontroll feilet — styrende: **{governing}**')

    # Messages
    for key in ('msg_D46', 'msg_I46'):
        msg = diag.get(key, '')
        if msg:
            if 'NB' in msg or 'ikke' in msg.lower():
                st.warning(msg)
            else:
                st.success(msg)

    # Full diagnostics table
    if diag:
        st.markdown('#### Beregningsdetaljer')
        rows = []
        for key, val in diag.items():
            if key.startswith('msg_') or key.endswith('_check'):
                continue
            label, unit = _DIAG_LABELS.get(key, (key, ''))
            if val is not None:
                fmt = f'{val:.4f}' if isinstance(val, (int, float)) else str(val)
                rows.append({'Parameter': label, 'Verdi': fmt, 'Enhet': unit})
        if rows:
            st.dataframe(pd.DataFrame(rows), use_container_width=True,
                         hide_index=True)
    else:
        st.info('Ingen detaljerte beregningsdata lagret for denne seksjonen. '
                'Kjør optimaliseringen på nytt for å få detaljerte resultater.')


# ---------------------------------------------------------------------------
# Tørmur detail panel
# ---------------------------------------------------------------------------

def _render_tormur_detail(act: dict):
    """Tørmur workflow: tabs for V220 params vs GH results / 3D."""
    act_id = act['id']

    has_results = act.get('has_results', False)
    tab_params, tab_results = st.tabs(['🧱 V220 Parametere', '📊 Optimeringsresultater'])

    # -----------------------------------------------------------------------
    # Tab 1 — V220 Parameters
    # -----------------------------------------------------------------------
    with tab_params:
        params = _render_tormur_params(act_id)

        if params:
            # Live check
            st.markdown('#### 🔍 Kontroll (gjeldende parametre)')
            _render_tormur_check(params)

            st.markdown('---')
            if st.button('💾 Sett parametere', key=f'save_p_{act_id}',
                         type='primary', use_container_width=True):
                api.save_tormur_params(act_id, params)
                st.session_state[f'tormur_params_{act_id}'] = params
                st.success('Parametere lagret.')
            st.caption(
                'Etter at parametre er satt, gå til Grasshopper og send '
                'to polylinjer (topp + bunn) med ønsket intervall til:\n\n'
                f'`POST /api/modeling/optimize-from-gh`\n\n'
                f'med `project_name` = prosjektnavnet og '
                f'`activity_name` = "{act["name"]}"`'
            )

    # -----------------------------------------------------------------------
    # Tab 2 — Grasshopper results / waiting state
    # -----------------------------------------------------------------------
    with tab_results:
        if not has_results:
            st.markdown('### 📡 Grasshopper-resultater')
            st.info(
                '**Ingen data sendt fra Grasshopper**\n\n'
                'Sett parameterne i V220-fanen, og kjør deretter '
                'optimaliseringen fra Grasshopper-plugin.\n\n'
                'Pluginen sender polylinjer (topp + bunn av mur) '
                'og intervall. Backend beregner optimale dimensjoner '
                'per seksjon automatisk.'
            )
            st.markdown(
                f'**Endepunkt:**\n\n'
                f'`POST /api/modeling/optimize-from-gh`\n\n'
                f'med `project_name` og `activity_name` = `"{act["name"]}"`'
            )
            return

        # --- Results exist — show everything ---
        st.markdown('### 📊 Optimeringsresultater')
        results = api.get_modeling_results(act_id)
        if 'error' in results:
            st.error(f'Kunne ikke hente resultater: {results.get("error")}')
            return

        report = results.get('run_report', {})
        summary = results.get('run_summary', '')

        if summary:
            with st.expander('📄 Sammendrag', expanded=False):
                st.markdown(summary)

        _build_summary_cards(report)

        # Tabs: charts + 3D + section detail
        sections = report.get('Sections', [])
        if sections:
            tab_geo, tab_sf, tab_xs, tab_tbl, tab_detail, tab_3d = st.tabs(
                ['📐 Geometri', '🔒 Sikkerhetsfaktorer', '📊 Tverrsnitt',
                 '📋 Tabell', '🔬 Seksjonsdetaljer', '🏗️ 3D Modell']
            )

            df = pd.DataFrame([{
                'Stasjon':     s.get('Station', 0),
                'Høyde':       s.get('Height', 0),
                'Topp-bredde': s.get('SmoothedTopWidth', s.get('TopWidth', 0)),
                'Bunn-bredde': s.get('SmoothedBottomWidth', s.get('BottomWidth', 0)),
                'Vinkel (°)':  s.get('SmoothedFaceAngleDeg', s.get('FaceAngleDeg', 0)),
                'Glidning SF': s.get('Checks', {}).get('SlidingFactor', 0),
                'Velting SF':  s.get('Checks', {}).get('OverturningFactor', 0),
                'Bæreevne SF': s.get('Checks', {}).get('BearingFactor', 0),
                'Godkjent':    s.get('Checks', {}).get('AllOk', False),
            } for s in sections])

            with tab_geo:
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=df['Stasjon'], y=df['Høyde'], mode='lines+markers',
                    name='Høyde', line=dict(color='steelblue', width=2),
                ))
                fig.update_layout(title='Høyde langs vegg',
                                  xaxis_title='Stasjon (m)',
                                  yaxis_title='Høyde (m)', height=350)
                st.plotly_chart(fig, use_container_width=True)

            with tab_sf:
                cfg = report.get('Config', {})
                fig = go.Figure()
                for col_name, color in [('Glidning SF', 'blue'),
                                         ('Velting SF', 'green'),
                                         ('Bæreevne SF', 'orange')]:
                    fig.add_trace(go.Scatter(
                        x=df['Stasjon'], y=df[col_name],
                        mode='lines', name=col_name, line=dict(color=color),
                    ))
                for val, name, color in [
                    (cfg.get('SlidingMin', 1.5), 'Min glidning', 'blue'),
                    (cfg.get('OverturningMin', 2.0), 'Min velting', 'green'),
                    (cfg.get('BearingMin', 3.0), 'Min bæreevne', 'orange'),
                ]:
                    fig.add_hline(y=val, line_dash='dash', line_color=color,
                                  annotation_text=f'{name} ({val})',
                                  annotation_position='right')
                fig.update_layout(title='Sikkerhetsfaktorer',
                                  xaxis_title='Stasjon (m)',
                                  yaxis_title='SF (−)', height=400)
                st.plotly_chart(fig, use_container_width=True)

            with tab_xs:
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=df['Stasjon'], y=df['Topp-bredde'],
                                          mode='lines', name='Topp-bredde',
                                          line=dict(color='teal')))
                fig.add_trace(go.Scatter(x=df['Stasjon'], y=df['Bunn-bredde'],
                                          mode='lines', name='Bunn-bredde',
                                          line=dict(color='coral')))
                fig.update_layout(title='Tverrsnitt', xaxis_title='Stasjon (m)',
                                  yaxis_title='Bredde (m)', height=350)
                st.plotly_chart(fig, use_container_width=True)

            with tab_tbl:
                display = df.copy()
                display['Styrende'] = [
                    s.get('Checks', {}).get('GoverningCheck', '')
                    for s in sections
                ]
                display['Status'] = display['Godkjent'].map({True: '✅', False: '❌'})
                st.dataframe(
                    display.drop(columns='Godkjent'),
                    use_container_width=True, hide_index=True,
                )

            with tab_detail:
                _render_section_detail(sections)

            with tab_3d:
                _render_3d_viewer(report)

        # Downloads
        st.markdown('---')
        dc1, dc2 = st.columns(2)
        with dc1:
            url = api.get_modeling_excel_export_url(act_id)
            st.link_button('⬇ Last ned Excel', url)
        with dc2:
            if act.get('has_ifc'):
                dl = api.get_modeling_download_url(act_id, 'ifc')
                if 'url' in dl:
                    st.link_button('⬇ Last ned IFC', dl['url'])


# ---------------------------------------------------------------------------
# Generell GH detail panel (existing functionality)
# ---------------------------------------------------------------------------

def _render_gh_detail(act: dict):
    """Original GH-based modeling detail view."""
    act_id = act['id']

    status_map = {
        'active':      '🟡 Ingen filer',
        'has_excel':   '🟠 Excel lastet opp — venter på GH-resultater',
        'has_results': '🟢 Resultater tilgjengelig',
    }
    st.caption(status_map.get(act.get('status', ''), act.get('status', '')))

    # Excel upload
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
    st.markdown('#### 📈 GH-optimeringsresultater')

    if act.get('has_results'):
        results = api.get_modeling_results(act_id)
        if 'error' not in results:
            report  = results.get('run_report', {})
            summary = results.get('run_summary', '')
            if summary:
                with st.expander('📄 Kjøringssammendrag', expanded=True):
                    st.markdown(summary)
            _build_summary_cards(report)
            st.markdown('---')
            _build_charts(report)
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


main()
