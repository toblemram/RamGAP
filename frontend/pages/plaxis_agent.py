# -*- coding: utf-8 -*-
"""
GAPI — AI-drevet PLAXIS-assistent  (ny pipeline-flyt)
======================================================
Flyt:
  0. Tilkobling til PLAXIS
  1. Bruker skriver inn forespørsel
  2. GAPI henter kontekst + lager plan  (Step 0+1)
  3. Bruker godkjenner / avviser planen  (Step 2)
  4. GAPI genererer kode, validerer, kjører  (Step 3+4+5)
  5. Resultater vises i funn-panelet
  Observer oppdaterer læringslogg i databasen etter kjøring  (Step 6)
"""

import re
import json
import streamlit as st
import streamlit.components.v1 as components
from components.api_client import APIClient
from components.auth import require_username

USERNAME = require_username()
api = APIClient()

st.title("🤖 GAPI")

# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------
_defaults = {
    "pa_messages":      [],
    "pa_connected":     False,
    "pa_session_id":    "agent_default",
    "pa_pdf_text":      None,
    "pa_pdf_name":      None,
    # Pipeline state
    "pa_stage":         "idle",   # idle | planning | awaiting_approval | executing | done
    "pa_pending_plan":  None,     # plan dict while awaiting approval
    "pa_context_summary": None,
    "pa_last_message":  "",
    # Model snapshot
    "pa_model_info":    None,     # cached snapshot from /snapshot endpoint
}
for k, v in _defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ---------------------------------------------------------------------------
# Connection panel
# ---------------------------------------------------------------------------

if not st.session_state.pa_connected:
    st.info("Koble til PLAXIS for å starte GAPI. Sørg for at **PlaxisWorker** kjører på maskinen din.")
    with st.container(border=True):
        st.subheader("🔌 Koble til PLAXIS")
        col_port, col_pwd = st.columns(2)
        with col_port:
            port = st.number_input("Port (Input)", value=10000, min_value=1, max_value=65535, key="pa_port")
        with col_pwd:
            password = st.text_input("Passord (Code)", type="password", key="pa_pwd")
        output_port = st.number_input("Port (Output)", value=10001, min_value=1, max_value=65535, key="pa_output_port")
        col_btn, col_status = st.columns([1, 2])
        with col_btn:
            if st.button("🔌 Koble til", use_container_width=True, type="primary"):
                with col_status:
                    with st.spinner("Kobler til…"):
                        res = api.plaxis_agent_connect(
                            port=port, password=password,
                            session_id=st.session_state.pa_session_id,
                            output_port=output_port, output_password=password,
                        )
                    if res.get("success"):
                        st.session_state.pa_connected = True
                        st.session_state.pa_model_info = res.get("model_info") or {}
                        st.rerun()
                    else:
                        st.error(res.get("error", "Tilkobling feilet"))
    st.stop()


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

with st.sidebar:
    st.success("✅ PLAXIS tilkoblet")
    if st.button("🔌 Koble fra", use_container_width=True):
        for k in ["pa_connected", "pa_messages",
                  "pa_stage", "pa_pending_plan", "pa_context_summary", "pa_model_info"]:
            st.session_state[k] = _defaults.get(k, None if k != "pa_stage" else "idle")
        st.rerun()

    # ── Model snapshot ──────────────────────────────────────────────
    st.divider()
    st.markdown("### 🏗️ Modellinfo")
    mi = st.session_state.pa_model_info
    if mi:
        proj = mi.get("project", {})
        if proj.get("name"):
            st.caption(f"📁 **{proj['name']}**")
        if proj.get("title"):
            st.caption(f"_{proj['title']}_")

        phases = mi.get("phases", [])
        structs = mi.get("structures", {})
        geo = mi.get("geometry", {})
        mats = mi.get("materials", {})
        mesh = mi.get("mesh", {})

        col_a, col_b = st.columns(2)
        with col_a:
            st.metric("Faser", len(phases))
            st.metric("Plater", len(structs.get("plates", [])))
            st.metric("Peler/beams", len(structs.get("embedded_beams", [])))
        with col_b:
            st.metric("Materialer", len(mats))
            n2n = len(structs.get("n2n_anchors", []))
            fea = len(structs.get("fixed_end_anchors", []))
            st.metric("Ankere", n2n + fea)
            if mesh.get("n_elements"):
                st.metric("Elementer", mesh["n_elements"])

        with st.expander("📐 Geometri", expanded=False):
            bhs = geo.get("boreholes", [])
            if bhs:
                for bh in bhs:
                    st.caption(f"Boring x={bh.get('x')}, GVN={bh.get('head')}")
                    for lay in bh.get("layers", []):
                        st.caption(f"  {lay.get('material','?')}:  {lay.get('top')} → {lay.get('bottom')} m")
            x0, x1 = geo.get("xmin"), geo.get("xmax")
            y0, y1 = geo.get("ymin"), geo.get("ymax")
            if x0 is not None:
                st.caption(f"Modellgrense X: {x0} … {x1}  Y: {y0} … {y1}")

        with st.expander("🧱 Materialer", expanded=False):
            for name, md in list(mats.items())[:20]:
                if name.startswith("_"): continue
                params = md.get("params", {})
                key_vals = " | ".join(f"{k}={v}" for k,v in list(params.items())[:4])
                st.caption(f"**{name}** ({md.get('type','?')})  {key_vals}")

        with st.expander("📊 Faser", expanded=False):
            for ph in phases:
                status_icon = {"Completed":"✅","Not finished yet":"⬜","Failed":"❌"}.get(
                    str(ph.get("status","")),"❓")
                st.caption(f"{status_icon} {ph.get('name','')}  [{ph.get('calc_type','')}]")

        with st.expander("📈 Resultater", expanded=False):
            results = mi.get("results", {})
            if results:
                for ph_name, pd in results.items():
                    vals = "  ".join(f"{k}={v}" for k,v in pd.items())
                    st.caption(f"**{ph_name}**: {vals}")
            else:
                st.caption("Ingen output-resultater tilgjengelig.")

    if st.button("🔄 Oppdater modellinfo", use_container_width=True, key="pa_refresh_snap"):
        with st.spinner("Henter modellinfo…"):
            snap_res = api.plaxis_agent_snapshot(session_id=st.session_state.pa_session_id)
        if snap_res.get("success") and snap_res.get("snapshot"):
            st.session_state.pa_model_info = snap_res["snapshot"]
            st.rerun()
        else:
            st.error(snap_res.get("error", "Snapshot feilet"))

    # Auto-fetch snapshot if not loaded yet
    if st.session_state.pa_model_info is None:
        with st.spinner("Laster modellinfo…"):
            snap_res = api.plaxis_agent_snapshot(session_id=st.session_state.pa_session_id)
        if snap_res.get("success") and snap_res.get("snapshot"):
            st.session_state.pa_model_info = snap_res["snapshot"]
            st.rerun()

    st.divider()
    st.markdown("### 📄 Last opp dokument")
    uploaded = st.file_uploader("PDF for ekstra kontekst", type=["pdf"], key="pa_pdf_upload")
    if uploaded and uploaded.name != st.session_state.pa_pdf_name:
        with st.spinner("Leser PDF…"):
            res = api.plaxis_agent_upload_pdf(uploaded.getvalue(), uploaded.name)
        if "error" in res:
            st.error(res["error"])
        else:
            st.session_state.pa_pdf_text = res.get("text", "")
            st.session_state.pa_pdf_name = uploaded.name
            st.success(f"📄 {uploaded.name}")
    if st.session_state.pa_pdf_text:
        st.caption(f"Aktiv: **{st.session_state.pa_pdf_name}**")
        if st.button("🗑️ Fjern PDF"):
            st.session_state.pa_pdf_text = None
            st.session_state.pa_pdf_name = None
            st.rerun()

    st.divider()
    if st.button("🗑️ Ny samtale", use_container_width=True):
        st.session_state.pa_messages = []
        st.session_state.pa_stage = "idle"
        st.session_state.pa_pending_plan = None
        st.rerun()

    # Learnings from DB
    st.divider()
    st.markdown("### 📗 Læringslogg")
    learning_res = api.plaxis_agent_get_learnings(scope="global")
    learning = learning_res.get("learning")
    if learning:
        updated = learning.get("updated_at", "")[:10] if learning.get("updated_at") else ""
        st.caption(f"Sist oppdatert: {updated}")
        with st.expander("Vis læringslogg", expanded=False):
            st.markdown(learning.get("content", "Ingen innhold"))
    else:
        st.caption("Ingen læringslogg ennå.")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_history() -> list:
    hist = []
    for msg in st.session_state.pa_messages:
        if msg["role"] == "user":
            hist.append({"role": "user", "content": msg["content"]})
        elif msg["role"] == "assistant":
            hist.append({"role": "assistant",
                         "content": msg.get("code") or msg.get("content", "")})
    return hist


_RISK_ICON  = {"lav": "✅", "medium": "⚠️", "høy": "🔴"}
_RISK_COLOR = {"lav": "green", "medium": "orange", "høy": "red"}

_VERDICT_COLOR = {"success": "green", "partial": "orange", "wrong": "orange", "error": "red"}
_VERDICT_ICON  = {"success": "✅", "partial": "⚠️", "wrong": "🔄", "error": "❌"}


def _render_verdict(verdict: dict, expected_output: str = ""):
    """Render the result-evaluation verdict block under an execution message."""
    status     = verdict.get("status", "error")
    forklaring = verdict.get("forklaring", "")
    mangler    = verdict.get("mangler", [])
    hint       = verdict.get("retry_hint", "")
    icon       = _VERDICT_ICON.get(status, "❓")
    color      = _VERDICT_COLOR.get(status, "gray")

    label = {
        "success": "Output matcher forventet",
        "partial": "Delvis resultat",
        "wrong":   "Feil output — kjørte på nytt",
        "error":   "Kjøring feilet",
    }.get(status, status)

    st.markdown(
        f"<div style='border-left:3px solid {color};padding:6px 10px;margin:4px 0;"
        f"border-radius:4px;background:rgba(0,0,0,0.03)'>"
        f"<b>{icon} Resultat-evaluering: {label}</b></div>",
        unsafe_allow_html=True,
    )

    if forklaring:
        st.caption(forklaring)

    if expected_output:
        st.caption(f"Forventet: _{expected_output}_")

    if mangler:
        with st.expander("📋 Hva mangler / er feil", expanded=(status != "success")):
            for m in mangler:
                st.markdown(f"• {m}")

    if hint and status not in ("success",):
        with st.expander("💡 Hint til neste forsøk", expanded=False):
            st.code(hint, language="text")




def _render_plan(plan: dict, ctx_summary: dict = None):
    """Render a plan dict as a structured info block in the chat."""
    st.markdown(f"**📋 Plan: {plan.get('forståelse', '')}**")

    steg = plan.get("steg", [])
    for s in steg:
        risk   = s.get("risiko", "medium")
        icon   = _RISK_ICON.get(risk, "⚠️")
        color  = _RISK_COLOR.get(risk, "orange")
        st.markdown(
            f"{icon} **Steg {s['nr']}**: {s['beskrivelse']}  "
            f"<span style='color:{color};font-size:0.8em'>({risk} risiko)</span>",
            unsafe_allow_html=True,
        )

    if plan.get("standard_advarsler"):
        with st.expander("📙 Standard-advarsler", expanded=True):
            for w in plan["standard_advarsler"]:
                st.markdown(f"• {w}")

    if plan.get("modellerings_tips"):
        with st.expander("📓 Modelleringstips", expanded=False):
            for t in plan["modellerings_tips"]:
                st.markdown(f"• {t}")

    if ctx_summary:
        badges = []
        if ctx_summary.get("has_learnings"):
            badges.append("📗 Læringslogg")
        n_std = ctx_summary.get("standards_found", 0)
        if n_std:
            badges.append(f"📙 {n_std} standardseksjoner")
        n_man = ctx_summary.get("manual_docs_found", 0)
        if n_man:
            badges.append(f"📓 {n_man} tutorial-seksjoner")
        if badges:
            st.caption("Kontekst brukt: " + " · ".join(badges))


def _render_plan_approval():
    """Render the plan approval buttons."""
    plan = st.session_state.pa_pending_plan
    if not plan:
        return

    st.divider()
    st.markdown("#### 🤖 GAPI er klar til å kjøre — godkjenn planen:")

    missing = plan.get("manglende_info", [])
    if missing:
        st.warning("⚠️ Mangler informasjon:\n" + "\n".join(f"• {m}" for m in missing))

    col_run, col_edit, col_cancel = st.columns(3)
    with col_run:
        if st.button("▶️ Kjør plan", type="primary", use_container_width=True, key="pa_approve"):
            _execute_plan()
    with col_edit:
        if st.button("✏️ Endre forespørsel", use_container_width=True, key="pa_edit"):
            st.session_state.pa_stage = "idle"
            st.session_state.pa_pending_plan = None
            st.rerun()
    with col_cancel:
        if st.button("❌ Avbryt", use_container_width=True, key="pa_cancel"):
            st.session_state.pa_stage = "idle"
            st.session_state.pa_pending_plan = None
            st.session_state.pa_messages.append({
                "role": "assistant",
                "content": "Plan avbrutt.",
            })
            st.rerun()


# ---------------------------------------------------------------------------
# Geometry canvas renderer
# ---------------------------------------------------------------------------

_SOIL_COLORS = {
    "fyll":    "#C2956B", "sand":    "#E8D5A3", "grus":    "#D4A76A",
    "leire":   "#8DAA6F", "silt":    "#B5C98E", "berg":    "#A0A0A0",
    "morene":  "#9B8B7A", "torv":    "#5C4033", "ks":      "#F0E68C",
    "kvikkleire": "#7FBF7F",
}

def _soil_color(material_name: str) -> str:
    if not material_name:
        return "#B0B0B0"
    low = material_name.lower()
    for key, color in _SOIL_COLORS.items():
        if key in low:
            return color
    return "#C0C0C0"


def _build_geometry_html(mi: dict, width: int = 700, height: int = 480) -> str:
    """Build a self-contained HTML/Canvas cross-section from snapshot model_info."""
    geo = mi.get("geometry", {})
    structs = mi.get("structures", {})

    xmin = geo.get("xmin", -20)
    xmax = geo.get("xmax", 30)
    ymin = geo.get("ymin", -35)
    ymax = geo.get("ymax", 8)

    boreholes = geo.get("boreholes", [])
    plates = structs.get("plates", [])
    n2n_anchors = structs.get("n2n_anchors", [])
    embedded_beams = structs.get("embedded_beams", [])
    fea_anchors = structs.get("fixed_end_anchors", [])

    # Build layer list for drawing (full-width soil bands)
    layers_js = []
    if boreholes:
        bh = boreholes[0]
        gwl = bh.get("head")
        for lay in bh.get("layers", []):
            top = lay.get("top")
            bot = lay.get("bottom")
            mat = lay.get("material", "?")
            if top is not None and bot is not None:
                layers_js.append({
                    "top": top, "bottom": bot, "material": mat,
                    "color": _soil_color(mat),
                })
    else:
        gwl = None

    # Structures for JS
    plates_js = []
    for p in plates:
        if p.get("x1") is not None:
            plates_js.append({
                "name": p.get("name", ""), "x1": p["x1"], "y1": p["y1"],
                "x2": p["x2"], "y2": p["y2"], "material": p.get("material", ""),
            })

    anchors_js = []
    for a in n2n_anchors:
        if a.get("x1") is not None:
            anchors_js.append({
                "name": a.get("name", ""), "x1": a["x1"], "y1": a["y1"],
                "x2": a["x2"], "y2": a["y2"], "material": a.get("material", ""),
            })

    beams_js = []
    for b in embedded_beams:
        if b.get("x1") is not None:
            beams_js.append({
                "name": b.get("name", ""), "x1": b["x1"], "y1": b["y1"],
                "x2": b["x2"], "y2": b["y2"], "material": b.get("material", ""),
            })

    data = json.dumps({
        "xmin": xmin, "xmax": xmax, "ymin": ymin, "ymax": ymax,
        "layers": layers_js, "gwl": gwl,
        "plates": plates_js, "anchors": anchors_js, "beams": beams_js,
    }, ensure_ascii=False)

    return f"""<!DOCTYPE html>
<html><head><style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ background:transparent; font-family:"Source Sans Pro",system-ui,sans-serif; }}
canvas {{ display:block; }}
.legend {{ display:flex; flex-wrap:wrap; gap:6px 14px; padding:6px 4px 2px; }}
.leg-item {{ display:flex; align-items:center; gap:4px; font-size:11px; color:#555; }}
.leg-swatch {{ width:12px; height:12px; border-radius:2px; border:1px solid rgba(0,0,0,0.15); }}
.tooltip {{ position:absolute; pointer-events:none; background:rgba(30,30,30,0.92); color:#fff;
  font-size:11px; padding:4px 8px; border-radius:4px; display:none; white-space:nowrap; z-index:10; }}
</style></head><body>
<div style="position:relative">
  <canvas id="cv" width="{width}" height="{height}"></canvas>
  <div class="tooltip" id="tt"></div>
</div>
<div class="legend" id="leg"></div>
<script>
(function() {{
const D = {data};
const cv = document.getElementById('cv');
const ctx = cv.getContext('2d');
const tt = document.getElementById('tt');
const W = cv.width, H = cv.height;
const pad = {{top:30, right:30, bottom:36, left:50}};
const pw = W - pad.left - pad.right;
const ph = H - pad.top - pad.bottom;

function tx(x) {{ return pad.left + (x - D.xmin) / (D.xmax - D.xmin) * pw; }}
function ty(y) {{ return pad.top + (D.ymax - y) / (D.ymax - D.ymin) * ph; }}

// --- Background ---
ctx.fillStyle = '#f8f9fa';
ctx.fillRect(0, 0, W, H);

// --- Soil layers (full width) ---
const seenMats = new Map();
for (const L of D.layers) {{
  const y0 = ty(L.top), y1 = ty(L.bottom);
  ctx.fillStyle = L.color;
  ctx.fillRect(pad.left, y0, pw, y1 - y0);
  // Subtle hatch pattern for soil
  ctx.save();
  ctx.globalAlpha = 0.06;
  ctx.strokeStyle = '#000';
  ctx.lineWidth = 0.5;
  for (let hx = pad.left; hx < pad.left + pw; hx += 8) {{
    ctx.beginPath(); ctx.moveTo(hx, y0); ctx.lineTo(hx + (y1-y0)*0.3, y1); ctx.stroke();
  }}
  ctx.restore();
  // Label
  const midY = (y0 + y1) / 2;
  ctx.fillStyle = 'rgba(0,0,0,0.65)';
  ctx.font = '600 11px "Source Sans Pro",sans-serif';
  ctx.textAlign = 'left';
  ctx.textBaseline = 'middle';
  if (y1 - y0 > 14) {{
    ctx.fillText(L.material, pad.left + 6, midY);
  }}
  seenMats.set(L.material, L.color);
}}

// --- Ground water level ---
if (D.gwl !== null && D.gwl !== undefined) {{
  const gy = ty(D.gwl);
  ctx.save();
  ctx.setLineDash([6, 3]);
  ctx.strokeStyle = '#2196F3';
  ctx.lineWidth = 1.5;
  ctx.beginPath(); ctx.moveTo(pad.left, gy); ctx.lineTo(pad.left + pw, gy); ctx.stroke();
  ctx.restore();
  // GWL label
  ctx.fillStyle = '#1565C0';
  ctx.font = '600 10px "Source Sans Pro",sans-serif';
  ctx.textAlign = 'right';
  ctx.fillText('GVN ' + D.gwl.toFixed(1), pad.left + pw - 4, gy - 5);
}}

// --- Grid lines ---
ctx.save();
ctx.strokeStyle = 'rgba(0,0,0,0.08)';
ctx.lineWidth = 0.5;
// Horizontal
const yStep = Math.max(1, Math.ceil((D.ymax - D.ymin) / 10));
for (let y = Math.ceil(D.ymin / yStep) * yStep; y <= D.ymax; y += yStep) {{
  const py = ty(y);
  ctx.beginPath(); ctx.moveTo(pad.left, py); ctx.lineTo(pad.left + pw, py); ctx.stroke();
}}
// Vertical
const xStep = Math.max(1, Math.ceil((D.xmax - D.xmin) / 10));
for (let x = Math.ceil(D.xmin / xStep) * xStep; x <= D.xmax; x += xStep) {{
  const px = tx(x);
  ctx.beginPath(); ctx.moveTo(px, pad.top); ctx.lineTo(px, pad.top + ph); ctx.stroke();
}}
ctx.restore();

// --- Axes ---
ctx.strokeStyle = '#333';
ctx.lineWidth = 1;
ctx.beginPath();
ctx.moveTo(pad.left, pad.top);
ctx.lineTo(pad.left, pad.top + ph);
ctx.lineTo(pad.left + pw, pad.top + ph);
ctx.stroke();

// Tick labels
ctx.fillStyle = '#666';
ctx.font = '10px "Source Sans Pro",sans-serif';
ctx.textAlign = 'center';
for (let x = Math.ceil(D.xmin / xStep) * xStep; x <= D.xmax; x += xStep) {{
  ctx.fillText(x.toString(), tx(x), pad.top + ph + 14);
}}
ctx.textAlign = 'right';
ctx.textBaseline = 'middle';
for (let y = Math.ceil(D.ymin / yStep) * yStep; y <= D.ymax; y += yStep) {{
  ctx.fillText(y.toString(), pad.left - 6, ty(y));
}}
// Axis labels
ctx.fillStyle = '#444';
ctx.font = '600 11px "Source Sans Pro",sans-serif';
ctx.textAlign = 'center';
ctx.fillText('x [m]', pad.left + pw/2, H - 4);
ctx.save();
ctx.translate(12, pad.top + ph/2);
ctx.rotate(-Math.PI/2);
ctx.fillText('y [m]', 0, 0);
ctx.restore();

// --- Plates (thick line with glow) ---
const hitTargets = [];
for (const p of D.plates) {{
  const px1 = tx(p.x1), py1 = ty(p.y1), px2 = tx(p.x2), py2 = ty(p.y2);
  // Shadow/glow
  ctx.save();
  ctx.shadowColor = 'rgba(0,100,200,0.3)';
  ctx.shadowBlur = 6;
  ctx.strokeStyle = '#1565C0';
  ctx.lineWidth = 4;
  ctx.lineCap = 'round';
  ctx.beginPath(); ctx.moveTo(px1, py1); ctx.lineTo(px2, py2); ctx.stroke();
  ctx.restore();
  // Core line
  ctx.strokeStyle = '#0D47A1';
  ctx.lineWidth = 2.5;
  ctx.lineCap = 'round';
  ctx.beginPath(); ctx.moveTo(px1, py1); ctx.lineTo(px2, py2); ctx.stroke();
  // End caps
  for (const [cx, cy] of [[px1,py1],[px2,py2]]) {{
    ctx.fillStyle = '#0D47A1';
    ctx.beginPath(); ctx.arc(cx, cy, 3.5, 0, Math.PI*2); ctx.fill();
  }}
  hitTargets.push({{ type:'plate', x1:px1, y1:py1, x2:px2, y2:py2,
    label: p.name + ' (' + (p.material||'') + ')' }});
}}

// --- N2N Anchors (dashed, orange) ---
for (const a of D.anchors) {{
  const ax1 = tx(a.x1), ay1 = ty(a.y1), ax2 = tx(a.x2), ay2 = ty(a.y2);
  ctx.save();
  ctx.setLineDash([5, 3]);
  ctx.strokeStyle = '#E65100';
  ctx.lineWidth = 2;
  ctx.lineCap = 'round';
  ctx.beginPath(); ctx.moveTo(ax1, ay1); ctx.lineTo(ax2, ay2); ctx.stroke();
  ctx.restore();
  // Anchor symbol (diamond)
  const mx = (ax1+ax2)/2, my = (ay1+ay2)/2;
  ctx.fillStyle = '#E65100';
  ctx.beginPath();
  ctx.moveTo(mx, my-5); ctx.lineTo(mx+4, my); ctx.lineTo(mx, my+5); ctx.lineTo(mx-4, my);
  ctx.closePath(); ctx.fill();
  hitTargets.push({{ type:'anchor', x1:ax1, y1:ay1, x2:ax2, y2:ay2,
    label: a.name + ' (' + (a.material||'') + ')' }});
}}

// --- Embedded beams (dotted, purple) ---
for (const b of D.beams) {{
  const bx1 = tx(b.x1), by1 = ty(b.y1), bx2 = tx(b.x2), by2 = ty(b.y2);
  ctx.save();
  ctx.setLineDash([3, 4]);
  ctx.strokeStyle = '#6A1B9A';
  ctx.lineWidth = 2.5;
  ctx.lineCap = 'round';
  ctx.beginPath(); ctx.moveTo(bx1, by1); ctx.lineTo(bx2, by2); ctx.stroke();
  ctx.restore();
  hitTargets.push({{ type:'beam', x1:bx1, y1:by1, x2:bx2, y2:by2,
    label: b.name + ' (' + (b.material||'') + ')' }});
}}

// --- Title ---
ctx.fillStyle = '#222';
ctx.font = '700 13px "Source Sans Pro",sans-serif';
ctx.textAlign = 'left';
ctx.fillText('Tverrsnitt', pad.left, 16);

// --- Legend ---
const leg = document.getElementById('leg');
const items = [];
seenMats.forEach((c, n) => {{
  items.push('<span class="leg-item"><span class="leg-swatch" style="background:'+c+'"></span>'+n+'</span>');
}});
if (D.plates.length) items.push('<span class="leg-item"><span class="leg-swatch" style="background:#0D47A1"></span>Plate</span>');
if (D.anchors.length) items.push('<span class="leg-item"><span class="leg-swatch" style="background:#E65100"></span>Anker</span>');
if (D.beams.length) items.push('<span class="leg-item"><span class="leg-swatch" style="background:#6A1B9A"></span>Beam</span>');
if (D.gwl !== null) items.push('<span class="leg-item"><span class="leg-swatch" style="background:#2196F3"></span>GVN</span>');
leg.innerHTML = items.join('');

// --- Tooltip on hover ---
function distToSegment(px, py, x1, y1, x2, y2) {{
  const dx = x2-x1, dy = y2-y1;
  const len2 = dx*dx + dy*dy;
  if (len2 === 0) return Math.hypot(px-x1, py-y1);
  let t = ((px-x1)*dx + (py-y1)*dy) / len2;
  t = Math.max(0, Math.min(1, t));
  return Math.hypot(px - (x1+t*dx), py - (y1+t*dy));
}}

cv.addEventListener('mousemove', function(e) {{
  const rect = cv.getBoundingClientRect();
  const mx = e.clientX - rect.left, my = e.clientY - rect.top;
  let best = null, bestDist = 12;
  for (const h of hitTargets) {{
    const d = distToSegment(mx, my, h.x1, h.y1, h.x2, h.y2);
    if (d < bestDist) {{ bestDist = d; best = h; }}
  }}
  if (best) {{
    tt.style.display = 'block';
    tt.style.left = (mx + 12) + 'px';
    tt.style.top  = (my - 20) + 'px';
    tt.textContent = best.label;
  }} else {{
    tt.style.display = 'none';
  }}
}});
cv.addEventListener('mouseleave', function() {{ tt.style.display = 'none'; }});
}})();
</script></body></html>"""


def _render_geometry(mi: dict):
    """Render the cross-section canvas for the model."""
    geo = mi.get("geometry", {})
    if not geo.get("xmin") and not mi.get("structures", {}).get("plates"):
        st.caption("Ingen geometridata tilgjengelig.")
        return
    html = _build_geometry_html(mi, width=680, height=440)
    components.html(html, height=490, scrolling=False)


def _render_phases_panel(mi: dict):
    """Render phase cards."""
    phases = mi.get("phases", [])
    if not phases:
        st.caption("Ingen faser.")
        return

    _CALC_TYPE_MAP = {
        "1": "K0", "2": "Gravity", "3": "Flow only", "4": "Plastic",
        "5": "Consolidation", "6": "Dynamic", "7": "Safety (SRM)",
        "8": "Updated mesh", "9": "Fully coupled",
    }

    for ph in phases:
        status = str(ph.get("status", ""))
        icon = {"Completed": "✅", "Not finished yet": "⬜", "Failed": "❌"}.get(status, "⚪")
        calc_raw = str(ph.get("calc_type", ""))
        calc_name = _CALC_TYPE_MAP.get(calc_raw, calc_raw)
        name = ph.get("name", "Fase")
        number = ph.get("number", "")

        st.markdown(
            f"<div style='display:flex;align-items:center;gap:8px;padding:3px 0;'>"
            f"<span style='font-size:14px'>{icon}</span>"
            f"<span style='font-size:12px;color:#888;min-width:20px'>{number}</span>"
            f"<span style='font-size:13px;font-weight:500'>{name}</span>"
            f"<span style='font-size:11px;color:#999;margin-left:auto'>{calc_name}</span>"
            f"</div>",
            unsafe_allow_html=True,
        )


def _start_planning(user_input: str):
    """Step 0+1: gather context and create plan."""
    st.session_state.pa_messages.append({"role": "user", "content": user_input})
    st.session_state.pa_last_message = user_input
    st.session_state.pa_stage = "planning"

    with st.spinner("🔍 GAPI analyserer og lager plan… (søker i standarder, manual, referanse)"):
        res = api.plaxis_agent_plan(
            message=user_input,
            session_id=st.session_state.pa_session_id,
            username=USERNAME,
            history=_build_history()[:-1],
            pdf_text=st.session_state.pa_pdf_text,
        )

    if "error" in res:
        st.session_state.pa_messages.append({
            "role": "assistant",
            "content": f"❌ Planlegging feilet: {res['error']}",
        })
        st.session_state.pa_stage = "idle"
        st.rerun()
        return

    plan = res.get("plan", {})
    ctx_summary = res.get("context_summary", {})

    # Check if plan asks for more info
    if plan.get("manglende_info"):
        info_list = "\n".join(f"• {m}" for m in plan["manglende_info"])
        st.session_state.pa_messages.append({
            "role": "assistant",
            "content": f"⚠️ Jeg trenger mer informasjon før jeg kan lage en plan:\n\n{info_list}",
        })
        st.session_state.pa_stage = "idle"
        st.rerun()
        return

    # Store plan, show approval UI
    st.session_state.pa_pending_plan = plan
    st.session_state.pa_context_summary = ctx_summary
    st.session_state.pa_stage = "awaiting_approval"

    # Add plan to chat as assistant message
    st.session_state.pa_messages.append({
        "role": "assistant",
        "plan": plan,
        "context_summary": ctx_summary,
    })
    st.rerun()


def _execute_plan():
    """Steps 3+4+5+6: generate code, validate, execute, update learnings."""
    st.session_state.pa_stage = "executing"

    n_steps = len(st.session_state.pa_pending_plan.get("steg", []))
    expected_output = st.session_state.pa_pending_plan.get("ønsket_output", "")
    with st.spinner(f"⚙️ Kjører {n_steps} steg… dette kan ta litt tid"):
        res = api.plaxis_agent_execute_plan(
            session_id=st.session_state.pa_session_id,
            username=USERNAME,
            history=_build_history(),
            pdf_text=st.session_state.pa_pdf_text,
        )

    code    = res.get("code", "")
    output  = res.get("output", "")
    error   = res.get("error")
    success = res.get("success", False)
    verdict = res.get("verdict", {})
    attempts = res.get("attempts", 1)

    # Build result summary text based on verdict
    v_status   = verdict.get("status", "success" if success else "error")
    v_explain  = verdict.get("forklaring", "")
    v_mangler  = verdict.get("mangler", [])
    v_hint     = verdict.get("retry_hint", "")

    _STATUS_ICON = {"success": "✅", "partial": "⚠️", "wrong": "🔄", "error": "❌"}
    _STATUS_TEXT = {
        "success": "Output matcher forventet resultat",
        "partial": "Delvis resultat — noe mangler",
        "wrong":   "Feil type output — kjørte på nytt",
        "error":   "Kjøring feilet",
    }
    status_icon = _STATUS_ICON.get(v_status, "❓")
    status_text = _STATUS_TEXT.get(v_status, v_status)

    if error and not success:
        content_line = f"❌ Kjøring feilet: {error}"
    else:
        content_line = f"{status_icon} {status_text}"

    msg: dict = {
        "role": "assistant",
        "code": code,
        "output": output,
        "error": error,
        "verdict": verdict,
        "expected_output": expected_output,
        "attempts": attempts,
        "steps": res.get("steps", n_steps),
        "content": content_line,
    }

    st.session_state.pa_messages.append(msg)
    st.session_state.pa_stage = "idle"
    st.session_state.pa_pending_plan = None
    st.rerun()



# ---------------------------------------------------------------------------
# Layout: LEFT = chat   |   RIGHT = model view
# ---------------------------------------------------------------------------

col_chat, col_model = st.columns([3, 2])


# ======================= RIGHT: MODEL VIEW =======================

with col_model:
    mi = st.session_state.pa_model_info
    if mi:
        tab_geo, tab_phases = st.tabs(["📐 Tverrsnitt", "📊 Faser"])
        with tab_geo:
            _render_geometry(mi)
        with tab_phases:
            _render_phases_panel(mi)
    else:
        st.caption("Koble til PLAXIS for å se modellvisning.")


# ======================= LEFT: CHAT =======================

with col_chat:
    st.markdown("### 💬 Chat")

    # --- Chat history ---
    chat_container = st.container(height=500)
    with chat_container:
        for msg in st.session_state.pa_messages:
            if msg["role"] == "user":
                with st.chat_message("user"):
                    st.markdown(msg["content"])
            elif msg["role"] == "assistant":
                with st.chat_message("assistant", avatar="🤖"):
                    if msg.get("content"):
                        st.markdown(msg["content"])
                    if msg.get("plan"):
                        _render_plan(msg["plan"], msg.get("context_summary"))
                    if msg.get("verdict"):
                        _render_verdict(msg["verdict"], msg.get("expected_output", ""))
                    if msg.get("code"):
                        with st.expander("🐍 Vis kode", expanded=False):
                            st.code(msg["code"], language="python")
                    if msg.get("output"):
                        raw = msg["output"]
                        items = [
                            line.split("ITEM:", 1)[1].strip()
                            for line in raw.splitlines()
                            if "ITEM:" in line
                        ]
                        if items and msg.get("verdict", {}).get("status") in ("success", "partial"):
                            with st.expander("📊 Resultater", expanded=True):
                                for item in items:
                                    st.markdown(f"• {item}")
                        elif items:
                            with st.expander("📊 Output", expanded=True):
                                for item in items:
                                    st.markdown(f"• {item}")
                        with st.expander("📄 Rå output", expanded=False):
                            st.code(raw[:3000], language="text")
                    if msg.get("error"):
                        st.error(f"Feil: {msg['error']}")
                    meta = []
                    if msg.get("attempts", 0) > 1:
                        meta.append(f"🔄 {msg['attempts']} forsøk")
                    if msg.get("steps", 0) > 1:
                        meta.append(f"📊 {msg['steps']} steg")
                    if meta:
                        st.caption(" · ".join(meta))

    # --- Plan approval UI (shown inline when awaiting) ---
    if st.session_state.pa_stage == "awaiting_approval":
        _render_plan_approval()

    # --- Chat input (disabled while pipeline is running) ---
    disabled = st.session_state.pa_stage in ("planning", "executing")
    user_input = st.chat_input(
        "Beskriv hva du vil gjøre i PLAXIS…",
        disabled=disabled,
        key="pa_chat_input",
    )

    if user_input and st.session_state.pa_stage == "idle":
        _start_planning(user_input)


