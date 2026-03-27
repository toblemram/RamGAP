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
import io as _io
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import streamlit as st

# Ensure frontend/ root is importable (needed when Streamlit runs pages/ directly)
_HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from components.api_client import APIClient

st.set_page_config(
    page_title="RamGAP",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Hide Streamlit's auto-generated pages navigation
st.markdown("""
<style>
    [data-testid="stSidebarNav"] { display: none !important; }
</style>
""", unsafe_allow_html=True)


from components.auth import require_username

USERNAME = require_username()
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
        {"type": "leire", "start": 0.0,        "end": md / 3},
        {"type": "sand",  "start": md / 3,     "end": 2 * md / 3},
        {"type": "fjell", "start": 2 * md / 3, "end": md},
    ]


def _clear_layer_ss(n: int):
    """Remove old widget session keys so they re-initialise from layers."""
    for j in range(n + 2):
        for prefix in ("gt_top_", "gt_bot_", "gt_type_", "gt_rng_"):
            st.session_state.pop(f"{prefix}{j}", None)


@st.fragment
def show_step3():
    """Step 3: Interactive depth-profile chart and layer boundary editor."""
    files = st.session_state.geotolk_files
    if not files:
        st.warning("Ingen filer å tolke")
        return

    idx = st.session_state.geotolk_current_file
    cur = files[idx]
    parsed    = cur["parsed_data"]
    max_depth = float(parsed.get("max_depth", 10))

    # File navigation
    cn1, cn2, cn3 = st.columns([1, 3, 1])
    with cn1:
        if st.button("◀ Forrige", use_container_width=True, disabled=idx == 0):
            files[idx]["layers"] = st.session_state.geotolk_layers
            st.session_state.geotolk_current_file = idx - 1
            prev = files[idx - 1]
            _clear_layer_ss(len(st.session_state.geotolk_layers))
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
            _clear_layer_ss(len(st.session_state.geotolk_layers))
            if nxt.get("layers"):
                st.session_state.geotolk_layers = nxt["layers"]
            else:
                _init_layers(nxt)
            st.rerun()

    layers = st.session_state.geotolk_layers
    n = len(layers)

    # ------------------------------------------------------------------ PRE-APPLY
    # Initialise session-state keys on first render, then read them back into
    # layers BEFORE building the chart so the chart is always in sync.
    for i, lay in enumerate(layers):
        if f"gt_type_{i}" not in st.session_state:
            st.session_state[f"gt_type_{i}"] = lay["type"]
        if f"gt_top_{i}" not in st.session_state:
            st.session_state[f"gt_top_{i}"] = float(lay["start"])
        if f"gt_bot_{i}" not in st.session_state:
            st.session_state[f"gt_bot_{i}"] = float(lay["end"])

    for i in range(n):
        layers[i]["type"]  = st.session_state[f"gt_type_{i}"]
        layers[i]["start"] = float(st.session_state[f"gt_top_{i}"])
        layers[i]["end"]   = float(st.session_state[f"gt_bot_{i}"])

    # Enforce hard limits and cascade adjacency top→bottom
    layers[0]["start"] = 0.0;       st.session_state["gt_top_0"] = 0.0
    layers[-1]["end"]  = max_depth; st.session_state[f"gt_bot_{n-1}"] = max_depth
    for i in range(n - 1):
        adj = layers[i]["end"]
        if abs(layers[i + 1]["start"] - adj) > 0.001:
            layers[i + 1]["start"] = adj
            st.session_state[f"gt_top_{i + 1}"] = adj
    for i in range(n):
        if layers[i]["start"] >= layers[i]["end"]:
            layers[i]["end"] = min(layers[i]["start"] + 0.05, max_depth)
            st.session_state[f"gt_bot_{i}"] = layers[i]["end"]

    st.session_state.geotolk_layers = layers

    # -------------------------------------------------------------------- CHART
    max_x = max(parsed.get("c2", [1000])) or 1000
    fig, ax = plt.subplots(figsize=(5, 10))
    for lay in layers:
        chex = GEOTOLK_COLORS.get(lay["type"], "#DDDDDD")
        rgb  = tuple(int(chex.lstrip("#")[j:j+2], 16) / 255 for j in (0, 2, 4))
        ax.axhspan(lay["start"], lay["end"], alpha=0.3, color=rgb, zorder=1)
        mid = (lay["start"] + lay["end"]) / 2
        ax.text(max_x * 0.02, mid, lay["type"], fontsize=9, va="center", color="#333", zorder=3)

    depths, c2vals = list(parsed.get("depth", [])), list(parsed.get("c2", []))
    if len(depths) > 500:
        s = len(depths) // 500
        depths, c2vals = depths[::s], c2vals[::s]
    if depths:
        ax.plot(c2vals, depths, "k-", linewidth=1.5, zorder=2)

    for i in range(n - 1):
        ax.axhline(y=layers[i]["end"], color="red", linewidth=2, linestyle="--", zorder=4)

    for s, e in parsed.get("spyling", []):
        ax.barh([(s+e)/2], [max_x*0.05], left=0,           height=e-s, alpha=0.5, color="blue", zorder=2)
    for s, e in parsed.get("slag", []):
        ax.barh([(s+e)/2], [max_x*0.05], left=max_x*0.05,  height=e-s, alpha=0.5, color="red",  zorder=2)

    ax.set_xlabel("Motstand", fontsize=10)
    ax.set_ylabel("Dybde (m)", fontsize=10)
    ax.set_xlim(0, max_x); ax.set_ylim(max_depth, 0)
    ax.grid(True, alpha=0.3, linestyle=":")
    plt.tight_layout(pad=0.5)
    buf = _io.BytesIO()
    fig.savefig(buf, format="png", dpi=110, bbox_inches="tight")
    plt.close(fig); buf.seek(0)

    # ------------------------------------------------------------------- LAYOUT
    col_plot, col_edit = st.columns([2, 1])

    with col_plot:
        st.image(buf, use_container_width=True)
        st.caption("🔵 Spyling | 🔴 Slag | 🔴- - - Laggrenser")

    with col_edit:
        st.markdown("#### Lagdeling")
        st.caption(f"Total dybde: {max_depth:.2f} m")

        for i, lay in enumerate(layers):
            color = GEOTOLK_COLORS.get(lay["type"], "#DDDDDD")
            st.markdown(
                f'<span style="display:inline-block;width:12px;height:12px;'
                f'background:{color};border:1px solid #888;border-radius:2px;'
                f'vertical-align:middle;margin-right:6px"></span>'
                f'<strong>Lag {i + 1}</strong>',
                unsafe_allow_html=True,
            )
            st.selectbox(
                "Materiale", GEOTOLK_MATERIALS,
                index=GEOTOLK_MATERIALS.index(lay["type"]) if lay["type"] in GEOTOLK_MATERIALS else 0,
                key=f"gt_type_{i}", label_visibility="collapsed",
            )
            cur_s = float(max(0.0, lay["start"]))
            cur_e = float(min(max_depth, lay["end"]))
            if cur_s >= cur_e:
                cur_e = min(cur_s + 0.05, max_depth)
            rng = st.slider(
                f"Dybde lag {i + 1}",
                min_value=0.0, max_value=max_depth,
                value=(cur_s, cur_e),
                step=0.05,
                key=f"gt_rng_{i}",
                label_visibility="collapsed",
            )
            layers[i]["start"] = float(rng[0])
            layers[i]["end"]   = float(rng[1])
            # keep number-input keys in sync so pre-apply is consistent
            st.session_state[f"gt_top_{i}"] = float(rng[0])
            st.session_state[f"gt_bot_{i}"] = float(rng[1])
            st.caption(f"Fra **{rng[0]:.2f} m** → Til **{rng[1]:.2f} m**")
            if i < n - 1:
                st.divider()

        st.markdown("---")
        del_cols = st.columns(n)
        for i, dc in enumerate(del_cols):
            with dc:
                if st.button(f"✖ {i + 1}", key=f"del_{i}", disabled=n <= 1):
                    if i < n - 1:
                        layers[i + 1]["start"] = layers[i]["start"]
                    else:
                        layers[i - 1]["end"] = layers[i]["end"]
                    layers.pop(i)
                    _clear_layer_ss(n)
                    st.session_state.geotolk_layers = layers
                    st.rerun()

        if st.button("➕ Legg til lag", use_container_width=True):
            if layers:
                last = layers[-1]
                mid  = (last["start"] + last["end"]) / 2
                last["end"] = mid
                layers.append({"type": "annet", "start": mid, "end": max_depth})
            else:
                layers.append({"type": "annet", "start": 0.0, "end": max_depth})
            _clear_layer_ss(n)
            st.session_state.geotolk_layers = layers
            st.rerun()

        if st.button("🔄 Auto 3 lag", use_container_width=True):
            _clear_layer_ss(n)
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
                st.session_state.geotolk_files  = []
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
