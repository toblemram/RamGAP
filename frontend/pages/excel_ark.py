# -*- coding: utf-8 -*-
"""Excel-ark — standardiserte beregningsark."""

from __future__ import annotations

from typing import Any
import math
import os
import sys

import altair as alt
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# ---------------------------------------------------------------------------
# Ensure frontend/ is importable
# ---------------------------------------------------------------------------
_FRONTEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _FRONTEND_DIR not in sys.path:
    sys.path.insert(0, _FRONTEND_DIR)

from components.torrmur.engine import inputs_from_cell_dict, calculate, TorrmurResult
from components.live_slider_component import live_slider as _live_slider


# ===================================================================
# Available calculation sheets
# ===================================================================
CALC_SHEETS = [
    {
        "id": "torrmur",
        "name": "Dimensjonering av tørrmur",
        "icon": "🧱",
        "description": "Beregning av tørrmur iht. V220 kap. 10.3",
    },
]

# ===================================================================
# Page header + sheet selector
# ===================================================================
st.title("📊 Excel-ark")

# ---------------------------------------------------------------------------
# Tørrmur — full implementation (defined before routing logic)
# ---------------------------------------------------------------------------

INPUT_SECTIONS = [
    {
        "title": "Laster",
        "fields": [
            {"cell": "B4", "label": "Nyttelast bak mur, qk 1)", "unit": "kPa", "kind": "number", "default": 5.0},
            {"cell": "B5", "label": "Boggilast bak mur, qQk 2)", "unit": "kPa", "kind": "number", "default": 16.8},
            {"cell": "B6", "label": "Lastfaktor, γQ nyttelast", "unit": "", "kind": "number", "default": 1.3},
            {"cell": "C6", "label": "Lastfaktor, γQ boggilast", "unit": "", "kind": "number", "default": 1.15},
            {"cell": "B7", "label": "Helning bak mur, 1/tan β", "unit": "", "kind": "number", "default": 1.80},
            {"cell": "B8", "label": "Horisontallast topp mur, PH", "unit": "kN/m", "kind": "number", "default": 2.0},
            {"cell": "B9", "label": "Vertikallast topp mur, PV", "unit": "kN/m", "kind": "number", "default": 0.0},
            {"cell": "B10", "label": "Høyde over mur for horisontal kraft, yp", "unit": "m", "kind": "number", "default": 0.0},
            {"cell": "B11", "label": "Avstand fra murfront for vertikal kraft, xp", "unit": "m", "kind": "number", "default": 0.0},
            {"cell": "B12", "label": "Spesifikk tyngdetetthet mur, γmur", "unit": "kN/m³", "kind": "number", "default": 23.0},
        ],
    },
    {
        "title": "Jordparametre",
        "fields": [
            {"cell": "H5", "label": "Friksjonsvinkel, φbak", "unit": "°", "kind": "number", "default": 42.0},
            {"cell": "H6", "label": "Attraksjon, abak/ae,bak", "unit": "kPa", "kind": "number", "default": 0.0},
            {"cell": "H7", "label": "Spesifikk tyngdetetthet, γ'bak", "unit": "kN/m³", "kind": "number", "default": 19.0},
            {"cell": "H9", "label": "Friksjonsvinkel, φunder/foran", "unit": "°", "kind": "number", "default": 37.0},
            {"cell": "H10", "label": "Attraksjon, aunder/foran", "unit": "kPa", "kind": "number", "default": 9.0},
            {"cell": "H11", "label": "Spesifikk tyngdetetthet under mur, γ'under", "unit": "kN/m³", "kind": "number", "default": 9.0},
            {"cell": "H12", "label": "Spesifikk tyngdetetthet foran mur, γ'foran", "unit": "kN/m³", "kind": "number", "default": 19.0},
        ],
    },
    {
        "title": "Dimensjoner mur",
        "fields": [
            {"cell": "B14", "label": "Murhøyde, H", "unit": "m", "kind": "number", "default": 4.0},
            {"cell": "B15", "label": "Fotdybde, D", "unit": "m", "kind": "number", "default": 0.5},
            {"cell": "B16", "label": "Murbredde ved bunn, bb", "unit": "m", "kind": "number", "default": 2.2},
            {"cell": "B17", "label": "Støpt såle 3)", "unit": "", "kind": "choice", "default": "Nei", "options": ["Ja", "Nei"]},
            {"cell": "B18", "label": "Tillegg i murbredde ved bunn, bx", "unit": "m", "kind": "number", "default": 0.0},
            {"cell": "B19", "label": "Murbredde ved topp, bt", "unit": "m", "kind": "number", "default": 2.2},
            {"cell": "B20", "label": "Murens helning, d", "unit": "", "kind": "number", "default": 5.0},
            {"cell": "B21", "label": "Terrenghelning foran mur, 1/tan α", "unit": "", "kind": "number", "default": 0.0},
            {"cell": "B22", "label": "Ruhet bak muren, rv", "unit": "", "kind": "number", "default": 0.3},
        ],
    },
    {
        "title": "Beregning",
        "fields": [
            {"cell": "B24", "label": "Materialfaktor, γm", "unit": "", "kind": "number", "default": 1.40},
            {"cell": "B25", "label": "Inkludere jordsug ved β>0 4)", "unit": "", "kind": "choice", "default": "Nei", "options": ["Ja", "Nei"]},
        ],
    },
]

SUMMARY_SECTIONS = [
    {
        "title": "Jordtrykk og laster",
        "rows": [
            {"label": "Mob. friksjonsvinkel under mur, tan ρunder", "cell": "B26", "unit": ""},
            {"label": "Mob. friksjonsvinkel bak mur, tan ρbak", "cell": "B27", "unit": ""},
            {"label": "Hellende terreng bak mur, s", "cell": "B28", "unit": ""},
            {"label": "Hellende terreng bak mur, t", "cell": "B29", "unit": ""},
            {"label": "Helning bakkant mur, db", "cell": "B30", "unit": ""},
            {"label": "Helning mur for Kδ-beregning, δ", "cell": "B31", "unit": ""},
            {"label": "Jordtrykkskoeffisient, KA", "cell": "B35", "unit": ""},
            {"label": "Korrigert jordtrykkskoeffisient, KA,korr", "cell": "B36", "unit": ""},
            {"label": "Korreksjon for hellende vegg, Kδ", "cell": "B37", "unit": ""},
            {"label": "Jordtrykksresultant, EA", "cell": "B38", "unit": "kN"},
            {"label": "Vertikal skjærkraft, T", "cell": "B39", "unit": "kN"},
            {"label": "Egenvekt mur, GV", "cell": "B40", "unit": "kN"},
            {"label": "Total vertikalresultant, RV", "cell": "B41", "unit": "kN"},
            {"label": "Total horisontalresultant, RH", "cell": "B42", "unit": "kN"},
            {"label": "Momentarm for jordtrykksresultant, c1", "cell": "B43", "unit": "m"},
            {"label": "Momentarm for skjærkraft, c2", "cell": "B44", "unit": "m"},
            {"label": "Momentarm for egenvekt mur, c3", "cell": "B45", "unit": "m"},
            {"label": "Momentarm for vertikalresultant, c4", "cell": "B46", "unit": "m"},
            {"label": "Momentarm for horisontalresultant, cH", "cell": "B47", "unit": "m"},
        ],
        "messages": ["A33", "A34"],
    },
    {
        "title": "Bæreevne",
        "rows": [
            {"label": "Vertikalresultantens eksentrisitet, e", "cell": "H40", "unit": ""},
            {"label": "Gjennomsnittlig vertikalspenning, qV", "cell": "H41", "unit": ""},
            {"label": "Ruhet i fundamentfuge, rb", "cell": "H42", "unit": ""},
            {"label": "Krav til rb ≤", "cell": "H43", "unit": ""},
            {"label": "Effektiv fundamentbredde, b0", "cell": "H44", "unit": ""},
            {"label": "Krav til b0 ≥ b0,min og e ≤ b0,min", "cell": "H45", "unit": ""},
        ],
        "messages": ["D46"],
    },
    {
        "title": "Bæreevnefaktorer",
        "rows": [
            {"label": "Bæreevnefaktor, Nγ", "cell": "M40", "unit": ""},
            {"label": "Bæreevnefaktor, Nq", "cell": "M41", "unit": ""},
            {"label": "Reduksjonsfaktor skrånende terreng, fsq", "cell": "M42", "unit": ""},
            {"label": "Reduksjonsfaktor skrånende terreng, fsa", "cell": "M43", "unit": ""},
            {"label": "Overført fundamenttrykk, σV", "cell": "M44", "unit": ""},
            {"label": "Kontroll sv > qv", "cell": "M45", "unit": ""},
        ],
        "messages": ["I46"],
    },
]

DETAIL_TABLES = [
    {
        "title": "Jordtrykk – detaljerte verdier",
        "rows": [
            {"label": "qg = qQk·γQ,b + qk·γQ", "cell": "B71", "unit": "kPa"},
            {"label": "Vertikalspenning ved D=5 m", "cell": "B73", "unit": "kPa"},
            {"label": "Vertikalspenning, bunn", "cell": "B74", "unit": "kPa"},
            {"label": "Strekk-test topp, D78", "cell": "D78", "unit": ""},
            {"label": "tan ρ bak", "cell": "R72", "unit": ""},
            {"label": "tan ρ under", "cell": "R74", "unit": ""},
            {"label": "R75 (KA·(p+a)-a)", "cell": "R75", "unit": "kPa"},
            {"label": "s (helning bak mur)", "cell": "R87", "unit": ""},
            {"label": "ω_a", "cell": "R88", "unit": ""},
            {"label": "KA", "cell": "R113", "unit": ""},
            {"label": "K_delta", "cell": "R135", "unit": ""},
            {"label": "EA (valgt tilfelle)", "cell": "B104", "unit": "kN"},
            {"label": "RH (valgt tilfelle)", "cell": "B105", "unit": "kN"},
            {"label": "T  (valgt tilfelle)", "cell": "B106", "unit": "kN"},
            {"label": "c1 (momentarm EA)", "cell": "F104", "unit": "m"},
            {"label": "cH (momentarm RH)", "cell": "F105", "unit": "m"},
            {"label": "Egenvekt mur, GV", "cell": "U118", "unit": "kN"},
        ],
    },
    {
        "title": "Bæreevne – mellomregninger",
        "rows": [
            {"label": "Eksentrisitet, e", "cell": "H40", "unit": "m"},
            {"label": "Effektiv bredde, b0", "cell": "R121", "unit": "m"},
            {"label": "b0 min", "cell": "R124", "unit": "m"},
            {"label": "Kontroll b0 ≥ b0,min", "cell": "R125", "unit": ""},
            {"label": "Kontroll e ≤ grense", "cell": "R126", "unit": ""},
            {"label": "Materialtype", "cell": "R140", "unit": ""},
            {"label": "rb krav (leire)", "cell": "R141", "unit": ""},
            {"label": "rb krav (grus)", "cell": "R142", "unit": ""},
            {"label": "rb krav (valgt)", "cell": "R143", "unit": ""},
            {"label": "Kontroll rb", "cell": "R67", "unit": ""},
            {"label": "Kontroll σV > qV", "cell": "R68", "unit": ""},
            {"label": "Samlet kontroll", "cell": "R69", "unit": ""},
            {"label": "fw", "cell": "R101", "unit": ""},
            {"label": "ω (rad)", "cell": "R103", "unit": ""},
            {"label": "N (spenningsforhold)", "cell": "R104", "unit": ""},
            {"label": "Nq", "cell": "R114", "unit": ""},
            {"label": "Nγ", "cell": "R115", "unit": ""},
            {"label": "fsq", "cell": "R116", "unit": ""},
            {"label": "fsa", "cell": "R117", "unit": ""},
        ],
    },
]


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _parse_number(raw: str) -> float | None:
    text = (raw or "").strip()
    if text == "":
        return None
    text = text.replace(" ", "").replace(",", ".")
    return float(text)


def _calculate_solution(user_inputs: dict[str, Any]) -> TorrmurResult:
    inp = inputs_from_cell_dict(user_inputs)
    return calculate(inp)


def _get_cell_value(solution: TorrmurResult, cell: str) -> Any:
    return solution.get(cell)


def _format_value(value: Any) -> str:
    if value is None or value == "":
        return ""
    text = str(value)
    if text in {" ", "None"}:
        return ""
    if text.startswith("#"):
        return text
    if isinstance(value, bool):
        return "Ja" if value else "Nei"
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if math.isnan(value) or math.isinf(value):
            return text
        if abs(value) >= 1000:
            return f"{value:,.3f}".replace(",", "X").replace(".", ",").replace("X", " ")
        return f"{value:.6f}".rstrip("0").rstrip(".").replace(".", ",")
    return text


def _build_summary_dataframe(solution: dict[str, Any], rows: list[dict[str, str]]) -> pd.DataFrame:
    records = []
    for row in rows:
        value = _get_cell_value(solution, row["cell"])
        records.append({"Parameter": row["label"], "Verdi": _format_value(value), "Enhet": row["unit"]})
    return pd.DataFrame(records)


def _build_detail_dataframe(solution: dict[str, Any], config: dict[str, Any]) -> pd.DataFrame:
    records = []
    for row_def in config["rows"]:
        value = _get_cell_value(solution, row_def["cell"])
        records.append({"Parameter": row_def["label"], "Verdi": _format_value(value), "Enhet": row_def.get("unit", "")})
    return pd.DataFrame(records)


def _render_message(text: str) -> None:
    clean = (text or "").strip()
    if not clean:
        return
    if clean.upper() in {"OK", "JA"}:
        st.success(clean)
    elif clean.upper() in {"NEI", "IKKE OK"} or clean.startswith("NB"):
        st.warning(clean)
    else:
        st.info(clean)


def _check_output_constraints(inputs: dict[str, Any], constraints: dict[str, dict]) -> bool:
    try:
        sol = _calculate_solution(inputs)
    except Exception:
        return False
    for cell, check in constraints.items():
        val = _get_cell_value(sol, cell)
        if check["type"] == "eq":
            if str(val).strip().upper() != str(check["value"]).strip().upper():
                return False
        else:
            if not isinstance(val, (int, float)) or math.isnan(val) or math.isinf(val):
                return False
            lo = check.get("min")
            hi = check.get("max")
            if lo is not None and val < lo:
                return False
            if hi is not None and val > hi:
                return False
    return True


def _find_limit(
    base_inputs: dict[str, Any], cell: str, base_val: float,
    direction: int, constraints: dict[str, dict], n_iter: int = 20,
) -> float | None:
    scale = max(abs(base_val), 0.5) * 5
    far = base_val + direction * scale
    test = dict(base_inputs)
    test[cell] = far
    if _check_output_constraints(test, constraints):
        return None
    safe, unsafe = base_val, far
    for _ in range(n_iter):
        mid = (safe + unsafe) / 2.0
        test[cell] = mid
        if _check_output_constraints(test, constraints):
            safe = mid
        else:
            unsafe = mid
    return safe


def _run_sensitivity(
    base_inputs: dict[str, Any], constraints: dict[str, dict],
    progress_callback=None, input_cells: set[str] | None = None,
) -> list[dict[str, Any]]:
    numeric_fields = [f for sec in INPUT_SECTIONS for f in sec["fields"] if f["kind"] == "number"]
    if input_cells is not None:
        numeric_fields = [f for f in numeric_fields if f["cell"] in input_cells]
    total = len(numeric_fields)
    results: list[dict[str, Any]] = []
    for idx, field_def in enumerate(numeric_fields):
        cell = field_def["cell"]
        base_val = base_inputs.get(cell)
        if base_val is None:
            continue
        if progress_callback:
            progress_callback(idx / total, f"Analyserer {field_def['label']} …")
        max_val = _find_limit(base_inputs, cell, base_val, +1, constraints)
        min_val = _find_limit(base_inputs, cell, base_val, -1, constraints)
        results.append({
            "label": field_def["label"], "unit": field_def["unit"], "cell": cell,
            "base": base_val, "min": min_val, "max": max_val,
            "room_down": None if min_val is None else abs(base_val - min_val),
            "room_up": None if max_val is None else abs(max_val - base_val),
        })
    if progress_callback:
        progress_callback(1.0, "Ferdig!")
    return results


# ---------------------------------------------------------------------------
# Cross-section drawing
# ---------------------------------------------------------------------------

def _draw_cross_section(sol: dict[str, Any]) -> go.Figure:
    H = float(sol.get("B14", 4))
    D = float(sol.get("B15", 0.5))
    bb = float(sol.get("B16", 2.2))
    bt = float(sol.get("B19", 2.2))
    d_h = float(sol.get("B20", 5))
    EA = float(sol.get("B38", 0))
    T = float(sol.get("B39", 0))
    GV = float(sol.get("B40", 0))
    RV = float(sol.get("B41", 0))
    RH = float(sol.get("B42", 0))
    PH = float(sol.get("B8", 0))
    PV = float(sol.get("B9", 0))
    c1 = float(sol.get("B43", 0))
    c3 = float(sol.get("B45", 0))
    cH = float(sol.get("B47", 0))
    c4 = float(sol.get("B46", bb / 2))

    top_offset = H / d_h if d_h != 0 else 0
    wx = [0, bb, bt + top_offset, top_offset, 0]
    wy = [0, 0, H, H, 0]

    fig = go.Figure()

    # Ground zones
    fig.add_trace(go.Scatter(x=[-1.5, 0, 0, -1.5, -1.5], y=[0, 0, -D, -D, 0],
        fill="toself", fillcolor="rgba(212,201,168,0.4)",
        line=dict(color="rgba(212,201,168,0.6)", width=1), hoverinfo="skip", showlegend=False))
    fig.add_trace(go.Scatter(x=[bb, bb+2.5, bb+2.5, bb, bb], y=[0, 0, -D, -D, 0],
        fill="toself", fillcolor="rgba(212,201,168,0.4)",
        line=dict(color="rgba(212,201,168,0.6)", width=1), hoverinfo="skip", showlegend=False))
    fig.add_trace(go.Scatter(x=[0, bb, bb, 0, 0], y=[0, 0, -D, -D, 0],
        fill="toself", fillcolor="rgba(196,185,152,0.3)",
        line=dict(color="rgba(196,185,152,0.5)", width=1), hoverinfo="skip", showlegend=False))
    fig.add_trace(go.Scatter(x=[bb, bb+2.5, bb+2.5, bt+top_offset, bb], y=[0, 0, H, H, 0],
        fill="toself", fillcolor="rgba(232,220,200,0.35)",
        line=dict(color="rgba(200,180,150,0.5)", width=1), name="Bakfylling", hoverinfo="name", showlegend=False))

    # Wall polygon
    fig.add_trace(go.Scatter(x=wx, y=wy, fill="toself", fillcolor="rgba(160,160,160,0.85)",
        line=dict(color="#444", width=2.5), name="Mur",
        hovertemplate=f"<b>Mur</b><br>H = {H:.2f} m<br>bb = {bb:.2f} m<br>bt = {bt:.2f} m<br>D = {D:.2f} m<extra></extra>",
        showlegend=False))
    fig.add_annotation(x=np.mean(wx[:4]), y=H/2, text="<b>MUR</b>", showarrow=False, font=dict(size=14, color="#333"))

    # Ground line
    fig.add_shape(type="line", x0=-1.5, y0=0, x1=bb+2.5, y1=0, line=dict(color="#6b5b3e", width=1.5, dash="dash"))
    fig.add_annotation(x=-1.3, y=0.08, text="terreng", showarrow=False, font=dict(size=10, color="#6b5b3e"))

    # Dimension annotations
    fig.add_annotation(x=0, y=-D-0.3, ax=bb, ay=-D-0.3, xref="x", yref="y", axref="x", ayref="y",
        showarrow=True, arrowhead=3, arrowsize=1, arrowwidth=1.5, arrowcolor="#555")
    fig.add_annotation(x=bb, y=-D-0.3, ax=0, ay=-D-0.3, xref="x", yref="y", axref="x", ayref="y",
        showarrow=True, arrowhead=3, arrowsize=1, arrowwidth=1.5, arrowcolor="#555")
    fig.add_annotation(x=bb/2, y=-D-0.55, text=f"bb = {bb:.2f} m", showarrow=False, font=dict(size=10, color="#555"))
    fig.add_annotation(x=-0.5, y=0, ax=-0.5, ay=H, xref="x", yref="y", axref="x", ayref="y",
        showarrow=True, arrowhead=3, arrowsize=1, arrowwidth=1.5, arrowcolor="#555")
    fig.add_annotation(x=-0.5, y=H, ax=-0.5, ay=0, xref="x", yref="y", axref="x", ayref="y",
        showarrow=True, arrowhead=3, arrowsize=1, arrowwidth=1.5, arrowcolor="#555")
    fig.add_annotation(x=-0.85, y=H/2, text=f"H = {H:.1f} m", showarrow=False, font=dict(size=10, color="#555"), textangle=-90)
    if D > 0:
        fig.add_annotation(x=-0.5, y=-D, ax=-0.5, ay=0, xref="x", yref="y", axref="x", ayref="y",
            showarrow=True, arrowhead=3, arrowsize=1, arrowwidth=1.5, arrowcolor="#555")
        fig.add_annotation(x=-0.5, y=0, ax=-0.5, ay=-D, xref="x", yref="y", axref="x", ayref="y",
            showarrow=True, arrowhead=3, arrowsize=1, arrowwidth=1.5, arrowcolor="#555")
        fig.add_annotation(x=-0.85, y=-D/2, text=f"D = {D:.1f} m", showarrow=False, font=dict(size=10, color="#555"), textangle=-90)

    # Earth pressure distribution
    ka_korr = float(sol.get("B36", 0))
    scale = max(H, bb) * 0.5
    if ka_korr > 0:
        ep_x = [bb, bb + ka_korr * scale * 0.8, bb, bb]
        ep_y = [0, 0, H, 0]
        fig.add_trace(go.Scatter(x=ep_x, y=ep_y, fill="toself", fillcolor="rgba(228,87,86,0.12)",
            line=dict(color="rgba(228,87,86,0.5)", width=1), name="Jordtrykk-fordeling",
            hovertemplate=f"K<sub>A,korr</sub> = {ka_korr:.4f}<extra></extra>", showlegend=False))

    force_max = max(abs(EA), abs(GV), abs(RH), abs(RV), 1)

    def _add_force_arrow(x0, y0, x1, y1, color, label, value, unit, extra_hover=""):
        hover = f"<b>{label}</b> = {value:.2f} {unit}"
        if extra_hover:
            hover += f"<br>{extra_hover}"
        hover += "<extra></extra>"
        fig.add_trace(go.Scatter(x=[x0, x1], y=[y0, y1], mode="lines",
            line=dict(color=color, width=3), hovertemplate=hover, showlegend=False))
        fig.add_annotation(x=x1, y=y1, ax=x0, ay=y0, xref="x", yref="y", axref="x", ayref="y",
            showarrow=True, arrowhead=2, arrowsize=1.5, arrowwidth=2.5, arrowcolor=color)
        fig.add_annotation(x=x0, y=y0, text=f"<b>{label} = {value:.1f} {unit}</b>",
            showarrow=False, font=dict(size=10, color=color),
            xanchor="left" if x0 >= x1 else "right", yanchor="bottom",
            xshift=5 if x0 >= x1 else -5, yshift=5)

    if EA != 0:
        arr_len = EA / force_max * scale
        _add_force_arrow(bb+1.5, c1, bb+1.5-arr_len, c1, "#e45756", "EA", EA, "kN", f"Momentarm c1 = {c1:.2f} m")
    if T != 0:
        arr_len = abs(T) / force_max * scale
        direction = -1 if T > 0 else 1
        y_tail = c1 + direction * arr_len
        _add_force_arrow(bb+0.3, y_tail, bb+0.3, c1, "#ff9900", "T", T, "kN")
    if GV != 0:
        arr_len = GV / force_max * scale * 0.5
        _add_force_arrow(c3, H+0.5, c3, H+0.5-arr_len, "#2171b5", "GV", GV, "kN", f"Momentarm c3 = {c3:.2f} m")
    if PH != 0:
        yp_val = float(sol.get("B10", 0))
        arr_len = abs(PH) / force_max * scale
        y_ph = H + yp_val
        x_start = top_offset + bt / 2 + arr_len
        _add_force_arrow(x_start, y_ph, x_start - arr_len, y_ph, "#9467bd", "PH", PH, "kN/m")
    if PV != 0:
        xp_val = float(sol.get("B11", 0))
        arr_len = abs(PV) / force_max * scale * 0.5
        x_pv = top_offset + xp_val
        _add_force_arrow(x_pv, H+1.0, x_pv, H+1.0-arr_len, "#17becf", "PV", PV, "kN/m")
    if RV != 0:
        arr_len = RV / force_max * scale * 0.5
        _add_force_arrow(c4, -D-0.1, c4, -D-0.1-arr_len, "#2ca02c", "RV", RV, "kN", f"Momentarm c4 = {c4:.2f} m")
    if RH != 0:
        arr_len = RH / force_max * scale
        _add_force_arrow(-0.1, cH, -0.1-arr_len, cH, "#d62728", "RH", RH, "kN", f"Momentarm cH = {cH:.2f} m")

    margin = max(1.5, scale * 0.5)
    fig.update_layout(
        title=dict(text="Tverrsnitt med krefter", font=dict(size=16)),
        xaxis=dict(title="Bredde [m]", range=[-margin-0.5, bb+3.5], constrain="domain",
            scaleanchor="y", scaleratio=1, gridcolor="rgba(0,0,0,0.06)"),
        yaxis=dict(title="Høyde [m]", range=[-D-margin, H+margin], gridcolor="rgba(0,0,0,0.06)"),
        plot_bgcolor="white", height=650, margin=dict(l=60, r=30, t=50, b=50), hovermode="closest",
    )
    return fig


# ---------------------------------------------------------------------------
# Optimization helper
# ---------------------------------------------------------------------------

_OPT_PARAMS = [
    {"cell": "B16", "label": "Murbredde bunn, bb", "unit": "m", "direction": "min"},
    {"cell": "B19", "label": "Murbredde topp, bt", "unit": "m", "direction": "min"},
    {"cell": "B14", "label": "Murhøyde, H", "unit": "m", "direction": "min"},
    {"cell": "B15", "label": "Fotdybde, D", "unit": "m", "direction": "min"},
    {"cell": "B24", "label": "Materialfaktor, γm", "unit": "", "direction": "max"},
]

_OPT_CONSTRAINTS = [
    {"label": "Bæreevne: σV > qV", "cell": "M45", "type": "eq", "value": "OK"},
    {"label": "Fundament: b0 og eksentrisitet OK", "cell": "H45", "type": "eq", "value": "OK"},
]


def _optimize_param(
    base_inputs: dict[str, Any], cell: str, direction: str,
    constraints: dict[str, dict], lo_bound: float, hi_bound: float, n_iter: int = 30,
) -> float | None:
    test = dict(base_inputs)
    if direction == "min":
        good, bad = hi_bound, lo_bound
        test[cell] = good
        if not _check_output_constraints(test, constraints):
            return None
        test[cell] = bad
        if _check_output_constraints(test, constraints):
            return bad
    else:
        good, bad = lo_bound, hi_bound
        test[cell] = good
        if not _check_output_constraints(test, constraints):
            return None
        test[cell] = bad
        if _check_output_constraints(test, constraints):
            return bad
    for _ in range(n_iter):
        mid = (good + bad) / 2.0
        test[cell] = mid
        if _check_output_constraints(test, constraints):
            good = mid
        else:
            bad = mid
    return good


# ---------------------------------------------------------------------------
# Main tørrmur render function
# ---------------------------------------------------------------------------

def _render_torrmur():
    st.header("🧱 Dimensjonering av tørrmur")
    st.caption("V220 kapittel 10.3 – frittstående Python-motor")

    tab_input, tab_output, tab_cross, tab_opt, tab_sens = st.tabs(
        ["📝 Inndata", "📊 Resultater", "🏗️ Tverrsnitt", "⚙️ Optimalisering", "🔍 Sensitivitetsanalyse"]
    )

    # --- Tab 1: Inndata ---
    with tab_input:
        with st.expander("Om denne versjonen", expanded=False):
            st.write(
                "Denne versjonen implementerer:\n"
                "- samme hovedinndata som i det opprinnelige beregningsarket\n"
                "- en frittstående beregningsmotor i ren Python (ingen Excel-avhengighet)\n"
                "- samme hovedresultater og utvalgte mellomregninger"
            )

        entered_values: dict[str, Any] = {}
        for section in INPUT_SECTIONS:
            st.markdown(f"#### {section['title']}")
            cols = st.columns(2)
            for i, field_def in enumerate(section["fields"]):
                with cols[i % 2]:
                    label = field_def["label"] if not field_def["unit"] else f"{field_def['label']} [{field_def['unit']}]"
                    key = f"tm_input_{field_def['cell']}"
                    if field_def["kind"] == "choice":
                        selected = st.selectbox(label, options=field_def["options"],
                            index=field_def["options"].index(field_def["default"]), key=key)
                        entered_values[field_def["cell"]] = selected
                    else:
                        raw = st.text_input(label,
                            value="" if field_def["default"] == "" else str(field_def["default"]), key=key)
                        try:
                            entered_values[field_def["cell"]] = _parse_number(raw)
                        except ValueError:
                            entered_values[field_def["cell"]] = "__INVALID__"
            st.divider()

    # --- Compute ---
    _invalid_cells = [c for c, v in entered_values.items() if v == "__INVALID__"]
    if _invalid_cells:
        solution = None
        _calc_error: str | None = f"Ugyldig tallformat i: {', '.join(_invalid_cells)}. Bruk tall, komma eller punktum."
    else:
        _calc_error = None
        try:
            solution = _calculate_solution(entered_values)
        except Exception as exc:
            solution = None
            _calc_error = f"Beregningsfeil: {exc}"

    # --- Tab 2: Resultater ---
    with tab_output:
        if _calc_error:
            st.error(_calc_error)
        elif solution is not None:
            st.subheader("Hovedresultater")
            result_cols = st.columns(len(SUMMARY_SECTIONS))
            for idx, section in enumerate(SUMMARY_SECTIONS):
                with result_cols[idx]:
                    st.markdown(f"#### {section['title']}")
                    df = _build_summary_dataframe(solution, section["rows"])
                    st.dataframe(df, width="stretch", hide_index=True)
                    for msg_cell in section.get("messages", []):
                        _render_message(_format_value(_get_cell_value(solution, msg_cell)))
            st.divider()
            st.subheader("Mellomregninger")
            for config in DETAIL_TABLES:
                with st.expander(config["title"]):
                    detail_df = _build_detail_dataframe(solution, config)
                    st.dataframe(detail_df, width="stretch", hide_index=True)
            with st.expander("Debug / celleverdier"):
                debug_cells = ["B26", "B27", "B28", "B29", "B30", "B31", "B35", "B36", "B37",
                    "B38", "B39", "B40", "B41", "B42", "H40", "H41", "H42", "H43",
                    "H44", "H45", "M40", "M41", "M42", "M43", "M44", "M45", "D46", "I46"]
                debug_records = [{"Celle": cell, "Verdi": _format_value(_get_cell_value(solution, cell))} for cell in debug_cells]
                st.dataframe(pd.DataFrame(debug_records), width="stretch", hide_index=True)

    # --- Tab 3: Tverrsnitt ---
    with tab_cross:
        if _calc_error:
            st.error(_calc_error)
        elif solution is not None:
            st.subheader("Tverrsnitt av tørrmur")
            st.caption("Velg parametere og dra sliderne – figuren oppdateres live.")

            _cross_all_fields = [f for sec in INPUT_SECTIONS for f in sec["fields"] if f["kind"] == "number"]
            _cross_field_labels = {
                (f["label"] + (f" [{f['unit']}]" if f["unit"] else "")): f for f in _cross_all_fields
            }
            _cross_selected = st.multiselect("Velg parametere å justere", options=list(_cross_field_labels.keys()),
                default=[k for k, f in _cross_field_labels.items() if f["cell"] in {"B14", "B16", "B19", "B15"}],
                key="tm_cross_param_select")

            @st.fragment
            def _cross_section_live():
                selected = st.session_state.get("tm_cross_param_select", [])
                field_map = _cross_field_labels
                overrides: dict[str, float] = {}
                if selected:
                    sl_cols = st.columns(min(len(selected), 3))
                    for si, slbl in enumerate(selected):
                        sf = field_map[slbl]
                        base = entered_values.get(sf["cell"])
                        if base is None:
                            base = sf.get("default") or 0.0
                        base = float(base)
                        half = max(abs(base) * 0.5, 0.5)
                        smin = round(base - half, 4)
                        smax = round(base + half, 4)
                        step = max(0.01, round(2 * half / 100, 4))
                        sk = f"tm_cross_sl_{sf['cell']}"
                        current = st.session_state.get(sk)
                        current = float(current) if current is not None else base
                        current = max(smin, min(smax, current))
                        with sl_cols[si % len(sl_cols)]:
                            overrides[sf["cell"]] = _live_slider(
                                label=slbl, min_value=smin, max_value=smax,
                                value=current, step=step, key=sk)

                cross_inputs = dict(entered_values)
                cross_inputs.update(overrides)
                try:
                    cross_sol = _calculate_solution(cross_inputs)
                except Exception as exc:
                    st.error(f"Beregningsfeil: {exc}")
                    return

                for cell, val in overrides.items():
                    cross_sol[cell] = val

                fig = _draw_cross_section(cross_sol)
                st.plotly_chart(fig, width="stretch")

                fcols = st.columns(3)
                forces = [("Jordtrykk, EA", "B38", "kN"), ("Skjærkraft, T", "B39", "kN"),
                    ("Egenvekt, GV", "B40", "kN"), ("Vertikalresultant, RV", "B41", "kN"),
                    ("Horisontalresultant, RH", "B42", "kN"), ("Horisontallast, PH", "B8", "kN/m"),
                    ("Vertikallast, PV", "B9", "kN/m")]
                for i, (lbl, cell, unit) in enumerate(forces):
                    with fcols[i % 3]:
                        val = _get_cell_value(cross_sol, cell)
                        st.metric(lbl, f"{_format_value(val)} {unit}")

            _cross_section_live()

    # --- Tab 4: Optimalisering ---
    with tab_opt:
        if _calc_error:
            st.error(_calc_error)
        elif solution is None:
            st.info("Fyll inn gyldige verdier i **Inndata**-fanen.")
        else:
            st.subheader("Optimalisering av murdimensjoner")
            st.caption("Finn minste (eller største) verdi av en parameter som fortsatt tilfredsstiller alle krav.")

            st.markdown("**Krav som skal holdes:**")
            opt_constraints: dict[str, dict] = {}
            _oc_cols = st.columns(len(_OPT_CONSTRAINTS))
            for _oi, _oc in enumerate(_OPT_CONSTRAINTS):
                with _oc_cols[_oi]:
                    _cur = _format_value(_get_cell_value(solution, _oc["cell"]))
                    _icon = "✅" if _cur.strip().upper() == _oc["value"].upper() else "❌"
                    if st.checkbox(f'{_icon} {_oc["label"]}  (nå: {_cur})', value=True, key=f"tm_opt_chk_{_oc['cell']}"):
                        opt_constraints[_oc["cell"]] = {"type": _oc["type"], "value": _oc["value"]}

            if not opt_constraints:
                st.info("Velg minst ett krav.")
            else:
                st.divider()
                _opt_labels = [p["label"] for p in _OPT_PARAMS]
                _opt_sel = st.multiselect("Parametere å optimalisere", options=_opt_labels,
                    default=[_opt_labels[0], _opt_labels[1]], key="tm_opt_param_select")

                _opt_configs: list[dict] = []
                if _opt_sel:
                    st.markdown("**Søkegrenser** (min og maks for søket)")
                    for _ol in _opt_sel:
                        _op = next(p for p in _OPT_PARAMS if p["label"] == _ol)
                        _base_v = entered_values.get(_op["cell"])
                        if _base_v is None:
                            _base_v = 0.0
                        _bc1, _bc2, _bc3, _bc4 = st.columns([3, 1.5, 1.5, 1])
                        with _bc1:
                            st.markdown(f'**{_op["label"]}** (nå: {_format_value(_base_v)} {_op["unit"]})')
                        with _bc2:
                            _lo_def = 0.1 if _op["direction"] == "min" else _base_v
                            _lo_b = st.number_input("Søk fra", value=_lo_def, step=0.1, format="%.2f", key=f"tm_opt_lo_{_op['cell']}")
                        with _bc3:
                            _hi_def = _base_v if _op["direction"] == "min" else _base_v * 3
                            _hi_b = st.number_input("Søk til", value=_hi_def, step=0.1, format="%.2f", key=f"tm_opt_hi_{_op['cell']}")
                        with _bc4:
                            st.markdown(f'Mål: **{"MIN" if _op["direction"] == "min" else "MAKS"}**')
                        _opt_configs.append({**_op, "base": _base_v, "lo": float(_lo_b), "hi": float(_hi_b)})

                if _opt_configs:
                    if st.button("🚀 Kjør optimalisering", type="primary", use_container_width=True):
                        if not _check_output_constraints(entered_values, opt_constraints):
                            st.error("Nåverdiene tilfredsstiller ikke kravene – juster inndata først.")
                        else:
                            _opt_results: list[dict] = []
                            _prog_opt = st.progress(0.0, text="Optimaliserer …")
                            for _idx, _oc_cfg in enumerate(_opt_configs):
                                _prog_opt.progress(_idx / len(_opt_configs), text=f'Optimaliserer {_oc_cfg["label"]} …')
                                _opt_val = _optimize_param(entered_values, _oc_cfg["cell"], _oc_cfg["direction"],
                                    opt_constraints, _oc_cfg["lo"], _oc_cfg["hi"])
                                _opt_results.append({"label": _oc_cfg["label"], "unit": _oc_cfg["unit"],
                                    "base": _oc_cfg["base"], "optimal": _opt_val, "direction": _oc_cfg["direction"]})
                            _prog_opt.progress(1.0, text="Ferdig!")
                            _prog_opt.empty()

                            st.markdown("---")
                            st.markdown("#### Resultat")
                            _res_cols = st.columns(len(_opt_results))
                            for _ri, _rr in enumerate(_opt_results):
                                with _res_cols[_ri % len(_res_cols)]:
                                    if _rr["optimal"] is not None:
                                        _diff = _rr["optimal"] - _rr["base"]
                                        _pct = _diff / abs(_rr["base"]) * 100 if _rr["base"] != 0 else 0
                                        _arrow = "↓" if _diff < 0 else "↑"
                                        st.metric(_rr["label"], f'{_format_value(_rr["optimal"])} {_rr["unit"]}',
                                            delta=f"{_arrow} {abs(_pct):.1f}% fra {_format_value(_rr['base'])}",
                                            delta_color="normal" if _rr["direction"] == "max" else "inverse")
                                    else:
                                        st.metric(_rr["label"], "Ingen løsning",
                                            delta="Kravene kan ikke oppfylles i søkeområdet", delta_color="off")

                            _opt_rows = []
                            for _rr in _opt_results:
                                _opt_rows.append({"Parameter": _rr["label"], "Enhet": _rr["unit"],
                                    "Nåverdi": _format_value(_rr["base"]),
                                    "Optimal verdi": _format_value(_rr["optimal"]) if _rr["optimal"] is not None else "—",
                                    "Endring": _format_value(_rr["optimal"] - _rr["base"]) if _rr["optimal"] is not None else "—",
                                    "Mål": "Minimér" if _rr["direction"] == "min" else "Maksimér"})
                            st.dataframe(pd.DataFrame(_opt_rows), width="stretch", hide_index=True)

                            _bar_data = []
                            for _rr in _opt_results:
                                if _rr["optimal"] is None:
                                    continue
                                _bar_data.append({"Parameter": _rr["label"], "Verdi": _rr["base"], "Type": "Nåværende"})
                                _bar_data.append({"Parameter": _rr["label"], "Verdi": _rr["optimal"], "Type": "Optimal"})
                            if _bar_data:
                                _bdf = pd.DataFrame(_bar_data)
                                _bchart = (alt.Chart(_bdf).mark_bar(cornerRadiusEnd=4, opacity=0.85)
                                    .encode(x=alt.X("Parameter:N", title=None, axis=alt.Axis(labelAngle=0)),
                                        y=alt.Y("Verdi:Q", title="Verdi"),
                                        color=alt.Color("Type:N", scale=alt.Scale(domain=["Nåværende", "Optimal"], range=["#90a4ae", "#43a047"]),
                                            legend=alt.Legend(orient="top", title=None)),
                                        xOffset="Type:N",
                                        tooltip=["Parameter", "Type", alt.Tooltip("Verdi:Q", format=".3f")])
                                    .properties(height=300).configure_view(strokeWidth=0))
                                st.altair_chart(_bchart, width="stretch")

    # --- Tab 5: Sensitivitetsanalyse ---
    _PREDEFINED_CHECKS = [
        {"label": "Bæreevne: σV > qV", "cell": "M45", "type": "eq", "value": "OK"},
        {"label": "Fundament: b0 og eksentrisitet OK", "cell": "H45", "type": "eq", "value": "OK"},
    ]

    with tab_sens:
        if solution is None:
            st.info("Fyll inn gyldige verdier i **Inndata**-fanen.")
        else:
            st.subheader("Sensitivitetsanalyse")
            st.caption("Juster parameterne med sliderne. Nedre og øvre grenseverdier beregnes automatisk.")

            st.markdown("**Krav som skal oppfylles:**")
            active_constraints: dict[str, dict] = {}
            _chk_cols = st.columns(len(_PREDEFINED_CHECKS))
            for _ci, chk in enumerate(_PREDEFINED_CHECKS):
                with _chk_cols[_ci]:
                    cur = _format_value(_get_cell_value(solution, chk["cell"]))
                    icon = "✅" if cur.strip().upper() == chk["value"].upper() else "❌"
                    if st.checkbox(f'{icon} {chk["label"]}  (nå: {cur})', value=True, key=f"tm_sens_chk_{chk['cell']}"):
                        active_constraints[chk["cell"]] = {"type": chk["type"], "value": chk["value"]}

            with st.expander("Egendefinerte tallgrenser (valgfritt)"):
                _output_opts: dict[str, dict] = {}
                for _sec in SUMMARY_SECTIONS:
                    for _row in _sec["rows"]:
                        _lbl = _row["label"]
                        if _row["unit"]:
                            _lbl += f" [{_row['unit']}]"
                        _output_opts[_lbl] = _row
                _custom_labels = st.multiselect("Velg output-parametere", options=list(_output_opts.keys()), key="tm_sens_custom_select")
                for _lbl in _custom_labels:
                    _info = _output_opts[_lbl]
                    _cell = _info["cell"]
                    _base_c = _get_cell_value(solution, _cell)
                    _c1, _c2, _c3 = st.columns([4, 2, 2])
                    with _c1:
                        st.markdown(f"**{_lbl}** — nåverdi: {_format_value(_base_c)}")
                    with _c2:
                        _lo_raw = st.text_input("Min", key=f"tm_sens_cmin_{_cell}", placeholder="ingen")
                    with _c3:
                        _hi_raw = st.text_input("Maks", key=f"tm_sens_cmax_{_cell}", placeholder="ingen")
                    _lo: float | None = None
                    _hi: float | None = None
                    try:
                        if _lo_raw.strip():
                            _lo = _parse_number(_lo_raw)
                    except ValueError:
                        pass
                    try:
                        if _hi_raw.strip():
                            _hi = _parse_number(_hi_raw)
                    except ValueError:
                        pass
                    if _lo is not None or _hi is not None:
                        active_constraints[_cell] = {"type": "range", "min": _lo, "max": _hi}

            if not active_constraints:
                st.info("Velg minst ett krav for å aktivere analysen.")
            else:
                st.divider()

                _all_numeric = [f for sec in INPUT_SECTIONS for f in sec["fields"] if f["kind"] == "number"]
                _slider_inputs = dict(entered_values)
                for _f in _all_numeric:
                    _sk = f"tm_sens_sl_{_f['cell']}"
                    if _sk in st.session_state:
                        _slider_inputs[_f["cell"]] = st.session_state[_sk]

                _base_ok = _check_output_constraints(_slider_inputs, active_constraints)
                _sr: list[dict[str, Any]] = []
                _sens_map: dict[str, dict] = {}
                if _base_ok:
                    with st.spinner("Beregner grenseverdier …"):
                        _sr = _run_sensitivity(_slider_inputs, active_constraints)
                    _sens_map = {r["cell"]: r for r in _sr}

                if not _base_ok:
                    st.error("⚠️ Sliderverdiene bryter kravene – juster parameterne til kravene er oppfylt.")

                for section in INPUT_SECTIONS:
                    _nf = [f for f in section["fields"] if f["kind"] == "number"]
                    if not _nf:
                        continue
                    st.markdown(
                        f'<p style="margin:18px 0 4px;font-weight:700;font-size:15px;'
                        f'color:#444;border-bottom:2px solid #e0e0e0;padding-bottom:4px;">'
                        f'{section["title"]}</p>', unsafe_allow_html=True)
                    for _f in _nf:
                        _bv = entered_values.get(_f["cell"])
                        if _bv is None:
                            _bv = _f.get("default") or 0.0
                        _half = abs(_bv) * 0.5 if _bv != 0 else 5.0
                        _half = max(_half, 0.01)
                        _smin = float(round(_bv - _half, 6))
                        _smax = float(round(_bv + _half, 6))
                        _step = float(max(0.001, round(2 * _half / 100, 6)))
                        _sk = f"tm_sens_sl_{_f['cell']}"
                        if _sk in st.session_state:
                            _sv = st.session_state[_sk]
                            if _sv < _smin or _sv > _smax:
                                del st.session_state[_sk]
                        _lbl = _f["label"] + (f" [{_f['unit']}]" if _f["unit"] else "")
                        _item = _sens_map.get(_f["cell"])
                        if _item:
                            _lo_v = _item["min"]
                            _hi_v = _item["max"]
                        else:
                            _lo_v = None
                            _hi_v = None
                        if _base_ok:
                            _lo_s = _format_value(_lo_v) if _lo_v is not None else "∞"
                            _hi_s = _format_value(_hi_v) if _hi_v is not None else "∞"
                        else:
                            _lo_s = "—"
                            _hi_s = "—"

                        st.slider(_lbl, min_value=_smin, max_value=_smax, value=float(_bv), step=_step, key=_sk)

                        _range = _smax - _smin
                        if _range > 0 and _base_ok:
                            _bar_lo = max(_smin, _lo_v) if _lo_v is not None else _smin
                            _bar_hi = min(_smax, _hi_v) if _hi_v is not None else _smax
                            _pct_left = (_bar_lo - _smin) / _range * 100
                            _pct_right = (_smax - _bar_hi) / _range * 100
                            _pct_mid = max(0, 100 - _pct_left - _pct_right)
                            _cur = st.session_state.get(_sk, _bv)
                            _pct_cur = max(0, min(100, (_cur - _smin) / _range * 100))
                            _left_open = _lo_v is None
                            _right_open = _hi_v is None
                            _bar_html = (
                                '<div style="position:relative;height:30px;margin:-10px 0 12px 0;padding:0 2px;">'
                                '<div style="position:absolute;top:14px;left:0;right:0;height:6px;background:#f0f0f0;border-radius:3px;box-shadow:inset 0 1px 2px rgba(0,0,0,0.08);"></div>'
                                + (f'<div style="position:absolute;top:14px;left:0;width:{_pct_left:.2f}%;height:6px;background:linear-gradient(90deg,#f8d7da,#e45756);border-radius:3px 0 0 3px;"></div>' if _pct_left > 0.5 else '')
                                + f'<div style="position:absolute;top:14px;left:{_pct_left:.2f}%;width:{_pct_mid:.2f}%;height:6px;background:linear-gradient(90deg,#b7e4b0,#4caf50,#b7e4b0);border-radius:3px;"></div>'
                                + (f'<div style="position:absolute;top:14px;right:0;width:{_pct_right:.2f}%;height:6px;background:linear-gradient(90deg,#e45756,#f8d7da);border-radius:0 3px 3px 0;"></div>' if _pct_right > 0.5 else '')
                                + (f'<div style="position:absolute;top:10px;left:{_pct_left:.2f}%;width:2px;height:14px;background:#d32f2f;border-radius:1px;"></div><span style="position:absolute;top:-2px;left:{_pct_left:.2f}%;transform:translateX(-50%);font-size:9px;font-weight:600;color:#d32f2f;white-space:nowrap;">{_lo_s}</span>' if not _left_open and _pct_left > 0.5 else '')
                                + (f'<div style="position:absolute;top:10px;left:{100-_pct_right:.2f}%;width:2px;height:14px;background:#d32f2f;border-radius:1px;"></div><span style="position:absolute;top:-2px;left:{100-_pct_right:.2f}%;transform:translateX(-50%);font-size:9px;font-weight:600;color:#d32f2f;white-space:nowrap;">{_hi_s}</span>' if not _right_open and _pct_right > 0.5 else '')
                                + f'<div style="position:absolute;top:12px;left:calc({_pct_cur:.2f}% - 5px);width:10px;height:10px;background:#1976d2;border:2px solid #fff;border-radius:50%;box-shadow:0 1px 3px rgba(0,0,0,0.3);z-index:2;"></div>'
                                + '</div>'
                            )
                            st.markdown(_bar_html, unsafe_allow_html=True)
                        else:
                            st.markdown(f'<div style="margin:-10px 0 12px 0;font-size:10px;color:#999;font-style:italic;">Nedre: {_lo_s} &nbsp;·&nbsp; Øvre: {_hi_s}</div>', unsafe_allow_html=True)

                # Tornado chart + table
                if _sr:
                    st.markdown("---")
                    _constrained = [r for r in _sr if r["room_down"] is not None or r["room_up"] is not None]

                    def _min_room(rr):
                        vv = [v for v in (rr["room_down"], rr["room_up"]) if v is not None]
                        return min(vv) if vv else float("inf")

                    _constrained.sort(key=_min_room)

                    if _constrained:
                        st.markdown(
                            '<h4 style="margin-bottom:2px;">📊 Tornado-diagram</h4>'
                            '<p style="color:#888;font-size:12px;margin-top:0;">Sortert etter sensitivitet – mest sensitiv øverst</p>',
                            unsafe_allow_html=True)

                        _chart_rows: list[dict[str, Any]] = []
                        for _r in _constrained:
                            _b = _r["base"]
                            if not _b:
                                continue
                            if _r["room_down"] is not None:
                                _chart_rows.append({"Parameter": _r["label"], "Endring (%)": -_r["room_down"] / abs(_b) * 100, "Retning": "Kan synke"})
                            if _r["room_up"] is not None:
                                _chart_rows.append({"Parameter": _r["label"], "Endring (%)": _r["room_up"] / abs(_b) * 100, "Retning": "Kan øke"})

                        if _chart_rows:
                            _cdf = pd.DataFrame(_chart_rows)
                            _pord = [r["label"] for r in _constrained]
                            _chart = (alt.Chart(_cdf).mark_bar(cornerRadiusEnd=4, opacity=0.85)
                                .encode(
                                    y=alt.Y("Parameter:N", sort=_pord, title=None, axis=alt.Axis(labelLimit=300, labelFontSize=11)),
                                    x=alt.X("Endring (%):Q", title="Tillatt endring fra nåverdi (%)", axis=alt.Axis(grid=True, gridOpacity=0.15)),
                                    color=alt.Color("Retning:N", scale=alt.Scale(domain=["Kan synke", "Kan øke"], range=["#ef5350", "#66bb6a"]),
                                        legend=alt.Legend(orient="top", title=None, labelFontSize=11)),
                                    tooltip=[alt.Tooltip("Parameter:N"), alt.Tooltip("Retning:N"), alt.Tooltip("Endring (%):Q", format=".2f")])
                                .properties(height=max(len(_constrained) * 34, 200)).configure_view(strokeWidth=0))
                            st.altair_chart(_chart, width="stretch")

                        _rows_out = []
                        for _r in (_constrained or _sr):
                            _rows_out.append({"Parameter": _r["label"], "Nåverdi": _format_value(_r["base"]),
                                "Nedre grense": "∞" if _r["min"] is None else _format_value(_r["min"]),
                                "Øvre grense": "∞" if _r["max"] is None else _format_value(_r["max"]),
                                "Rom ned": "∞" if _r["room_down"] is None else _format_value(_r["room_down"]),
                                "Rom opp": "∞" if _r["room_up"] is None else _format_value(_r["room_up"])})
                        if _rows_out:
                            with st.expander("Grenseverdi-tabell"):
                                st.dataframe(pd.DataFrame(_rows_out), width="stretch", hide_index=True)

                    _unconstrained = [r for r in _sr if r["room_down"] is None and r["room_up"] is None]
                    if _unconstrained:
                        with st.expander(f"Ubegrensede parametere ({len(_unconstrained)} stk)"):
                            st.caption("Kan variere fritt innenfor søkeområdet uten å bryte kravene.")
                            _unc_df = pd.DataFrame([{"Parameter": r["label"], "Nåverdi": _format_value(r["base"]), "Enhet": r["unit"]} for r in _unconstrained])
                            st.dataframe(_unc_df, width="stretch", hide_index=True)


# ===================================================================
# Page routing — list view or selected calculator
# ===================================================================

_selected = st.session_state.get("excel_ark_selected")

if _selected is None:
    st.markdown("---")
    st.markdown("#### Tilgjengelige beregningsark")
    for sheet in CALC_SHEETS:
        if st.button(
            f'{sheet["icon"]}  {sheet["name"]}',
            key=f'sheet_{sheet["id"]}',
            use_container_width=True,
            help=sheet["description"],
        ):
            st.session_state["excel_ark_selected"] = sheet["id"]
            st.rerun()

    st.markdown("---")
    st.markdown("#### Planlagte regneark")
    st.markdown("""
- 🏗️ Ramme- og pelekapasitet  
- 📐 Setningsberegning  
- 🔩 Forankringskapasitet  
- 📋 Grunnundersøkelses-sammenstilling  
""")
else:
    if st.button("← Tilbake til oversikt"):
        st.session_state["excel_ark_selected"] = None
        st.rerun()

    if _selected == "torrmur":
        _render_torrmur()
