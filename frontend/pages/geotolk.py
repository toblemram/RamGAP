# -*- coding: utf-8 -*-
"""
GeoTolk Page
============
Multi-step workflow for interpreting SND ground-investigation files:
  Step 1 -- Setup: name the interpretation session
  Step 2 -- Upload SND files
  Step 3 -- Visual interpretation: assign soil layers with boundary sliders
"""

import sys
import os
import streamlit as st

# Ensure frontend/ root is importable (needed when Streamlit runs pages/ directly)
_HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from components.api_client import APIClient

st.set_page_config(
    page_title="RamGAP - GeoTolk",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def _get_username() -> str:
    try:
        return os.getlogin()
    except OSError:
        return os.environ.get("USERNAME", os.environ.get("USER", "User"))


USERNAME = _get_username()
api = APIClient()

# Soil material colours used in the depth-profile chart
GEOTOLK_COLORS = {
    "leire": "#CC6666",
    "sand":  "#CCCC66",
    "fjell": "#99CCEE",
    "annet": "#DDDDDD",
}
GEOTOLK_MATERIALS = ["leire", "sand", "fjell", "annet"]

# -------------------------------------------------------------- session state
_DEFAULTS = {
    "geotolk_step":          1,
    "geotolk_activity_name": "",
    "geotolk_session_id":    None,
    "geotolk_files":         [],
    "geotolk_current_file":  0,
    "geotolk_layers":        [],
    "selected_project":      None,
}
for _k, _v in _DEFAULTS.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v


# -------------------------------------------------------------------- step 1

def show_step1():
    """Step 1: Set the activity/session name."""
    st.markdown("### Steg 1 – Oppsett")
    c1, c2 = st.columns([1, 1])

    with c1:
        aname = st.text_input(
            "Aktivitetsnavn",
            value=st.session_state.geotolk_activity_name,
            placeholder="F.eks. 'Grunnundersøkelse fase 1'",
        )
        st.session_state.geotolk_activity_name = aname

        if not aname.strip():
            st.warning("⚠️ Du må gi aktiviteten et navn.")
            return

        if st.button("Neste →", type="primary", use_container_width=True):
            proj_id = None
            if st.session_state.selected_project:
                proj_id = st.session_state.selected_project.get("id")
            res = api.create_geotolk_session(proj_id, aname, USERNAME)
            if res.get("success"):
                st.session_state.geotolk_session_id = res["session"]["id"]
                st.session_state.geotolk_step = 2
                st.rerun()
            else:
                st.error(f"Feil: {res.get('error')}")

    with c2:
        st.markdown("#### Om GeoTolk")
        st.info("""
**GeoTolk** lar deg tolke SND-filer fra grunnundersøkelser.

**Funksjoner:**
- Last opp SND-filer
- Visualiser motstand vs. dybde
- Definer lagdeling (leire, sand, fjell, annet)
- Tolkningene lagres for fremtidig ML-trening

**Fremtidig:** ML-algoritme vil foreslå lagdeling automatisk.
        """)


# -------------------------------------------------------------------- step 2

def show_step2():
    """Step 2: Upload and parse SND files."""
    st.markdown("### Steg 2 – Last opp SND-filer")

    uploaded = st.file_uploader("Velg SND-filer", type=["snd", "txt"],
                                  accept_multiple_files=True)
    if uploaded:
        files_data = []
        for uf in uploaded:
            content = uf.read().decode("utf-8", errors="ignore")
            res = api.geotolk_parse(content)
            if res.get("success"):
                files_data.append({
                    "filename":    uf.name,
                    "content":     content,
                    "parsed_data": res["data"],
                    "layers":      [],
                    "status":      "pending",
                })
            else:
                st.warning(f"Kunne ikke parse {uf.name}: {res.get('error')}")

        if files_data:
            st.success(f"✅ {len(files_data)} filer lastet opp og parset")
            for f in files_data:
                depth = f["parsed_data"].get("max_depth", 0)
                st.write(f"• {f['filename']} – Max dybde: {depth:.2f} m")
            st.session_state.geotolk_files = files_data

    st.markdown("---")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("← Forrige", use_container_width=True):
            st.session_state.geotolk_step = 1
            st.rerun()
    with c2:
        if st.button("Start tolkning →", type="primary", use_container_width=True,
                     disabled=len(st.session_state.geotolk_files) == 0):
            st.session_state.geotolk_current_file = 0
            _init_layers(st.session_state.geotolk_files[0])
            st.session_state.geotolk_step = 3
            st.rerun()


# -------------------------------------------------------------------- step 3

def _init_layers(file_entry: dict):
    """Set a default 3-layer split for a file."""
    md = file_entry["parsed_data"].get("max_depth", 10)
    st.session_state.geotolk_layers = [
        {"type": "leire", "start": 0.0,       "end": md / 3},
        {"type": "sand",  "start": md / 3,    "end": 2 * md / 3},
        {"type": "fjell", "start": 2 * md / 3, "end": md},
    ]


def show_step3():
    """Step 3: Interactive depth-profile chart and layer boundary editor."""
    import plotly.graph_objects as go

    files = st.session_state.geotolk_files
    if not files:
        st.warning("Ingen filer å tolke")
        return

    idx = st.session_state.geotolk_current_file
    cur = files[idx]

    # File navigation
    cn1, cn2, cn3 = st.columns([1, 3, 1])
    with cn1:
        if st.button("◀ Forrige", use_container_width=True, disabled=idx == 0):
            files[idx]["layers"] = st.session_state.geotolk_layers
            st.session_state.geotolk_current_file = idx - 1
            prev = files[idx - 1]
            if prev.get("layers"):
                st.session_state.geotolk_layers = prev["layers"]
            else:
                _init_layers(prev)
            st.rerun()
    with cn2:
        st.markdown(f"### Fil {idx + 1} av {len(files)}: {cur['filename']}")
    with cn3:
        if st.button("Neste ▶", use_container_width=True, disabled=idx >= len(files) - 1):
            files[idx]["layers"] = st.session_state.geotolk_layers
            st.session_state.geotolk_current_file = idx + 1
            nxt = files[idx + 1]
            if nxt.get("layers"):
                st.session_state.geotolk_layers = nxt["layers"]
            else:
                _init_layers(nxt)
            st.rerun()

    col_plot, col_edit = st.columns([2, 1])

    with col_plot:
        parsed    = cur["parsed_data"]
        max_depth = parsed.get("max_depth", 10)
        layers    = st.session_state.geotolk_layers
        fig       = go.Figure()

        # Coloured background bands per layer
        for i, lay in enumerate(layers):
            color = GEOTOLK_COLORS.get(lay["type"], "#DDDDDD")
            fig.add_hrect(y0=lay["start"], y1=lay["end"],
                          fillcolor=color, opacity=0.3, line_width=0,
                          annotation_text=f"{i + 1}. {lay['type']}",
                          annotation_position="left")

        # Resistance trace (downsampled for performance)
        depths = parsed["depth"]
        c2vals = parsed["c2"]
        if len(depths) > 500:
            step   = len(depths) // 500
            depths = depths[::step]
            c2vals = c2vals[::step]
        fig.add_trace(go.Scatter(
            x=c2vals, y=depths, mode="lines", name="Motstand",
            line=dict(color="black", width=1.5), hoverinfo="skip",
        ))

        # Layer boundary lines
        max_x = max(parsed["c2"]) if parsed["c2"] else 1000
        for i in range(len(layers) - 1):
            fig.add_shape(type="line", x0=0, x1=max_x,
                          y0=layers[i]["end"], y1=layers[i]["end"],
                          line=dict(color="red", width=2, dash="dash"))

        # Spyling / slag markers
        for s, e in parsed.get("spyling", []):
            fig.add_vrect(x0=0, x1=max_x * 0.05, y0=s, y1=e,
                          fillcolor="blue", opacity=0.5)
        for s, e in parsed.get("slag", []):
            fig.add_vrect(x0=max_x * 0.05, x1=max_x * 0.1, y0=s, y1=e,
                          fillcolor="red", opacity=0.5)

        fig.update_layout(
            xaxis_title="Motstand",
            yaxis_title="Dybde (m)",
            yaxis_autorange="reversed",
            height=700,
            showlegend=False,
            margin=dict(l=50, r=10, t=10, b=30),
            xaxis=dict(fixedrange=True),
            yaxis=dict(fixedrange=True),
        )
        st.plotly_chart(fig, use_container_width=True,
                        config={"displayModeBar": False, "staticPlot": True})
        st.caption("🔵 Spyling | 🔴 Slag | 🔴- - - Laggrenser")

    with col_edit:
        st.markdown("#### Lagdeling")
        st.caption(f"Max dybde: {max_depth:.2f} m")
        layers = st.session_state.geotolk_layers

        # Material-type selector per layer
        st.markdown("**Lagtyper:**")
        for i, lay in enumerate(layers):
            ci, ct = st.columns([1, 4])
            with ci:
                st.markdown(f"**{i + 1}.**")
            with ct:
                new_type = st.selectbox(
                    f"Lag {i + 1}",
                    GEOTOLK_MATERIALS,
                    index=GEOTOLK_MATERIALS.index(lay["type"])
                          if lay["type"] in GEOTOLK_MATERIALS else 0,
                    key=f"ltype_{i}",
                    label_visibility="collapsed",
                )
                layers[i]["type"] = new_type

        st.markdown("---")
        st.markdown("**Grenser (dra for å justere):**")
        st.caption("Topp: 0.00 m")

        for i in range(len(layers) - 1):
            min_v = layers[i]["start"] + 0.1
            max_v = layers[i + 1]["end"] - 0.1
            cur_v = max(min_v, min(float(layers[i]["end"]), max_v))
            new_b = st.slider(
                f"Grense {i + 1}→{i + 2}",
                min_value=0.0, max_value=float(max_depth),
                value=cur_v, step=0.05, key=f"bnd_{i}",
            )
            layers[i]["end"]       = new_b
            layers[i + 1]["start"] = new_b

        st.caption(f"Bunn: {max_depth:.2f} m")
        layers[0]["start"]  = 0.0
        layers[-1]["end"]   = float(max_depth)
        st.session_state.geotolk_layers = layers

        st.markdown("---")
        # Remove-layer buttons
        st.markdown("**Fjern lag:**")
        del_cols = st.columns(len(layers))
        for i, dc in enumerate(del_cols):
            with dc:
                if st.button(f"✖ {i + 1}", key=f"del_{i}", disabled=len(layers) <= 1):
                    if i < len(layers) - 1:
                        layers[i + 1]["start"] = layers[i]["start"]
                    else:
                        layers[i - 1]["end"] = layers[i]["end"]
                    layers.pop(i)
                    st.session_state.geotolk_layers = layers
                    st.rerun()

        if st.button("➕ Legg til lag", use_container_width=True):
            if layers:
                last = layers[-1]
                mid  = (last["start"] + last["end"]) / 2
                last["end"] = mid
                layers.append({"type": "annet", "start": mid, "end": float(max_depth)})
            else:
                layers.append({"type": "annet", "start": 0.0, "end": float(max_depth)})
            st.session_state.geotolk_layers = layers
            st.rerun()

        if st.button("🔄 Auto 3 lag", use_container_width=True):
            _init_layers(cur)
            st.rerun()

    # Save / Finish row
    st.markdown("---")
    cs, cf = st.columns(2)
    with cs:
        if st.button("💾 Lagre tolkning", type="primary", use_container_width=True):
            files[idx]["layers"] = st.session_state.geotolk_layers
            files[idx]["status"] = "interpreted"
            res = api.add_geotolk_interpretation(
                st.session_state.geotolk_session_id,
                cur["filename"],
                cur["parsed_data"],
                st.session_state.geotolk_layers,
            )
            if res.get("success"):
                st.success("✅ Tolkning lagret!")
            else:
                st.error(f"Feil: {res.get('error')}")

    with cf:
        done = sum(1 for f in files if f.get("status") == "interpreted")
        if st.button(f"✓ Fullfør ({done}/{len(files)} tolket)", use_container_width=True):
            if done > 0:
                st.session_state.geotolk_step  = 1
                st.session_state.geotolk_files = []
                st.session_state.geotolk_layers = []
                st.success("Tolkningsøkt fullført!")
                st.switch_page("app.py")
            else:
                st.warning("Lagre minst én tolkning før du fullfører")


# ----------------------------------------------------------------------- page

def main():
    st.markdown("# 🗺️ GeoTolk")

    proj      = st.session_state.selected_project
    back_label = f"← Tilbake til {proj['name']}" if proj else "← Tilbake til hjem"
    if st.button(back_label):
        st.session_state.geotolk_step  = 1
        st.session_state.geotolk_files = []
        st.switch_page("app.py")

    # Step progress indicator
    steps   = ["1. Oppsett", "2. Last opp filer", "3. Tolkning"]
    current = st.session_state.geotolk_step
    scols   = st.columns(3)
    for i, (sc, sname) in enumerate(zip(scols, steps)):
        with sc:
            if i + 1 < current:    st.success(f"✓ {sname}")
            elif i + 1 == current: st.info(f"→ {sname}")
            else:                  st.caption(sname)
    st.markdown("---")

    if   current == 1: show_step1()
    elif current == 2: show_step2()
    elif current == 3: show_step3()


main()

import streamlit as st
from components.sidebar import render_sidebar

st.set_page_config(page_title="GeoTolk — RamGAP", layout="wide")

render_sidebar()

st.title("GeoTolk")
st.write("Geotechnical file upload and visualization will be implemented here.")
# TODO: file uploader, depth-profile chart, interpretation controls
