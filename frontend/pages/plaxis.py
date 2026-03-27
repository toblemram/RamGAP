# -*- coding: utf-8 -*-
"""
Plaxis Page
===========
Multi-step workflow for extracting results from a running Plaxis model:
  Level 1 -- Connect and read model info
  Level 2 -- Select analysis function
  Level 3 -- Select sheet pile(s) and anchors
  Level 4 -- Select phases and analysis types
  Level 5 -- Output settings and run calculation
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
    page_title="RamGAP",
    page_icon="🔧",
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

# -------------------------------------------------------------- session state
_DEFAULTS = {
    "plaxis_connected":         False,
    "plaxis_port":              10000,
    "plaxis_password":          "",
    "plaxis_output_port":       10001,
    "plaxis_output_password":   "",
    "plaxis_level":             1,
    "plaxis_model_data":        None,
    "plaxis_selected_function": None,
    "plaxis_selected_spunts":   [],
    "plaxis_selected_anchors":  [],
    "plaxis_selected_phases":   {},
    "plaxis_demo_mode":         False,
    "plaxis_activity_name":     "",
    "selected_project":         None,
}
for _k, _v in _DEFAULTS.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v


# ------------------------------------------------------------------ level 1

def show_level1():
    """Level 1: Connect to Plaxis and load model info."""
    st.markdown("### Nivå 1 – Innlesing av Plaxis-modell")
    st.markdown("Koble til en åpen Plaxis-modell for å hente ut strukturer og faser.")

    col1, col2 = st.columns([1, 2])

    with col1:
        st.markdown("#### Aktivitetsnavn")
        activity_name = st.text_input(
            "Gi aktiviteten et navn",
            value=st.session_state.plaxis_activity_name,
            placeholder="F.eks. 'Spuntberegning fase 1'",
        )
        st.session_state.plaxis_activity_name = activity_name

        st.markdown("---")
        st.markdown("#### Plaxis Input (modell)")
        port = st.number_input("Input Port", 1000, 65535,
                               value=st.session_state.plaxis_port)
        password = st.text_input("Input Passord",
                                  value=st.session_state.plaxis_password,
                                  type="password")
        st.markdown("---")
        st.markdown("#### Plaxis Output (resultater)")
        output_port = st.number_input("Output Port", 1000, 65535,
                                       value=st.session_state.plaxis_output_port)
        output_password = st.text_input("Output Passord",
                                         value=st.session_state.plaxis_output_password,
                                         type="password")

        st.session_state.plaxis_port            = port
        st.session_state.plaxis_password        = password
        st.session_state.plaxis_output_port     = output_port
        st.session_state.plaxis_output_password = output_password

        if not activity_name.strip():
            st.warning("⚠️ Du må gi aktiviteten et navn for å fortsette")

        if st.button("🔌 Koble til Plaxis", type="primary",
                     use_container_width=True, disabled=not activity_name.strip()):
            with st.spinner("Kobler til Plaxis..."):
                conn = api.plaxis_connect(port, password, USERNAME)
                if conn.get("success") or conn.get("demo_mode"):
                    st.session_state.plaxis_connected = True
                    st.session_state.plaxis_demo_mode = conn.get("demo_mode", False)
                    model = api.plaxis_model_info(USERNAME)
                    if model.get("success") or model.get("demo_mode"):
                        st.session_state.plaxis_model_data = model
                        st.session_state.plaxis_demo_mode  = model.get("demo_mode", False)
                        if model.get("demo_mode"):
                            st.warning("⚠️ Demo-modus: viser eksempeldata")
                        else:
                            st.success("✅ Tilkoblet! Modelldata lastet.")
                        st.rerun()
                    else:
                        st.error(f"Feil ved lasting av modell: {model.get('error')}")
                else:
                    st.error(f"Tilkoblingsfeil: {conn.get('error')}")

    with col2:
        st.markdown("#### Modellstatus")
        if st.session_state.plaxis_connected and st.session_state.plaxis_model_data:
            model   = st.session_state.plaxis_model_data
            structs = model.get("structures", {})
            phases  = model.get("phases", [])

            if st.session_state.plaxis_demo_mode:
                st.info("🎭 Demo-modus aktiv")
            else:
                st.success("✅ Tilkoblet til Plaxis")

            st.markdown("**Strukturer funnet:**")
            st.write(f"- Plater (spunt): {len(structs.get('plates', []))}")
            st.write(f"- Embedded beams: {len(structs.get('embedded_beams', []))}")
            st.write(f"- N2N-ankere: {len(structs.get('node_to_node_anchors', []))}")
            st.write(f"- Fixed-end ankere: {len(structs.get('fixed_end_anchors', []))}")
            st.write(f"- Geogrids: {len(structs.get('geogrids', []))}")
            st.markdown(f"**Antall faser:** {len(phases)}")
            with st.expander("Vis alle faser"):
                for ph in phases:
                    st.write(f"- {ph['name']}")
            st.markdown("---")
            if st.button("Neste → Velg funksjon", type="primary", use_container_width=True):
                st.session_state.plaxis_level = 2
                st.rerun()
        else:
            st.info("Koble til Plaxis for å se modellinformasjon")


# ------------------------------------------------------------------ level 2

def show_level2():
    """Level 2: Select which analysis function to run."""
    st.markdown("### Nivå 2 – Valg av funksjon")

    FUNCTIONS = [
        {"id": "optimize_depth", "name": "Optimalisering av spuntdybde",
         "desc": "Endring av underkant spunt for å optimalisere design", "enabled": False},
        {"id": "optimize_ks", "name": "Optimalisering av KS-stab",
         "desc": "Endring av materialparametere og spuntdybde", "enabled": False},
        {"id": "extract_results", "name": "Uttak av spuntberegninger",
         "desc": "Hent ut resultater for kapasitetssjekk, Msf, og deformasjoner", "enabled": True},
    ]

    selected = st.session_state.plaxis_selected_function
    for fn in FUNCTIONS:
        c1, c2 = st.columns([3, 1])
        with c1:
            st.markdown(f"**{fn['name']}**")
            st.caption(fn["desc"])
        with c2:
            if fn["enabled"]:
                label = "✓ Valgt" if selected == fn["id"] else "Velg"
                btype = "primary" if selected == fn["id"] else "secondary"
                if st.button(label, key=f"fn_{fn['id']}", type=btype, use_container_width=True):
                    st.session_state.plaxis_selected_function = fn["id"]
                    st.rerun()
            else:
                st.button("Kommer snart", key=f"fn_{fn['id']}_dis", disabled=True)

    st.markdown("---")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("← Forrige", use_container_width=True):
            st.session_state.plaxis_level = 1
            st.rerun()
    with c2:
        if st.button("Neste →", type="primary", use_container_width=True, disabled=not selected):
            st.session_state.plaxis_level = 3
            st.rerun()


# ------------------------------------------------------------------ level 3

def show_level3():
    """Level 3: Select sheet pile(s) and anchors."""
    st.markdown("### Nivå 3 – Valg av spunt og avstivninger")

    model = st.session_state.plaxis_model_data
    if not model:
        st.error("Ingen modelldata tilgjengelig")
        return

    structs = model.get("structures", {})
    spunts  = structs.get("plates", []) + structs.get("embedded_beams", [])
    anchors = (structs.get("node_to_node_anchors", [])
               + structs.get("fixed_end_anchors", []))

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### Velg spunt(er)")
        spunt_names = st.multiselect(
            "Spunt(er) som skal analyseres",
            options=[s["name"] for s in spunts],
            default=st.session_state.plaxis_selected_spunts,
        )
        st.session_state.plaxis_selected_spunts = spunt_names

    with c2:
        st.markdown("#### Velg avstivninger")
        anchor_names = st.multiselect(
            "Ankere/avstivninger",
            options=[a["name"] for a in anchors],
            default=st.session_state.plaxis_selected_anchors,
        )
        st.session_state.plaxis_selected_anchors = anchor_names

    st.markdown("---")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("← Forrige", use_container_width=True):
            st.session_state.plaxis_level = 2
            st.rerun()
    with c2:
        if st.button("Neste →", type="primary", use_container_width=True,
                     disabled=len(spunt_names) == 0):
            st.session_state.plaxis_level = 4
            st.rerun()


# ------------------------------------------------------------------ level 4

def show_level4():
    """Level 4: Select phases and analysis types (MSF, Ux, capacity check)."""
    st.markdown("### Nivå 4 – Valg av faser og analysetype")

    model = st.session_state.plaxis_model_data
    if not model:
        st.error("Ingen modelldata tilgjengelig")
        return

    phases = model.get("phases", [])
    if not st.session_state.plaxis_selected_phases:
        st.session_state.plaxis_selected_phases = {
            ph["name"]: {"msf": False, "ux": False, "capacity": False}
            for ph in phases
        }

    # Header
    c_name, c_msf, c_ux, c_cap = st.columns([3, 1, 1, 1])
    with c_name: st.markdown("**Fase**")
    with c_msf:  st.markdown("**Msf**")
    with c_ux:   st.markdown("**Ux**")
    with c_cap:  st.markdown("**Kapasitet**")
    st.markdown("---")

    for ph in phases:
        pname = ph["name"]
        if pname not in st.session_state.plaxis_selected_phases:
            st.session_state.plaxis_selected_phases[pname] = {
                "msf": False, "ux": False, "capacity": False}
        sel = st.session_state.plaxis_selected_phases[pname]

        c_name, c_msf, c_ux, c_cap = st.columns([3, 1, 1, 1])
        with c_name: st.write(pname)
        with c_msf:
            sel["msf"] = st.checkbox("Msf", value=sel["msf"],
                                      key=f"msf_{pname}", label_visibility="collapsed")
        with c_ux:
            sel["ux"] = st.checkbox("Ux", value=sel["ux"],
                                     key=f"ux_{pname}", label_visibility="collapsed")
        with c_cap:
            sel["capacity"] = st.checkbox("Kap", value=sel["capacity"],
                                           key=f"cap_{pname}", label_visibility="collapsed")

    st.markdown("---")
    q1, q2, q3 = st.columns(3)
    with q1:
        if st.button("Velg alle Msf", use_container_width=True):
            for s in st.session_state.plaxis_selected_phases.values():
                s["msf"] = True
            st.rerun()
    with q2:
        if st.button("Velg alle Ux", use_container_width=True):
            for s in st.session_state.plaxis_selected_phases.values():
                s["ux"] = True
            st.rerun()
    with q3:
        if st.button("Velg alle Kapasitet", use_container_width=True):
            for s in st.session_state.plaxis_selected_phases.values():
                s["capacity"] = True
            st.rerun()

    st.markdown("---")
    any_sel = any(
        any(v for v in ps.values())
        for ps in st.session_state.plaxis_selected_phases.values()
    )
    c1, c2 = st.columns(2)
    with c1:
        if st.button("← Forrige", use_container_width=True):
            st.session_state.plaxis_level = 3
            st.rerun()
    with c2:
        if st.button("Neste →", type="primary", use_container_width=True, disabled=not any_sel):
            st.session_state.plaxis_level = 5
            st.rerun()


# ------------------------------------------------------------------ level 5

def show_level5():
    """Level 5: Output settings and run the extraction."""
    st.markdown("### Nivå 5 – Output og resultater")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Valgte spunter:**")
        for s in st.session_state.plaxis_selected_spunts:
            st.write(f"- {s}")
        st.markdown("**Valgte ankere:**")
        if st.session_state.plaxis_selected_anchors:
            for a in st.session_state.plaxis_selected_anchors:
                st.write(f"- {a}")
        else:
            st.write("- Ingen valgt")
    with c2:
        st.markdown("**Faser med analyser:**")
        for pname, sel in st.session_state.plaxis_selected_phases.items():
            active = [k for k, v in sel.items() if v]
            if active:
                st.write(f"- {pname}: {', '.join(active)}")

    st.markdown("---")
    st.markdown("#### Output-innstillinger")
    output_path    = st.text_input("Lagringsmappe",
                                    value=os.path.expanduser("~/Documents/RamGAP_Results"))
    generate_excel = st.checkbox("Generer Excel spuntark", value=True)

    st.markdown("---")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("← Forrige", use_container_width=True):
            st.session_state.plaxis_level = 4
            st.rerun()
    with c2:
        if st.button("🚀 Kjør beregning", type="primary", use_container_width=True):
            _run_calculation(output_path, generate_excel)


# --------------------------------------------------------------- calculation

def _run_calculation(output_path: str, generate_excel: bool):
    """Build job payload and POST to the backend /api/plaxis/run endpoint."""
    progress = st.progress(0)
    status   = st.empty()

    status.text("Forbereder beregningsjobb...")
    progress.progress(5)

    model   = st.session_state.plaxis_model_data or {}
    structs = model.get("structures", {})

    job_structures = {
        "plates": [], "embedded_beams": [],
        "node_to_node_anchors": [], "fixed_end_anchors": [], "geogrids": [],
    }
    for name in st.session_state.plaxis_selected_spunts:
        for pl in structs.get("plates", []):
            if pl["name"] == name:
                job_structures["plates"].append(name)
        for eb in structs.get("embedded_beams", []):
            if eb["name"] == name:
                job_structures["embedded_beams"].append(name)
    for name in st.session_state.plaxis_selected_anchors:
        for n2n in structs.get("node_to_node_anchors", []):
            if n2n["name"] == name:
                job_structures["node_to_node_anchors"].append(name)
        for fea in structs.get("fixed_end_anchors", []):
            if fea["name"] == name:
                job_structures["fixed_end_anchors"].append(name)

    cap_phases, msf_phases, ux_phases = [], [], []
    for pname, sel in st.session_state.plaxis_selected_phases.items():
        if sel.get("capacity"): cap_phases.append(pname)
        if sel.get("msf"):      msf_phases.append(pname)
        if sel.get("ux"):       ux_phases.append(pname)

    job = {
        "structures": job_structures,
        "analysis": {
            "capacity_check": {"enabled": bool(cap_phases), "phases": cap_phases},
            "msf":            {"enabled": bool(msf_phases), "phases": msf_phases},
            "displacement":   {"enabled": bool(ux_phases),  "phases": ux_phases,
                               "component": "Ux"},
        },
        "resultsPath": {"path": output_path},
    }

    project_id = None
    if st.session_state.selected_project:
        project_id = st.session_state.selected_project.get("id")

    status.text("Sender beregning til Plaxis...")
    progress.progress(15)

    result = api.plaxis_run({
        "session_id":      USERNAME,
        "job":             job,
        "project_id":      project_id,
        "activity_name":   st.session_state.plaxis_activity_name or "Plaxis beregning",
        "input_port":      st.session_state.plaxis_port,
        "input_password":  st.session_state.plaxis_password,
        "output_port":     st.session_state.plaxis_output_port,
        "output_password": st.session_state.plaxis_output_password,
    })

    if result.get("success"):
        progress.progress(100)
        status.text("Ferdig!")
        if result.get("demo_mode"):
            st.info("🎭 Demo-modus: viser eksempelresultater")
        st.success("✅ Beregning fullført!")
        if result.get("output_file") and result["output_file"] != "Demo - ingen fil generert":
            st.info(f"📁 Resultater lagret i: {result['output_file']}")

        st.markdown("---")
        st.markdown("#### Resultater")
        results = result.get("results", {})

        msf = results.get("msf", {})
        if msf:
            st.markdown("**Msf-verdier:**")
            st.table({"Fase": list(msf.keys()), "Msf": list(msf.values())})

        disp = results.get("displacement", {})
        if disp:
            st.markdown("**Maks horisontal deformasjon:**")
            for stype, objs in disp.items():
                for oname, phases in objs.items():
                    st.table({"Fase": list(phases.keys()),
                              f"{oname} Ux (mm)": list(phases.values())})

        cap = results.get("capacity", {})
        if cap:
            st.markdown("**Tverrsnittskrefter:**")
            for stype, objs in cap.items():
                if stype in ("plates", "embedded_beams"):
                    for oname, phases in objs.items():
                        st.markdown(f"*{oname}:*")
                        rows = [
                            {"Fase": pn, "Nx (kN/m)": f.get("Nx"),
                             "Q (kN/m)": f.get("Q"), "M (kNm/m)": f.get("M")}
                            for pn, f in phases.items()
                        ]
                        if rows:
                            st.table(rows)
    else:
        progress.progress(0)
        st.error(f"❌ Feil: {result.get('error', 'Ukjent feil')}")


# ----------------------------------------------------------------------- page

def main():
    st.markdown("# 🔧 Plaxis Automatisering")

    proj = st.session_state.selected_project
    back_label = f"← Tilbake til {proj['name']}" if proj else "← Tilbake til hjem"
    if st.button(back_label):
        st.session_state.plaxis_level      = 1
        st.session_state.plaxis_connected  = False
        st.session_state.plaxis_model_data = None
        st.switch_page("app.py")

    # Progress indicator
    levels  = ["1. Tilkobling", "2. Funksjon", "3. Spunt/Ankere", "4. Faser", "5. Output"]
    current = st.session_state.plaxis_level
    cols    = st.columns(5)
    for i, (col, name) in enumerate(zip(cols, levels)):
        with col:
            if i + 1 < current:    st.success(f"✓ {name}")
            elif i + 1 == current: st.info(f"→ {name}")
            else:                  st.caption(name)
    st.markdown("---")

    if   current == 1: show_level1()
    elif current == 2: show_level2()
    elif current == 3: show_level3()
    elif current == 4: show_level4()
    elif current == 5: show_level5()


main()
# TODO: connect form, model-info display, extraction job form, results table
