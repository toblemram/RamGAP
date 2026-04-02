# -*- coding: utf-8 -*-
"""
GeoTolk Page
============
Multi-step workflow for interpreting SND ground-investigation files:
  Step 1 -- Setup: name the interpretation session
  Step 2 -- Upload SND files
  Step 3 -- Visual interpretation: assign soil layers with boundary sliders
"""

import io as _io
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import streamlit as st
from components.auth import require_username
from components.api_client import APIClient

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

def _find_snd_files(folder_path: str) -> list[Path]:
    """Find SND files in a project folder (checks AUTOGRAF subfolder first)."""
    folder = Path(folder_path)
    if not folder.is_dir():
        return []

    autograf_dir = None
    if folder.name.upper().startswith("AUTOGRAF") and list(folder.glob("*.SND")):
        autograf_dir = folder
    else:
        for child in folder.iterdir():
            if child.is_dir() and child.name.upper().startswith("AUTOGRAF"):
                autograf_dir = child
                break

    if autograf_dir is None:
        direct_snd = list(folder.glob("*.SND")) + list(folder.glob("*.snd"))
        if direct_snd:
            autograf_dir = folder

    if autograf_dir is None:
        return []

    snd_set = {p.resolve() for p in autograf_dir.glob("*.SND")}
    snd_set |= {p.resolve() for p in autograf_dir.glob("*.snd")}
    return sorted(snd_set, key=lambda p: p.name)


def show_step2():
    """Step 2: Upload and parse SND files."""
    st.markdown("### Steg 2 – Last opp SND-filer")

    project = st.session_state.selected_project
    folder_path = project.get("folder_path") if project else None

    from_project = False
    if folder_path:
        from_project = st.checkbox(f"📁 Hent fra prosjekt (`{folder_path}`)", value=False, key="geotolk_from_project")

    if from_project and folder_path:
        if st.button("📥 Last inn filer fra prosjektmappe", type="primary", key="geotolk_fetch_project", use_container_width=True):
            snd_paths = _find_snd_files(folder_path)
            if not snd_paths:
                st.warning(f"Fant ingen SND-filer i prosjektmappen: `{folder_path}`")
            else:
                files_data = []
                progress = st.progress(0, text="Laster SND-filer…")
                for i, snd_path in enumerate(snd_paths):
                    progress.progress((i + 1) / len(snd_paths), text=f"Parser {snd_path.name} ({i+1}/{len(snd_paths)})")
                    content = snd_path.read_text(encoding="utf-8", errors="ignore")
                    res = api.geotolk_parse(content)
                    if res.get("success"):
                        files_data.append({
                            "filename":    snd_path.name,
                            "content":     content,
                            "parsed_data": res["data"],
                            "layers":      [],
                            "status":      "pending",
                        })
                    else:
                        st.warning(f"Kunne ikke parse {snd_path.name}: {res.get('error')}")
                progress.empty()

                if files_data:
                    st.success(f"✅ {len(files_data)} filer hentet fra prosjektmappen")
                    for f in files_data:
                        depth = f["parsed_data"].get("max_depth", 0)
                        st.write(f"• {f['filename']} – Max dybde: {depth:.2f} m")
                    st.session_state.geotolk_files = files_data
    else:
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

    # Interactive layer editor (Canvas-based, all in JS)
    from components.geotolk_editor import geotolk_editor

    updated_layers = geotolk_editor(
        sounding_data=parsed,
        layers=st.session_state.geotolk_layers,
        max_depth=max_depth,
        materials=GEOTOLK_MATERIALS,
        colors=GEOTOLK_COLORS,
        key=f"editor_{idx}",
    )
    if updated_layers:
        st.session_state.geotolk_layers = updated_layers

    # Reset layers
    cr, _ = st.columns([1, 3])
    with cr:
        if st.button("🔄 Tilbakestill lag", use_container_width=True):
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
                st.switch_page("pages/home.py")
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
        st.switch_page("pages/home.py")

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
