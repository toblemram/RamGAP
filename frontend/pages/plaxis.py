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

import os
import streamlit as st
from components.auth import require_username
from components.api_client import APIClient

USERNAME = require_username()
api = APIClient()

# -------------------------------------------------------------- session state
_DEFAULTS = {
    "plaxis_connected":         False,
    "plaxis_host":              "",
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
    "plaxis_activity_name":     "",
    "selected_project":         None,
    # Parametric study state
    "para_ks_soil":             None,
    "para_soil_params":         {},
    "para_spunt_plate":         None,
    "para_spunt_range":         {},
    "para_phases_config":       {},
    "para_results":             None,
    # Water sensitivity state
    "ws_water_values":          "",
    "ws_plate":                 None,
    "ws_phases_config":         {},
    "ws_results":               None,
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
        host = st.text_input("Plaxis Host",
                             value=st.session_state.plaxis_host,
                             placeholder="F.eks. '192.168.1.100' eller tomt for localhost")
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
        st.session_state.plaxis_host            = host
        st.session_state.plaxis_output_port     = output_port
        st.session_state.plaxis_output_password = output_password

        if not activity_name.strip():
            st.warning("⚠️ Du må gi aktiviteten et navn for å fortsette")

        if st.button("🔌 Koble til Plaxis", type="primary",
                     use_container_width=True, disabled=not activity_name.strip()):
            with st.spinner("Kobler til Plaxis..."):
                conn = api.plaxis_connect(port, password, USERNAME, host=host)
                if conn.get("success"):
                    st.session_state.plaxis_connected = True
                    model = api.plaxis_model_info(USERNAME)
                    if model.get("success"):
                        st.session_state.plaxis_model_data = model
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

            st.success("✅ Tilkoblet til Plaxis")

            # ---- Plate cards ----
            plates = structs.get("plates", [])
            if plates:
                st.markdown("---")
                st.markdown("#### 🔩 Plater (spunt)")
                for pl in plates:
                    with st.expander(f"**{pl['name']}**  —  {pl.get('material', {}).get('name', 'Ukjent materiale')}"):
                        c1, c2 = st.columns(2)
                        with c1:
                            st.markdown("**Geometri**")
                            st.write(f"Topp: ({pl.get('x1', '–')}, {pl.get('y1', '–')})")
                            st.write(f"Bunn: ({pl.get('x2', '–')}, {pl.get('y2', '–')})")
                            st.write(f"Lengde: {pl.get('length', '–')} m")
                        with c2:
                            mat = pl.get("material")
                            if mat:
                                st.markdown("**Materiale**")
                                st.write(f"Navn: {mat.get('name', '–')}")
                                if 'EA1' in mat:
                                    st.write(f"EA: {mat['EA1']:,.0f} kN/m")
                                if 'EI' in mat:
                                    st.write(f"EI: {mat['EI']:,.0f} kNm²/m")
                                if 'd' in mat:
                                    st.write(f"d: {mat['d']:.3f} m")
                                if 'w' in mat:
                                    st.write(f"w: {mat['w']} kN/m/m")

            # ---- Anchor cards ----
            n2n_anchors = structs.get("node_to_node_anchors", [])
            fea_anchors = structs.get("fixed_end_anchors", [])
            all_anchors = n2n_anchors + fea_anchors
            if all_anchors:
                st.markdown("---")
                st.markdown("#### ⚓ Ankere")
                for anc in all_anchors:
                    atype = "N2N-anker" if anc.get("type") == "node_to_node_anchor" else "Fixed-end anker"
                    mat_name = anc.get('material', {}).get('name', 'Ukjent')
                    with st.expander(f"**{anc['name']}**  —  {mat_name}  ({atype})"):
                        c1, c2 = st.columns(2)
                        with c1:
                            st.markdown("**Geometri**")
                            if 'x1' in anc:
                                st.write(f"Fra: ({anc['x1']}, {anc['y1']})")
                                st.write(f"Til: ({anc['x2']}, {anc['y2']})")
                            elif 'x' in anc:
                                st.write(f"Punkt: ({anc['x']}, {anc['y']})")
                            if 'length' in anc:
                                st.write(f"Lengde: {anc['length']} m")
                        with c2:
                            mat = anc.get("material")
                            if mat:
                                st.markdown("**Materiale**")
                                st.write(f"Navn: {mat.get('name', '–')}")
                                if 'EA' in mat:
                                    st.write(f"EA: {mat['EA']:,.0f} kN")
                                if 'Lspacing' in mat:
                                    st.write(f"Avstand: {mat['Lspacing']} m")

            # ---- Embedded beams cards ----
            ebeams = structs.get("embedded_beams", [])
            if ebeams:
                st.markdown("---")
                st.markdown("#### 🪵 Embedded Beams")
                for eb in ebeams:
                    with st.expander(f"**{eb['name']}**"):
                        st.write(f"Topp: ({eb.get('x1', '–')}, {eb.get('y1', '–')})")
                        st.write(f"Bunn: ({eb.get('x2', '–')}, {eb.get('y2', '–')})")
                        if 'length' in eb:
                            st.write(f"Lengde: {eb['length']} m")

            # ---- Phase cards ----
            st.markdown("---")
            st.markdown("#### 📋 Faser")
            for ph in phases:
                calc_type = ph.get("calc_type", "")
                prev = ph.get("previous", "")
                is_fos = ph.get("calc_type_id") == 7

                icon = "🔴" if is_fos else "🔵"
                label = f"{icon} **{ph['name']}**"
                if calc_type:
                    label += f"  —  _{calc_type}_"

                with st.expander(label):
                    c1, c2 = st.columns(2)
                    with c1:
                        st.write(f"**Nr:** {ph.get('number', ph['id'])}")
                        st.write(f"**Type:** {calc_type}")
                    with c2:
                        if prev:
                            st.write(f"**Forrige fase:** {prev}")
                        if is_fos:
                            st.caption("⚠️ Sikkerhetsfase (phi/c-reduksjon)")

            # AI Quality Check
            st.markdown("---")
            st.markdown("#### 🤖 AI-kvalitetssjekk av modell")
            st.caption("AI analyserer modellen og flagger potensielle problemer.")
            if st.button("🔍 Kjør AI-kvalitetssjekk", use_container_width=True, key="ai_qc_btn"):
                with st.spinner("AI analyserer modellen..."):
                    qc = api.plaxis_ai_quality_check(model)
                    if qc.get("success"):
                        st.session_state["_ai_qc_report"] = qc.get("report", "")
                    else:
                        st.error(f"AI-feil: {qc.get('error')}")

            if st.session_state.get("_ai_qc_report"):
                st.markdown(st.session_state["_ai_qc_report"])

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
        {"id": "parametric_spunt", "name": "Parametrisk spuntberegning",
         "desc": "Varier jordparametere og spuntdybde, kjør beregning automatisk og sammenlign resultater (FoS, deformasjon, krefter)",
         "enabled": True},
        {"id": "water_sensitivity", "name": "Vannstandssensitivitet",
         "desc": "Varier grunnvannstand og analyser effekt på sikkerhetsfaktor, deformasjon og krefter",
         "enabled": True},
        {"id": "extract_results", "name": "Uttak av spuntberegninger",
         "desc": "Hent ut resultater for kapasitetssjekk, Msf, og deformasjoner", "enabled": True},
        {"id": "optimize_depth", "name": "Optimalisering av spuntdybde",
         "desc": "Endring av underkant spunt for å optimalisere design", "enabled": False},
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

# ------------------------------------------------------------------ level 3

def _build_cross_section_figure(model, selected_spunts, selected_anchors):
    """Build a Plotly figure showing the 2D cross-section with soil layers,
    plates and anchors.  Clickable elements are highlighted."""
    import plotly.graph_objects as go

    geo       = model.get("geometry", {})
    structs   = model.get("structures", {})
    layers    = geo.get("soil_layers", [])
    water_head = geo.get("water_head")

    # Fallback extents from structural elements if geometry is missing
    plates_all = structs.get("plates", []) + structs.get("embedded_beams", [])
    anchors_all = (structs.get("node_to_node_anchors", [])
                   + structs.get("fixed_end_anchors", []))
    struct_xs = ([p.get("x1", p.get("x", 0)) for p in plates_all]
                 + [p.get("x2", p.get("x", 0)) for p in plates_all]
                 + [a.get("x1", 0) for a in anchors_all]
                 + [a.get("x2", 0) for a in anchors_all])
    struct_ys = ([p.get("y1", 0) for p in plates_all]
                 + [p.get("y2", 0) for p in plates_all]
                 + [a.get("y1", 0) for a in anchors_all]
                 + [a.get("y2", 0) for a in anchors_all])
    xmin = geo.get("xmin", min(struct_xs) if struct_xs else 0)
    xmax = geo.get("xmax", max(struct_xs) if struct_xs else 30)

    # Colour palette for soil layers (earth tones)
    layer_colors = [
        "rgba(194,178,128,0.5)",  # sand / fill
        "rgba(160,120, 80,0.5)",  # clay light
        "rgba(130,100, 70,0.5)",  # clay medium
        "rgba(110, 85, 60,0.5)",  # clay dark
        "rgba( 90, 70, 50,0.5)",  # clay deep
        "rgba(140,140,140,0.5)",  # rock
        "rgba(170,150,120,0.5)",
        "rgba(120,110,100,0.5)",
    ]

    fig = go.Figure()

    # --- Soil layers (horizontal bands as filled traces so they appear reliably) ---
    for i, layer in enumerate(layers):
        top = layer["top"]
        bot = layer["bottom"]
        colour = layer_colors[i % len(layer_colors)]
        mat_name = layer.get("material", layer["name"])
        fig.add_trace(go.Scatter(
            x=[xmin - 2, xmax + 2, xmax + 2, xmin - 2, xmin - 2],
            y=[top, top, bot, bot, top],
            fill="toself",
            fillcolor=colour,
            line=dict(color="rgba(80,60,40,0.4)", width=1),
            mode="lines",
            name=mat_name,
            text=f"{mat_name} ({top} → {bot})",
            hoverinfo="text",
            showlegend=False,
        ))
        # Label in the centre
        fig.add_annotation(
            x=(xmin + xmax) / 2, y=(top + bot) / 2,
            text=f"<b>{mat_name}</b><br>({top} → {bot})",
            showarrow=False, font=dict(size=10, color="rgba(60,40,20,0.9)"),
        )

    # --- Water level ---
    if water_head is not None:
        fig.add_shape(
            type="line",
            x0=xmin - 2, x1=xmax + 2, y0=water_head, y1=water_head,
            line=dict(color="deepskyblue", width=2, dash="dash"),
        )
        fig.add_annotation(
            x=xmin - 1, y=water_head, text=f"💧 GV {water_head}",
            showarrow=False, font=dict(size=9, color="deepskyblue"),
            xanchor="left",
        )

    # --- Plates (vertical thick lines) ---
    plates = structs.get("plates", []) + structs.get("embedded_beams", [])
    for pl in plates:
        is_sel = pl["name"] in selected_spunts
        colour = "red" if is_sel else "gray"
        width  = 5 if is_sel else 3
        fig.add_trace(go.Scatter(
            x=[pl.get("x1", pl.get("x")), pl.get("x2", pl.get("x"))],
            y=[pl.get("y1", 0), pl.get("y2", 0)],
            mode="lines+text",
            line=dict(color=colour, width=width),
            name=pl["name"],
            text=[pl["name"], ""],
            textposition="top center",
            textfont=dict(size=10, color=colour),
            hoverinfo="text",
            hovertext=f"<b>{pl['name']}</b><br>Materiale: {pl.get('material',{}).get('name','–')}<br>Lengde: {pl.get('length','–')} m",
            showlegend=False,
        ))

    # --- Anchors (horizontal / diagonal lines) ---
    all_anchors = (structs.get("node_to_node_anchors", [])
                   + structs.get("fixed_end_anchors", []))
    for anc in all_anchors:
        is_sel = anc["name"] in selected_anchors
        colour = "orangered" if is_sel else "steelblue"
        width  = 4 if is_sel else 2
        if "x1" in anc:
            fig.add_trace(go.Scatter(
                x=[anc["x1"], anc["x2"]],
                y=[anc["y1"], anc["y2"]],
                mode="lines+text",
                line=dict(color=colour, width=width, dash="dot"),
                name=anc["name"],
                text=[anc["name"], ""],
                textposition="top center",
                textfont=dict(size=9, color=colour),
                hoverinfo="text",
                hovertext=f"<b>{anc['name']}</b><br>Materiale: {anc.get('material',{}).get('name','–')}",
                showlegend=False,
            ))

    # --- Layout ---
    # Compute Y range from soil layers + structures
    all_y = [pl.get("y1", 0) for pl in plates] + [pl.get("y2", 0) for pl in plates]
    all_y += [l["top"] for l in layers] + [l["bottom"] for l in layers]
    y_lo = min(all_y) - 2 if all_y else -20
    y_hi = max(all_y) + 2 if all_y else 5

    fig.update_layout(
        height=550,
        margin=dict(l=40, r=20, t=30, b=40),
        xaxis=dict(title="x (m)", range=[xmin - 3, xmax + 3]),
        yaxis=dict(title="y (m)", range=[y_lo, y_hi], scaleanchor="x"),
        plot_bgcolor="white",
        hovermode="closest",
    )
    return fig


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

    # --- Selection mode toggle ---
    mode = st.radio(
        "Velg metode",
        ["📋 Velg fra liste", "🗺️ Velg fra snitt"],
        horizontal=True,
        key="l3_selection_mode",
    )

    if mode == "📋 Velg fra liste":
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

    else:  # Cross-section mode
        st.markdown("#### Velg elementer fra 2D-snitt")

        geo = model.get("geometry", {})
        if not geo.get("soil_layers"):
            st.warning("⚠️ Geometridata mangler. Gå tilbake til Nivå 1 og koble til Plaxis på nytt for å hente oppdatert modelldata.")
        st.caption("Valgte elementer vises i rødt. Bruk avkrysningsboksene under snittet.")

        # Checkboxes for selection (above the plot for immediate feedback)
        c_cols = st.columns(max(len(spunts) + len(anchors), 1))
        idx = 0
        for sp in spunts:
            with c_cols[idx % len(c_cols)]:
                mat_name = sp.get("material", {}).get("name", "")
                checked = st.checkbox(
                    f"🔩 {sp['name']}" + (f" ({mat_name})" if mat_name else ""),
                    value=sp["name"] in st.session_state.plaxis_selected_spunts,
                    key=f"cs_sp_{sp['name']}",
                )
                if checked and sp["name"] not in st.session_state.plaxis_selected_spunts:
                    st.session_state.plaxis_selected_spunts.append(sp["name"])
                elif not checked and sp["name"] in st.session_state.plaxis_selected_spunts:
                    st.session_state.plaxis_selected_spunts.remove(sp["name"])
            idx += 1
        for anc in anchors:
            with c_cols[idx % len(c_cols)]:
                mat_name = anc.get("material", {}).get("name", "")
                checked = st.checkbox(
                    f"⚓ {anc['name']}" + (f" ({mat_name})" if mat_name else ""),
                    value=anc["name"] in st.session_state.plaxis_selected_anchors,
                    key=f"cs_an_{anc['name']}",
                )
                if checked and anc["name"] not in st.session_state.plaxis_selected_anchors:
                    st.session_state.plaxis_selected_anchors.append(anc["name"])
                elif not checked and anc["name"] in st.session_state.plaxis_selected_anchors:
                    st.session_state.plaxis_selected_anchors.remove(anc["name"])
            idx += 1

        # Build and show cross-section figure
        fig = _build_cross_section_figure(
            model,
            st.session_state.plaxis_selected_spunts,
            st.session_state.plaxis_selected_anchors,
        )
        st.plotly_chart(fig, use_container_width=True)

        spunt_names  = st.session_state.plaxis_selected_spunts
        anchor_names = st.session_state.plaxis_selected_anchors

    st.markdown("---")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("← Forrige", use_container_width=True):
            st.session_state.plaxis_level = 2
            st.rerun()
    with c2:
        if st.button("Neste →", type="primary", use_container_width=True,
                     disabled=len(st.session_state.plaxis_selected_spunts) == 0):
            st.session_state.plaxis_level = 4
            st.rerun()


# ------------------------------------------------------------------ level 4

def show_level4():
    """Level 4: Select phases and analysis types (MSF, Ux, capacity check)."""
    import pandas as pd

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
    for ph in phases:
        if ph["name"] not in st.session_state.plaxis_selected_phases:
            st.session_state.plaxis_selected_phases[ph["name"]] = {
                "msf": False, "ux": False, "capacity": False}

    # Build dataframe for data_editor
    rows = []
    for ph in phases:
        pname = ph["name"]
        sel = st.session_state.plaxis_selected_phases[pname]
        rows.append({
            "Fase": ("🔴 " if ph.get("calc_type_id") == 7 else "🔵 ") + pname,
            "Msf":      sel["msf"],
            "Ux":       sel["ux"],
            "Kapasitet": sel["capacity"],
        })
    df = pd.DataFrame(rows)

    edited = st.data_editor(
        df,
        column_config={
            "Fase":      st.column_config.TextColumn("Fase", disabled=True),
            "Msf":       st.column_config.CheckboxColumn("Msf"),
            "Ux":        st.column_config.CheckboxColumn("Ux"),
            "Kapasitet": st.column_config.CheckboxColumn("Kapasitet"),
        },
        hide_index=True,
        use_container_width=True,
        key="phase_selector_table",
    )

    # Write edited values back to session state
    for i, ph in enumerate(phases):
        pname = ph["name"]
        st.session_state.plaxis_selected_phases[pname]["msf"]      = bool(edited.iloc[i]["Msf"])
        st.session_state.plaxis_selected_phases[pname]["ux"]       = bool(edited.iloc[i]["Ux"])
        st.session_state.plaxis_selected_phases[pname]["capacity"] = bool(edited.iloc[i]["Kapasitet"])

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
        "host":            st.session_state.plaxis_host or None,
        "input_port":      st.session_state.plaxis_port,
        "input_password":  st.session_state.plaxis_password,
        "output_port":     st.session_state.plaxis_output_port,
        "output_password": st.session_state.plaxis_output_password,
    })

    if result.get("success"):
        progress.progress(100)
        status.text("Ferdig!")
        st.success("✅ Beregning fullført!")
        if result.get("output_file"):
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


# ====================================================================
# PARAMETRIC SHEET PILE WORKFLOW  (Levels 3–5 when fn == parametric_spunt)
# ====================================================================

def show_para_level3():
    """Parametric Level 3: Configure soil parameters and spunt geometry to vary."""
    import pandas as pd

    st.markdown("### Nivå 3 – Parametrisk oppsett")
    st.caption(
        "Velg KS-jordlag, spunt(er) å variere, og hvilke faser som skal sjekkes. "
        "Plaxis kjører automatisk med ulike kombinasjoner."
    )

    model = st.session_state.plaxis_model_data
    if not model:
        st.error("Ingen modelldata tilgjengelig")
        return

    structs  = model.get("structures", {})
    phases   = model.get("phases", [])
    geo      = model.get("geometry", {})
    layers   = geo.get("soil_layers", [])
    soil_mat_names = list({l["material"] for l in layers if "material" in l})

    # ---- Section 1: KS soil selection ----
    st.markdown("---")
    st.markdown("#### 1. Velg KS-jordlag")
    st.caption("Velg laget som skal endres parametrisk (f.eks. et karakteristisk spenningsfelt).")

    ks_soil = st.selectbox(
        "KS-jordlag",
        options=soil_mat_names,
        index=(soil_mat_names.index(st.session_state.para_ks_soil)
               if st.session_state.para_ks_soil in soil_mat_names else 0),
        key="para_ks_select",
    )
    st.session_state.para_ks_soil = ks_soil

    # Show which layers use this material
    matching_layers = [l for l in layers if l.get("material") == ks_soil]
    if matching_layers:
        st.info(f"Laget brukes i: {', '.join(l['name'] + ' (' + str(l['top']) + ' → ' + str(l['bottom']) + ')' for l in matching_layers)}")

    # Parameter variations
    st.markdown("**Parametervariasjoner for KS-lag:**")
    st.caption("Definer parameterverdi-intervall som Plaxis skal iterere over.")

    params = st.session_state.para_soil_params
    if "su_values" not in params:
        params["su_values"] = "10, 15, 20, 25"
    if "gamma_values" not in params:
        params["gamma_values"] = ""

    params["su_values"] = st.text_input(
        "Su-verdier (kPa) — komma-separert",
        value=params["su_values"],
        help="Udrenert skjærstyrke — f.eks. '10, 15, 20, 25'",
    )
    params["gamma_values"] = st.text_input(
        "γ'-verdier (kN/m³) — valgfritt, komma-separert",
        value=params.get("gamma_values", ""),
        help="Effektiv tyngdetetthet — la stå tom for å beholde eksisterende",
    )

    # ---- Section 2: Spunt selection and depth range ----
    st.markdown("---")
    st.markdown("#### 2. Spunt — velg element og dybdevariasjon")

    plates = structs.get("plates", []) + structs.get("embedded_beams", [])
    plate_names = [p["name"] for p in plates]

    sel_plate = st.selectbox(
        "Spunt som skal varieres",
        options=plate_names,
        index=(plate_names.index(st.session_state.para_spunt_plate)
               if st.session_state.para_spunt_plate in plate_names else 0),
        key="para_plate_select",
    )
    st.session_state.para_spunt_plate = sel_plate

    # Show current plate geometry
    plate_info = next((p for p in plates if p["name"] == sel_plate), None)
    if plate_info:
        y_top = plate_info.get("y1", 0)
        y_bot = plate_info.get("y2", 0)
        length = plate_info.get("length", abs(y_top - y_bot))
        st.info(f"Nåværende: topp = {y_top} m, bunn = {y_bot} m, lengde = {length} m")

        rng = st.session_state.para_spunt_range
        if "enabled" not in rng:
            rng["enabled"] = False
            rng["min_y"] = y_bot
            rng["max_y"] = y_bot - 3
            rng["step"]  = 1.0

        rng["enabled"] = st.checkbox("Varier spuntdybde", value=rng["enabled"])
        if rng["enabled"]:
            c1, c2, c3 = st.columns(3)
            with c1:
                rng["min_y"] = st.number_input(
                    "Minste bunn-kote (m)", value=float(rng["min_y"]), step=0.5, format="%.1f")
            with c2:
                rng["max_y"] = st.number_input(
                    "Dypeste bunn-kote (m)", value=float(rng["max_y"]), step=0.5, format="%.1f")
            with c3:
                rng["step"] = st.number_input(
                    "Steg (m)", value=float(rng["step"]), min_value=0.5, step=0.5, format="%.1f")

    # ---- Section 3: Phase selection ----
    st.markdown("---")
    st.markdown("#### 3. Faser å evaluere")

    pc = st.session_state.para_phases_config
    if not pc:
        pc["fos_phase"] = None
        pc["disp_phase"] = None
        pc["cap_phase"]  = None

    phase_names = [p["name"] for p in phases]
    fos_phases = [p["name"] for p in phases if p.get("calc_type_id") == 7]

    pc["fos_phase"] = st.selectbox(
        "🔴 FoS-fase (sikkerhetsfaktor)",
        options=fos_phases if fos_phases else phase_names,
        index=0,
        key="para_fos_phase",
    )
    pc["disp_phase"] = st.selectbox(
        "📏 Deformasjonsfase (maks Ux)",
        options=phase_names,
        index=min(len(phase_names) - 1, len(phase_names) - 2) if len(phase_names) > 1 else 0,
        key="para_disp_phase",
    )
    pc["cap_phase"] = st.selectbox(
        "💪 Kapasitetsfase (maks krefter)",
        options=phase_names,
        index=min(len(phase_names) - 1, len(phase_names) - 2) if len(phase_names) > 1 else 0,
        key="para_cap_phase",
    )

    # ---- Summary ----
    st.markdown("---")
    st.markdown("#### Oppsummering")
    su_vals = [v.strip() for v in params.get("su_values", "").split(",") if v.strip()]
    n_su = len(su_vals)

    if rng.get("enabled") and rng["step"] > 0:
        import math
        n_depth = int(abs(rng["max_y"] - rng["min_y"]) / rng["step"]) + 1
    else:
        n_depth = 1

    n_combos = n_su * n_depth
    st.write(f"**{n_su}** Su-verdier × **{n_depth}** dybdevariasjoner = **{n_combos}** beregningskjøringer")
    if n_combos > 50:
        st.warning("⚠️ Mange kjøringer — dette kan ta lang tid!")

    # ---- Navigation ----
    st.markdown("---")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("← Forrige", use_container_width=True):
            st.session_state.plaxis_level = 2
            st.rerun()
    with c2:
        can_proceed = n_su > 0 and sel_plate
        if st.button("Neste → Kjør beregninger", type="primary",
                     use_container_width=True, disabled=not can_proceed):
            st.session_state.plaxis_level = 4
            st.rerun()


def show_para_level4():
    """Parametric Level 4: Run the parametric study."""
    st.markdown("### Nivå 4 – Kjør parametrisk studie")

    params = st.session_state.para_soil_params
    rng    = st.session_state.para_spunt_range
    pc     = st.session_state.para_phases_config

    su_vals = [float(v.strip()) for v in params.get("su_values", "").split(",") if v.strip()]
    gamma_vals = [float(v.strip()) for v in params.get("gamma_values", "").split(",") if v.strip()] or [None]

    if rng.get("enabled") and rng["step"] > 0:
        import numpy as np
        depth_vals = list(np.arange(
            float(rng["min_y"]),
            float(rng["max_y"]) - 0.01,
            -abs(float(rng["step"])),
        ))
        if not depth_vals:
            depth_vals = [float(rng["min_y"])]
    else:
        depth_vals = [None]  # None = keep original

    combos = []
    for su in su_vals:
        for depth in depth_vals:
            combos.append({"su": su, "depth": depth})

    st.write(f"**Antall beregninger:** {len(combos)}")

    # Show the run matrix
    import pandas as pd
    df_combos = pd.DataFrame(combos)
    df_combos.columns = ["Su (kPa)"] + (["Bunn-kote (m)"] if depth_vals != [None] else [])
    st.dataframe(df_combos, hide_index=True, use_container_width=True)

    st.markdown("---")

    c1, c2 = st.columns(2)
    with c1:
        if st.button("← Forrige", use_container_width=True):
            st.session_state.plaxis_level = 3
            st.rerun()
    with c2:
        if st.button("🚀 Start parametrisk beregning", type="primary", use_container_width=True):
            _run_parametric_study(combos, pc)


def _run_parametric_study(combos, phases_config):
    """Execute the parametric study — each combo modifies the model, calculates, and extracts results."""
    progress = st.progress(0)
    status   = st.empty()
    results  = []

    for i, combo in enumerate(combos):
        pct = int((i / len(combos)) * 100)
        progress.progress(pct)
        su = combo["su"]
        depth = combo.get("depth")
        depth_label = f", bunn={depth} m" if depth is not None else ""
        status.text(f"Kjører beregning {i+1}/{len(combos)}: Su={su} kPa{depth_label}...")

        payload = {
            "session_id":    st.session_state.get("username", "default"),
            "ks_soil":       st.session_state.para_ks_soil,
            "plate":         st.session_state.para_spunt_plate,
            "su":            su,
            "depth":         depth,
            "fos_phase":     phases_config.get("fos_phase"),
            "disp_phase":    phases_config.get("disp_phase"),
            "cap_phase":     phases_config.get("cap_phase"),
            "host":          st.session_state.plaxis_host or None,
            "input_port":    st.session_state.plaxis_port,
            "input_password": st.session_state.plaxis_password,
            "output_port":   st.session_state.plaxis_output_port,
            "output_password": st.session_state.plaxis_output_password,
        }

        try:
            result = api.plaxis_parametric_run(payload)
        except Exception:
            result = {"success": False, "error": "Endepunkt ikke tilgjengelig ennå"}

        row = {"Su (kPa)": su}
        if depth is not None:
            row["Bunn-kote (m)"] = depth
        row["FoS"]        = result.get("msf", "–")
        row["Ux_max (mm)"] = result.get("ux_max", "–")
        row["M_max (kNm/m)"] = result.get("m_max", "–")
        row["Status"]     = "✅" if result.get("success") else f"❌ {result.get('error', '')}"
        results.append(row)

    progress.progress(100)
    status.text("Ferdig!")
    st.session_state.para_results = results
    st.session_state.plaxis_level = 5
    st.rerun()


# --------------------------------------------------------- save / load helpers

def _show_save_button(calc_type: str, activity_name: str, config: dict, results: list, key_prefix: str):
    """Show a 'Lagre beregning' button and handle saving to the database."""
    save_key = f"{key_prefix}_saved_id"

    if st.session_state.get(save_key):
        st.success(f"✅ Beregning lagret (ID: {st.session_state[save_key]})")
        return

    name = st.text_input(
        "Beregningsnavn",
        value=activity_name,
        key=f"{key_prefix}_save_name",
    )
    if st.button("💾 Lagre beregning", type="primary", key=f"{key_prefix}_save_btn"):
        proj = st.session_state.selected_project
        payload = {
            "activity_name": name,
            "username":      st.session_state.get("username", "default"),
            "project_id":    proj.get("id") if proj else None,
            "calc_type":     calc_type,
            "config":        config,
            "results":       results,
            "input_port":    st.session_state.plaxis_port,
            "output_port":   st.session_state.plaxis_output_port,
        }
        try:
            resp = api.save_plaxis_calculation(payload)
            if resp.get("success"):
                st.session_state[save_key] = resp.get("calculation_id")
                st.rerun()
            else:
                st.error(f"Kunne ikke lagre: {resp.get('error')}")
        except Exception as exc:
            st.error(f"Feil ved lagring: {exc}")


def _show_ai_report_button(calc_type: str, config: dict, results: list, key_prefix: str):
    """Show AI report generation button on Level 5."""
    st.markdown("#### 🤖 AI-beregningsrapport")
    st.caption("Generer en profesjonell geoteknisk rapport basert på resultatene.")

    if st.button("📝 Generer AI-rapport", use_container_width=True, key=f"{key_prefix}_ai_rpt_btn"):
        with st.spinner("AI genererer rapport..."):
            model = st.session_state.plaxis_model_data or {}
            payload = {
                "calc_type":  calc_type,
                "config":     config,
                "results":    results,
                "model_data": {
                    "structures": model.get("structures", {}),
                    "geometry":   model.get("geometry", {}),
                    "phases":     model.get("phases", []),
                },
            }
            resp = api.plaxis_ai_report(payload)
            if resp.get("success"):
                st.session_state[f"_{key_prefix}_ai_report"] = resp.get("report", "")
            else:
                st.error(f"AI-feil: {resp.get('error')}")

    report = st.session_state.get(f"_{key_prefix}_ai_report")
    if report:
        with st.expander("📄 AI-beregningsrapport", expanded=True):
            st.markdown(report)


def _show_saved_calculations():
    """Show a list of saved calculations with an option to reload/re-run them."""
    import pandas as pd

    proj = st.session_state.selected_project
    project_id = proj.get("id") if proj else None
    try:
        calcs = api.get_plaxis_calculations(project_id=project_id, limit=20)
    except Exception:
        calcs = []

    if not calcs:
        return

    st.markdown("---")
    st.markdown("#### 📋 Lagrede beregninger")

    for calc in calcs:
        calc_id = calc.get("id")
        name    = calc.get("activity_name", "Ukjent")
        status  = calc.get("status", "?")
        ts      = calc.get("completed_at", calc.get("started_at", ""))
        if ts:
            ts = ts[:16].replace("T", " ")

        res_data = calc.get("results") or {}
        calc_type = res_data.get("calc_type", "unknown")
        config    = res_data.get("config", {})
        rows      = res_data.get("rows", [])

        type_labels = {
            "parametric_spunt": "Parametrisk spunt",
            "water_sensitivity": "Vannstand",
            "extract_results": "Resultatuttak",
        }
        type_label = type_labels.get(calc_type, calc_type)

        with st.expander(f"**{name}** — {type_label} ({ts})", expanded=False):
            st.caption(f"ID: {calc_id} | Status: {status}")

            if rows:
                df = pd.DataFrame(rows)
                st.dataframe(df, hide_index=True, use_container_width=True)

            # Show config summary
            if config:
                with st.popover("Vis konfigurasjon"):
                    st.json(config)

            # Re-run button — loads config back into session state
            if st.button("🔄 Kjør på nytt", key=f"rerun_{calc_id}"):
                _reload_calculation(calc_type, config, rows)


def _reload_calculation(calc_type: str, config: dict, rows: list):
    """Reload a saved calculation's config into session state and jump to its Level 3."""
    st.session_state.plaxis_selected_function = calc_type

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

    st.session_state.plaxis_level = 3
    st.rerun()


def show_para_level5():
    """Parametric Level 5: Display results in a comparison table and charts."""
    import pandas as pd

    st.markdown("### Nivå 5 – Parametriske resultater")

    results = st.session_state.para_results
    if not results:
        st.info("Ingen resultater ennå. Gå tilbake og kjør beregningen.")
        if st.button("← Tilbake"):
            st.session_state.plaxis_level = 4
            st.rerun()
        return

    df = pd.DataFrame(results)
    st.markdown("#### Resultatoversikt")
    st.dataframe(df, hide_index=True, use_container_width=True)

    # Charts
    numeric_cols = [c for c in ["FoS", "Ux_max (mm)", "M_max (kNm/m)"] if c in df.columns]
    has_depth = "Bunn-kote (m)" in df.columns

    for col in numeric_cols:
        # Convert to numeric, skip non-numeric
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df_valid = df.dropna(subset=[c for c in numeric_cols if c in df.columns])

    if not df_valid.empty:
        import plotly.express as px

        st.markdown("---")
        st.markdown("#### Grafer")

        if has_depth and "FoS" in df_valid.columns:
            fig = px.scatter(
                df_valid, x="Su (kPa)", y="FoS", color="Bunn-kote (m)",
                title="Sikkerhetsfaktor vs. Su og Spuntdybde",
                labels={"FoS": "FoS (Msf)"},
            )
            fig.add_hline(y=1.4, line_dash="dash", line_color="red",
                          annotation_text="FoS krav = 1.4")
            st.plotly_chart(fig, use_container_width=True)

        elif "FoS" in df_valid.columns:
            fig = px.line(
                df_valid, x="Su (kPa)", y="FoS",
                title="Sikkerhetsfaktor vs. Su",
                markers=True,
            )
            fig.add_hline(y=1.4, line_dash="dash", line_color="red",
                          annotation_text="FoS krav = 1.4")
            st.plotly_chart(fig, use_container_width=True)

        if "Ux_max (mm)" in df_valid.columns:
            fig2 = px.line(
                df_valid, x="Su (kPa)", y="Ux_max (mm)",
                color="Bunn-kote (m)" if has_depth else None,
                title="Maks horisontal deformasjon vs. Su",
                markers=True,
            )
            st.plotly_chart(fig2, use_container_width=True)

        if "M_max (kNm/m)" in df_valid.columns:
            fig3 = px.line(
                df_valid, x="Su (kPa)", y="M_max (kNm/m)",
                color="Bunn-kote (m)" if has_depth else None,
                title="Maks moment vs. Su",
                markers=True,
            )
            st.plotly_chart(fig3, use_container_width=True)

    # AI Report
    st.markdown("---")
    _show_ai_report_button(
        calc_type="parametric_spunt",
        config={
            "ks_soil": st.session_state.para_ks_soil,
            "plate": st.session_state.para_spunt_plate,
            "su_values": st.session_state.para_soil_params.get("su_values", ""),
            "gamma_values": st.session_state.para_soil_params.get("gamma_values", ""),
            "spunt_range": st.session_state.para_spunt_range,
            "phases": st.session_state.para_phases_config,
        },
        results=results,
        key_prefix="para",
    )

    # Save calculation
    st.markdown("---")
    _show_save_button(
        calc_type="parametric_spunt",
        activity_name="Parametrisk spuntberegning",
        config={
            "ks_soil": st.session_state.para_ks_soil,
            "plate": st.session_state.para_spunt_plate,
            "su_values": st.session_state.para_soil_params.get("su_values", ""),
            "gamma_values": st.session_state.para_soil_params.get("gamma_values", ""),
            "spunt_range": st.session_state.para_spunt_range,
            "phases": st.session_state.para_phases_config,
        },
        results=results,
        key_prefix="para",
    )

    # Navigation
    st.markdown("---")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("← Endre parametere", use_container_width=True):
            st.session_state.plaxis_level = 3
            st.rerun()
    with c2:
        if st.button("🔄 Kjør på nytt", use_container_width=True):
            st.session_state.para_results = None
            st.session_state.plaxis_level = 4
            st.rerun()


# -------------------------------------------------------- water sensitivity UI

def show_ws_level3():
    """Water Sensitivity Level 3: Configure water levels and plate to evaluate."""
    st.markdown("### Nivå 3 – Vannstandssensitivitet — oppsett")
    st.caption(
        "Definer vannstandsintervall og velg spunt og faser som skal evalueres. "
        "Plaxis endrer grunnvannstand trinnvis og beregner for hvert nivå."
    )

    model = st.session_state.plaxis_model_data
    if not model:
        st.error("Ingen modelldata tilgjengelig")
        return

    structs = model.get("structures", {})
    phases  = model.get("phases", [])
    geo     = model.get("geometry", {})

    current_wh = geo.get("water_head", 0)
    ymax = geo.get("ymax", 3.0)
    ymin = geo.get("ymin", -15.0)

    # Apply any value generated by the interval tab BEFORE widgets are rendered.
    # (Streamlit forbids writing to a keyed widget's state after instantiation.)
    if "_ws_pending_values" in st.session_state:
        st.session_state.ws_water_values = st.session_state.pop("_ws_pending_values")

    # ---- Section 1: Water level range ----
    st.markdown("---")
    st.markdown("#### 1. Vannstandsverdier")
    st.caption(
        f"Nåværende grunnvannstand i modellen: **{current_wh} m**. "
        "Angi verdier som komma-separert liste, eller bruk intervall-generatoren."
    )

    tab_manual, tab_range = st.tabs(["Manuell liste", "Intervall"])

    with tab_manual:
        # No key= so that value= is always respected (avoids Streamlit keyed-widget
        # restriction where value= is ignored after first render).
        entered = st.text_input(
            "Vannstandsverdier (m) — komma-separert",
            value=st.session_state.ws_water_values or f"{current_wh}",
            help="F.eks. '-1, 0, 0.5, 1.0, 1.5, 2.0, 2.5'",
        )
        st.session_state.ws_water_values = entered

    with tab_range:
        c1, c2, c3 = st.columns(3)
        with c1:
            wl_min = st.number_input("Fra (m)", value=float(ymin / 2), step=0.5, format="%.1f", key="ws_wl_min")
        with c2:
            wl_max = st.number_input("Til (m)", value=float(ymax), step=0.5, format="%.1f", key="ws_wl_max")
        with c3:
            wl_step = st.number_input("Steg (m)", value=0.5, min_value=0.1, step=0.1, format="%.1f", key="ws_wl_step")

        if st.button("Generer verdier", key="ws_generate"):
            import numpy as np
            vals = list(np.arange(wl_min, wl_max + wl_step * 0.01, wl_step))
            # Store in a pending key — applied at the TOP of the next render,
            # before the text_input widget is instantiated (Streamlit requirement).
            st.session_state["_ws_pending_values"] = ", ".join(f"{v:.1f}" for v in vals)
            st.rerun()

    # Parse values for preview
    wl_vals = [
        v.strip()
        for v in st.session_state.ws_water_values.split(",")
        if v.strip()
    ]
    n_wl = len(wl_vals)
    if n_wl > 0:
        st.info(f"**{n_wl}** vannstandsnivåer: {', '.join(wl_vals)} m")

    # ---- Section 2: Plate selection ----
    st.markdown("---")
    st.markdown("#### 2. Velg spunt å evaluere")

    plates = structs.get("plates", []) + structs.get("embedded_beams", [])
    plate_names = [p["name"] for p in plates]

    sel_plate = st.selectbox(
        "Spunt",
        options=plate_names,
        index=(plate_names.index(st.session_state.ws_plate)
               if st.session_state.ws_plate in plate_names else 0),
        key="ws_plate_select",
    )
    st.session_state.ws_plate = sel_plate

    # ---- Section 3: Phase selection ----
    st.markdown("---")
    st.markdown("#### 3. Faser å evaluere")

    pc = st.session_state.ws_phases_config
    if not pc:
        pc["fos_phase"] = None
        pc["disp_phase"] = None
        pc["cap_phase"] = None

    phase_names = [p["name"] for p in phases]
    fos_phases = [p["name"] for p in phases if p.get("calc_type_id") == 7]

    pc["fos_phase"] = st.selectbox(
        "🔴 FoS-fase (sikkerhetsfaktor)",
        options=fos_phases if fos_phases else phase_names,
        index=0,
        key="ws_fos_phase",
    )
    pc["disp_phase"] = st.selectbox(
        "📏 Deformasjonsfase (maks Ux)",
        options=phase_names,
        index=min(len(phase_names) - 1, len(phase_names) - 2) if len(phase_names) > 1 else 0,
        key="ws_disp_phase",
    )
    pc["cap_phase"] = st.selectbox(
        "💪 Kapasitetsfase (maks moment)",
        options=phase_names,
        index=min(len(phase_names) - 1, len(phase_names) - 2) if len(phase_names) > 1 else 0,
        key="ws_cap_phase",
    )

    # ---- Summary ----
    st.markdown("---")
    st.markdown("#### Oppsummering")
    st.write(f"**{n_wl}** vannstandsnivåer × **1** spunt = **{n_wl}** beregningskjøringer")
    if n_wl > 20:
        st.warning("⚠️ Mange kjøringer — dette kan ta lang tid!")

    # ---- Navigation ----
    st.markdown("---")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("← Forrige", use_container_width=True, key="ws3_back"):
            st.session_state.plaxis_level = 2
            st.rerun()
    with c2:
        can_proceed = n_wl > 0 and sel_plate
        if st.button("Neste → Kjør beregninger", type="primary",
                     use_container_width=True, disabled=not can_proceed, key="ws3_next"):
            st.session_state.plaxis_level = 4
            st.rerun()


def show_ws_level4():
    """Water Sensitivity Level 4: Run the water-level study."""
    st.markdown("### Nivå 4 – Kjør vannstandssensitivitet")

    wl_vals = [
        float(v.strip())
        for v in st.session_state.ws_water_values.split(",")
        if v.strip()
    ]
    pc = st.session_state.ws_phases_config

    st.write(f"**Antall beregninger:** {len(wl_vals)}")

    import pandas as pd
    df_preview = pd.DataFrame({"Vannstand (m)": wl_vals})
    st.dataframe(df_preview, hide_index=True, use_container_width=True)

    st.markdown("---")

    c1, c2 = st.columns(2)
    with c1:
        if st.button("← Forrige", use_container_width=True, key="ws4_back"):
            st.session_state.plaxis_level = 3
            st.rerun()
    with c2:
        if st.button("🚀 Start vannstandsanalyse", type="primary",
                     use_container_width=True, key="ws4_run"):
            _run_water_sensitivity(wl_vals, pc)


def _run_water_sensitivity(wl_vals, phases_config):
    """Execute the water-level sensitivity study."""
    progress = st.progress(0)
    status   = st.empty()
    results  = []

    for i, wl in enumerate(wl_vals):
        pct = int((i / len(wl_vals)) * 100)
        progress.progress(pct)
        status.text(f"Kjører beregning {i+1}/{len(wl_vals)}: vannstand = {wl} m ...")

        payload = {
            "session_id":      st.session_state.get("username", "default"),
            "water_level":     wl,
            "plate":           st.session_state.ws_plate,
            "fos_phase":       phases_config.get("fos_phase"),
            "disp_phase":      phases_config.get("disp_phase"),
            "cap_phase":       phases_config.get("cap_phase"),
            "host":            st.session_state.plaxis_host or None,
            "output_port":     st.session_state.plaxis_output_port,
            "output_password": st.session_state.plaxis_output_password,
        }

        try:
            result = api.plaxis_water_sensitivity_run(payload)
        except Exception:
            result = {"success": False, "error": "Endepunkt ikke tilgjengelig ennå"}

        row = {
            "Vannstand (m)":   wl,
            "FoS":             result.get("msf", "–"),
            "Ux_max (mm)":     result.get("ux_max", "–"),
            "M_max (kNm/m)":   result.get("m_max", "–"),
            "Status":          "✅" if result.get("success") else f"❌ {result.get('error', '')}",
        }
        results.append(row)

    progress.progress(100)
    status.text("Ferdig!")
    st.session_state.ws_results = results
    st.session_state.plaxis_level = 5
    st.rerun()


def show_ws_level5():
    """Water Sensitivity Level 5: Display results."""
    import pandas as pd

    st.markdown("### Nivå 5 – Vannstandssensitivitet — resultater")

    results = st.session_state.ws_results
    if not results:
        st.info("Ingen resultater ennå. Gå tilbake og kjør beregningen.")
        if st.button("← Tilbake", key="ws5_empty_back"):
            st.session_state.plaxis_level = 4
            st.rerun()
        return

    df = pd.DataFrame(results)
    st.markdown("#### Resultatoversikt")
    st.dataframe(df, hide_index=True, use_container_width=True)

    # Charts
    numeric_cols = ["FoS", "Ux_max (mm)", "M_max (kNm/m)"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df_valid = df.dropna(subset=[c for c in numeric_cols if c in df.columns])

    if not df_valid.empty:
        import plotly.express as px
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots

        st.markdown("---")
        st.markdown("#### Grafer")

        # Combined subplot figure
        fig = make_subplots(
            rows=3, cols=1,
            subplot_titles=("Sikkerhetsfaktor (FoS)", "Maks deformasjon Ux", "Maks moment M"),
            shared_xaxes=True,
            vertical_spacing=0.08,
        )

        x = df_valid["Vannstand (m)"]

        if "FoS" in df_valid.columns:
            fig.add_trace(
                go.Scatter(x=x, y=df_valid["FoS"], mode="lines+markers",
                           name="FoS", line=dict(color="#EF553B")),
                row=1, col=1,
            )
            fig.add_hline(y=1.4, line_dash="dash", line_color="red",
                          annotation_text="FoS krav = 1.4", row=1, col=1)

        if "Ux_max (mm)" in df_valid.columns:
            fig.add_trace(
                go.Scatter(x=x, y=df_valid["Ux_max (mm)"], mode="lines+markers",
                           name="Ux_max (mm)", line=dict(color="#636EFA")),
                row=2, col=1,
            )

        if "M_max (kNm/m)" in df_valid.columns:
            fig.add_trace(
                go.Scatter(x=x, y=df_valid["M_max (kNm/m)"], mode="lines+markers",
                           name="M_max (kNm/m)", line=dict(color="#00CC96")),
                row=3, col=1,
            )

        fig.update_xaxes(title_text="Vannstand (m)", row=3, col=1)
        fig.update_yaxes(title_text="FoS (Msf)", row=1, col=1)
        fig.update_yaxes(title_text="Ux (mm)", row=2, col=1)
        fig.update_yaxes(title_text="M (kNm/m)", row=3, col=1)
        fig.update_layout(height=800, showlegend=False)

        st.plotly_chart(fig, use_container_width=True)

        # Also individual line charts for clarity
        if "FoS" in df_valid.columns:
            geo = st.session_state.plaxis_model_data.get("geometry", {})
            current_wh = geo.get("water_head")
            fig_fos = px.line(
                df_valid, x="Vannstand (m)", y="FoS",
                title="Sikkerhetsfaktor vs. Vannstand",
                markers=True,
            )
            fig_fos.add_hline(y=1.4, line_dash="dash", line_color="red",
                              annotation_text="FoS krav = 1.4")
            if current_wh is not None:
                fig_fos.add_vline(x=current_wh, line_dash="dot", line_color="deepskyblue",
                                  annotation_text=f"Nåværende GV = {current_wh} m")
            st.plotly_chart(fig_fos, use_container_width=True)

    # AI Report
    st.markdown("---")
    _show_ai_report_button(
        calc_type="water_sensitivity",
        config={
            "water_values": st.session_state.ws_water_values,
            "plate": st.session_state.ws_plate,
            "phases": st.session_state.ws_phases_config,
        },
        results=results,
        key_prefix="ws",
    )

    # Save calculation
    st.markdown("---")
    _show_save_button(
        calc_type="water_sensitivity",
        activity_name="Vannstandssensitivitet",
        config={
            "water_values": st.session_state.ws_water_values,
            "plate": st.session_state.ws_plate,
            "phases": st.session_state.ws_phases_config,
        },
        results=results,
        key_prefix="ws",
    )

    # Navigation
    st.markdown("---")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("← Endre parametere", use_container_width=True, key="ws5_back"):
            st.session_state.plaxis_level = 3
            st.rerun()
    with c2:
        if st.button("🔄 Kjør på nytt", use_container_width=True, key="ws5_rerun"):
            st.session_state.ws_results = None
            st.session_state.plaxis_level = 4
            st.rerun()


# ----------------------------------------------------------------------- page

def main():
    st.markdown("# 🔧 Plaxis Automatisering")

    proj = st.session_state.selected_project
    back_label = f"← Tilbake til {proj['name']}" if proj else "← Tilbake til hjem"
    if st.button(back_label):
        st.session_state.plaxis_level      = 1
        st.session_state.plaxis_connected  = False
        st.session_state.plaxis_model_data = None
        st.switch_page("pages/home.py")

    fn = st.session_state.plaxis_selected_function
    current = st.session_state.plaxis_level

    # Progress indicator — labels depend on chosen function
    if fn == "parametric_spunt":
        levels = ["1. Tilkobling", "2. Funksjon", "3. Parametere", "4. Kjør", "5. Resultater"]
    elif fn == "water_sensitivity":
        levels = ["1. Tilkobling", "2. Funksjon", "3. Vannstand", "4. Kjør", "5. Resultater"]
    else:
        levels = ["1. Tilkobling", "2. Funksjon", "3. Spunt/Ankere", "4. Faser", "5. Output"]

    cols = st.columns(5)
    for i, (col, name) in enumerate(zip(cols, levels)):
        with col:
            if i + 1 < current:    st.success(f"✓ {name}")
            elif i + 1 == current: st.info(f"→ {name}")
            else:                  st.caption(name)
    st.markdown("---")

    if   current == 1: show_level1()
    elif current == 2: show_level2()
    elif current >= 3 and fn == "parametric_spunt":
        if   current == 3: show_para_level3()
        elif current == 4: show_para_level4()
        elif current == 5: show_para_level5()
    elif current >= 3 and fn == "water_sensitivity":
        if   current == 3: show_ws_level3()
        elif current == 4: show_ws_level4()
        elif current == 5: show_ws_level5()
    else:
        if   current == 3: show_level3()
        elif current == 4: show_level4()
        elif current == 5: show_level5()


main()
