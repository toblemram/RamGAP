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
import csv
import math
import os
from itertools import combinations
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import plotly.graph_objects as go
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
    pid = project.get("id") if project else None
    folder_path = project.get("folder_path") if project else None

    # ── Option 1: Use SND files already loaded from project upload ────
    snd_contents = st.session_state.get(f"_snd_contents_{pid}") if pid else None
    if snd_contents:
        st.info(f"📁 Prosjektet har **{len(snd_contents)}** SND-filer lastet inn.")
        if st.button("📂 Bruk prosjekt filer", type="primary", key="geotolk_use_project_files", use_container_width=True):
            files_data = []
            progress = st.progress(0, text="Parser SND-filer…")
            snd_items = sorted(snd_contents.items())
            for i, (filename, content) in enumerate(snd_items):
                progress.progress((i + 1) / len(snd_items), text=f"Parser {filename} ({i+1}/{len(snd_items)})")
                res = api.geotolk_parse(content)
                if res.get("success"):
                    files_data.append({
                        "filename":    filename,
                        "content":     content,
                        "parsed_data": res["data"],
                        "layers":      [],
                        "status":      "pending",
                    })
                else:
                    st.warning(f"Kunne ikke parse {filename}: {res.get('error')}")
            progress.empty()

            if files_data:
                st.success(f"✅ {len(files_data)} filer hentet fra prosjektet")
                for f in files_data:
                    depth = f["parsed_data"].get("max_depth", 0)
                    st.write(f"• {f['filename']} – Max dybde: {depth:.2f} m")
                st.session_state.geotolk_files = files_data

    # ── Option 2: Fetch from local project folder (only if accessible) ──
    from_project = False
    if folder_path:
        from pathlib import Path as _P
        if _P(folder_path).is_dir():
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

    # Ødometer checkbox for this file
    oedo_key = f"oedometer_{idx}"
    if oedo_key not in st.session_state:
        st.session_state[oedo_key] = cur.get("has_oedometer", False)
    has_oedo = st.checkbox(
        "Tolket med ødometer",
        value=st.session_state[oedo_key],
        key=f"oedo_cb_{idx}",
    )
    st.session_state[oedo_key] = has_oedo
    cur["has_oedometer"] = has_oedo

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
            files[idx]["has_oedometer"] = has_oedo
            res = api.add_geotolk_interpretation(
                st.session_state.geotolk_session_id,
                cur["filename"],
                cur["parsed_data"],
                st.session_state.geotolk_layers,
                has_oedometer=has_oedo,
                snd_raw_content=cur.get("content", ""),
            )
            if res.get("success"):
                st.success("✅ Tolkning lagret!")
            else:
                st.error(f"Feil: {res.get('error')}")

    with cf:
        done = sum(1 for f in files if f.get("status") == "interpreted")
        if st.button(f"✓ Fullfør ({done}/{len(files)} tolket)", use_container_width=True):
            if done > 0:
                _complete_session(files)
            else:
                st.warning("Lagre minst én tolkning før du fullfører")


# --------------------------------------------------------- complete & export

def _build_csv_content(files: list, username: str) -> str:
    """Build CSV string with interpretation results for all interpreted files."""
    output = _io.StringIO()
    writer = csv.writer(output, delimiter=";")
    writer.writerow([
        "Filnavn", "Lag_nr", "Materiale", "Fra_dybde_m", "Til_dybde_m",
        "Tykkelse_m", "Max_dybde_m", "Har_oedometer", "Tolket_av",
    ])
    for f in files:
        if f.get("status") != "interpreted":
            continue
        layers = f.get("layers", [])
        max_depth = f.get("parsed_data", {}).get("max_depth", 0)
        has_oedo = "Ja" if f.get("has_oedometer") else "Nei"
        for i, layer in enumerate(layers, 1):
            writer.writerow([
                f["filename"],
                i,
                layer.get("type", ""),
                f"{layer.get('start', 0):.2f}",
                f"{layer.get('end', 0):.2f}",
                f"{layer.get('end', 0) - layer.get('start', 0):.2f}",
                f"{max_depth:.2f}",
                has_oedo,
                username,
            ])
    return output.getvalue()


def _complete_session(files: list):
    """
    Called when the user clicks Fullfør:
    1. Export CSV to project folder (or user-chosen folder)
    2. Send all interpretation data to Azure DB for ML training
    3. Log as activity
    4. Reset state and navigate home
    """
    project = st.session_state.selected_project
    session_id = st.session_state.geotolk_session_id

    # --- 1. CSV export ---
    csv_content = _build_csv_content(files, USERNAME)
    activity_name = st.session_state.geotolk_activity_name or "GeoTolk"
    safe_name = "".join(c if c.isalnum() or c in ("-", "_", " ") else "_" for c in activity_name)
    csv_filename = f"GeoTolk_{safe_name}.csv"

    folder_path = project.get("folder_path") if project else None

    if folder_path and os.path.isdir(folder_path):
        csv_path = os.path.join(folder_path, csv_filename)
        try:
            with open(csv_path, "w", encoding="utf-8-sig", newline="") as fh:
                fh.write(csv_content)
            st.success(f"CSV lagret: {csv_path}")
        except OSError as exc:
            st.error(f"Kunne ikke lagre CSV til prosjektmappe: {exc}")

    # Always offer download button (works on Azure and locally)
    st.download_button(
        label="⬇️ Last ned tolkning (CSV)",
        data=csv_content.encode("utf-8-sig"),
        file_name=csv_filename,
        mime="text/csv",
    )

    # --- 2. Send to Azure DB for ML training ---
    interpreted_files = []
    for f in files:
        if f.get("status") != "interpreted":
            continue
        coords = _extract_coords_from_content(f.get("content", ""))
        interpreted_files.append({
            "filename":          f["filename"],
            "parsed_data":       f["parsed_data"],
            "layers":            f.get("layers", []),
            "has_oedometer":     f.get("has_oedometer", False),
            "status":            f["status"],
            "interpretation_id": f.get("interpretation_id", 0),
            "coords":            coords,
            "snd_raw_content":   f.get("content", ""),
        })

    if session_id and interpreted_files:
        with st.spinner("Sender data til ML-database..."):
            res = api.complete_geotolk_session(session_id, interpreted_files, USERNAME)
        if res.get("success"):
            ml_count = res.get("ml_records", 0)
            st.success(f"✅ Tolkningsøkt fullført! {ml_count} oppføringer sendt til ML-database.")
        else:
            st.error(f"Feil ved fullføring: {res.get('error')}")
            return  # Stopp — ikke naviger bort ved feil

    # --- 3. Reset and navigate home ---
    st.session_state.geotolk_step   = 1
    st.session_state.geotolk_files  = []
    st.session_state.geotolk_layers = []
    st.switch_page("pages/home.py")


# ---------------------------------------------------------------- polyTolkning
# Line-cover algorithm and cross-section profile view
# ----------------------------------------------------------------

def _extract_coords_from_content(content: str) -> dict | None:
    """Extract X (easting), Y (northing), Z (elevation) from SND header lines."""
    lines = content.splitlines()
    if len(lines) < 3:
        return None
    try:
        y = float(lines[0].strip())  # northing
        x = float(lines[1].strip())  # easting
        z = float(lines[2].strip())  # elevation
        if x == 0 and y == 0:
            return None
        return {"x": x, "y": y, "z": z}
    except (ValueError, IndexError):
        return None


def _point_to_line_dist(px, py, x1, y1, x2, y2):
    """Perpendicular distance from point (px, py) to line through (x1,y1)-(x2,y2)."""
    dx, dy = x2 - x1, y2 - y1
    length = math.hypot(dx, dy)
    if length < 1e-9:
        return math.hypot(px - x1, py - y1)
    return abs(dy * px - dx * py + x2 * y1 - y2 * x1) / length


def _fit_lines(points: list[dict], tolerance: float = 2.0) -> list[list[int]]:
    """
    Greedy line cover: find minimum lines so every point is on at least one line.

    Args:
        points: list of dicts with 'x', 'y' keys (easting/northing).
        tolerance: max perpendicular distance (m) to count a point as on a line.

    Returns:
        List of lines, each a list of point indices sorted by projection along the line.
    """
    n = len(points)
    if n <= 1:
        return [[i] for i in range(n)]
    if n == 2:
        return [[0, 1]]

    uncovered = set(range(n))
    lines = []

    while uncovered:
        if len(uncovered) == 1:
            lines.append(list(uncovered))
            break

        best_line = []
        # Try all pairs from remaining uncovered points
        unc_list = list(uncovered)
        for i, j in combinations(unc_list, 2):
            x1, y1 = points[i]["x"], points[i]["y"]
            x2, y2 = points[j]["x"], points[j]["y"]
            on_line = []
            for k in range(n):
                if k not in uncovered:
                    continue
                d = _point_to_line_dist(points[k]["x"], points[k]["y"], x1, y1, x2, y2)
                if d <= tolerance:
                    on_line.append(k)
            if len(on_line) > len(best_line):
                best_line = on_line

        if not best_line:
            # Shouldn't happen, but safety: take one remaining
            best_line = [unc_list[0]]

        # Sort points along the line direction
        if len(best_line) >= 2:
            # Use direction from first to last in best_line
            ax = points[best_line[0]]["x"]
            ay = points[best_line[0]]["y"]
            bx = points[best_line[-1]]["x"]
            by = points[best_line[-1]]["y"]
            dx, dy = bx - ax, by - ay
            if abs(dx) > 1e-9 or abs(dy) > 1e-9:
                best_line.sort(key=lambda k: (points[k]["x"] - ax) * dx + (points[k]["y"] - ay) * dy)

        lines.append(best_line)
        for k in best_line:
            uncovered.discard(k)

    return lines


def _project_along_line(points: list[dict], indices: list[int]) -> list[float]:
    """Project points onto the line axis, returning cumulative distances from first point."""
    if len(indices) <= 1:
        return [0.0]
    x0, y0 = points[indices[0]]["x"], points[indices[0]]["y"]
    x1, y1 = points[indices[-1]]["x"], points[indices[-1]]["y"]
    dx, dy = x1 - x0, y1 - y0
    length = math.hypot(dx, dy)
    if length < 1e-9:
        return [0.0] * len(indices)
    ux, uy = dx / length, dy / length
    return [(points[i]["x"] - x0) * ux + (points[i]["y"] - y0) * uy for i in indices]


def _build_plan_figure(points, lines, line_colors):
    """Build a Plotly plan-view showing all points and fitted lines."""
    fig = go.Figure()

    for li, idx_list in enumerate(lines):
        color = line_colors[li % len(line_colors)]
        xs = [points[i]["x"] for i in idx_list]
        ys = [points[i]["y"] for i in idx_list]
        names = [points[i]["name"] for i in idx_list]
        fig.add_trace(go.Scatter(
            x=xs, y=ys, mode="lines",
            line=dict(color=color, width=2, dash="dash"),
            name=f"Profil {li + 1}",
            hoverinfo="skip",
        ))
        fig.add_trace(go.Scatter(
            x=xs, y=ys, mode="markers+text",
            marker=dict(size=10, color=color, line=dict(width=1, color="#333")),
            text=names, textposition="top center", textfont=dict(size=10),
            name=f"Profil {li + 1} – punkt",
            hovertemplate="%{text}<br>X: %{x:.1f}<br>Y: %{y:.1f}<extra></extra>",
        ))

    fig.update_layout(
        title="Punktoversikt med profil-linjer",
        xaxis_title="Øst (m)", yaxis_title="Nord (m)",
        yaxis_scaleanchor="x", yaxis_scaleratio=1,
        height=500, showlegend=True,
        margin=dict(l=60, r=20, t=40, b=40),
    )
    return fig


def _build_profile_figure(points, files, indices, distances, line_idx):
    """Build a cross-section profile: boreholes side by side at correct elevation."""
    # Find global elevation range for consistent y-axis
    all_z = [points[i]["z"] for i in indices]
    all_max_depth = [files[i]["parsed_data"].get("max_depth", 0) for i in indices]
    elev_top = max(all_z) + 2
    elev_bot = min(z - md for z, md in zip(all_z, all_max_depth)) - 2

    fig = go.Figure()

    # Terrain line
    fig.add_trace(go.Scatter(
        x=[distances[j] for j in range(len(indices))],
        y=[points[indices[j]]["z"] for j in range(len(indices))],
        mode="lines+markers",
        line=dict(color="#8B4513", width=2),
        marker=dict(size=4, color="#8B4513"),
        name="Terreng",
        hovertemplate="Terrengkvote: %{y:.1f} m<extra></extra>",
    ))

    bh_width_m = max(distances[-1] * 0.015, 0.5) if distances[-1] > 0 else 1.0

    for j, pi in enumerate(indices):
        f = files[pi]
        parsed = f["parsed_data"]
        z_top = points[pi]["z"]
        name = points[pi]["name"]
        dist = distances[j]
        max_depth = parsed.get("max_depth", 0)

        depths = parsed.get("depth", [])
        c2 = parsed.get("c2", [])

        # Normalize c2 to borehole width for visual
        if c2:
            c2_max = max(c2) if max(c2) > 0 else 1
        else:
            c2_max = 1

        # Draw sounding curve (c2 values scaled horizontally around the borehole position)
        if depths and c2:
            step = max(1, len(depths) // 300)
            curve_x = [dist + (c2[k] / c2_max) * bh_width_m * 2 for k in range(0, len(depths), step)]
            curve_y = [z_top - depths[k] for k in range(0, len(depths), step)]
            fig.add_trace(go.Scatter(
                x=curve_x, y=curve_y,
                mode="lines", line=dict(color="#333", width=1.2),
                name=name,
                hovertemplate=f"{name}<br>Dybde: " + "%{customdata:.2f} m<br>Motstand: %{text}<extra></extra>",
                customdata=[depths[k] for k in range(0, len(depths), step)],
                text=[f"{c2[k]:.0f}" for k in range(0, len(depths), step)],
                showlegend=True,
            ))

        # Borehole shaft line
        fig.add_trace(go.Scatter(
            x=[dist, dist], y=[z_top, z_top - max_depth],
            mode="lines",
            line=dict(color="#1E88E5", width=3),
            showlegend=False,
            hoverinfo="skip",
        ))

        # Borehole label at top
        fig.add_annotation(
            x=dist, y=z_top + 1.5,
            text=f"<b>{name}</b><br>{z_top:.1f} m",
            showarrow=False, font=dict(size=11),
        )

        # Distance annotation at bottom
        if j > 0:
            prev_dist = distances[j - 1]
            seg_dist = dist - prev_dist
            mid_x = (dist + prev_dist) / 2
            fig.add_annotation(
                x=mid_x, y=elev_bot + 0.5,
                text=f"← {seg_dist:.1f} m →",
                showarrow=False, font=dict(size=10, color="#666"),
            )

    # Overall distance
    if len(indices) > 1:
        fig.add_annotation(
            x=distances[-1] / 2, y=elev_bot - 1,
            text=f"Total lengde: {distances[-1]:.1f} m",
            showarrow=False, font=dict(size=12, color="#333"),
        )

    fig.update_layout(
        title=f"Profil {line_idx + 1} – Tverrsnitt",
        xaxis_title="Avstand langs profil (m)",
        yaxis_title="Kvote (m)",
        height=600,
        showlegend=True,
        margin=dict(l=60, r=20, t=40, b=60),
    )
    fig.update_yaxes(range=[elev_bot - 3, elev_top + 3])

    return fig


def show_poly_tolkning():
    """polyTolkning: Group boreholes into lines, show cross-section profiles."""
    files = st.session_state.geotolk_files
    if not files:
        st.warning("Ingen filer lastet. Gå tilbake til Steg 2.")
        return

    # Extract coordinates from raw SND content
    points = []
    valid_indices = []
    for i, f in enumerate(files):
        coords = _extract_coords_from_content(f["content"])
        if coords:
            points.append({
                "x": coords["x"], "y": coords["y"], "z": coords["z"],
                "name": Path(f["filename"]).stem,
                "file_idx": i,
            })
            valid_indices.append(i)

    if len(points) < 2:
        st.warning("Trenger minst 2 borehull med gyldige koordinater for polyTolkning.")
        if points:
            st.info(f"Fant kun {len(points)} punkt med koordinater.")
        no_coords = [f["filename"] for i, f in enumerate(files) if i not in valid_indices]
        if no_coords:
            st.caption(f"Uten koordinater: {', '.join(no_coords)}")
        return

    # Tolerance slider
    tolerance = st.slider(
        "Toleranse for linje-tilhørighet (m)",
        min_value=0.5, max_value=20.0, value=3.0, step=0.5,
        help="Maks avstand fra linje for at et punkt regnes som del av profilen.",
        key="poly_tolerance",
    )

    # Fit lines
    lines = _fit_lines(points, tolerance=tolerance)

    LINE_COLORS = [
        "#1E88E5", "#E53935", "#43A047", "#FB8C00",
        "#8E24AA", "#00ACC1", "#D81B60", "#6D4C41",
    ]

    # Plan view
    fig_plan = _build_plan_figure(points, lines, LINE_COLORS)
    st.plotly_chart(fig_plan, use_container_width=True)

    # Line summary
    st.markdown(f"### Profil-oversikt ({len(lines)} profiler, {len(points)} punkter)")
    import pandas as pd
    summary_rows = []
    for li, idx_list in enumerate(lines):
        dists = _project_along_line(points, idx_list)
        total = dists[-1] - dists[0] if len(dists) > 1 else 0
        names = [points[i]["name"] for i in idx_list]
        summary_rows.append({
            "Profil": f"Profil {li + 1}",
            "Antall punkter": len(idx_list),
            "Total lengde (m)": f"{total:.1f}",
            "Punkter": ", ".join(names),
        })
    st.dataframe(pd.DataFrame(summary_rows), use_container_width=True, hide_index=True)

    # Profile selection
    st.markdown("---")
    st.markdown("### Velg profil for tverrsnitt-tolkning")

    for li, idx_list in enumerate(lines):
        color = LINE_COLORS[li % len(LINE_COLORS)]
        names = [points[i]["name"] for i in idx_list]
        dists = _project_along_line(points, idx_list)
        total = dists[-1] - dists[0] if len(dists) > 1 else 0

        btn_label = f"📐 Profil {li + 1}: {', '.join(names)}  ({total:.0f} m)"
        if st.button(btn_label, key=f"poly_line_{li}", use_container_width=True):
            st.session_state.poly_selected_line = li

    selected_li = st.session_state.get("poly_selected_line")
    if selected_li is not None and selected_li < len(lines):
        idx_list = lines[selected_li]
        distances = _project_along_line(points, idx_list)

        fig_profile = _build_profile_figure(points, files, idx_list, distances, selected_li)
        st.plotly_chart(fig_profile, use_container_width=True)

        # Compute shared elevation range for all boreholes on this profile
        all_z = [points[pi]["z"] for pi in idx_list]
        all_md = [files[points[pi]["file_idx"]]["parsed_data"].get("max_depth", 0) for pi in idx_list]
        shared_elev_top = max(all_z) + 2
        shared_elev_bot = min(z - md for z, md in zip(all_z, all_md)) - 2
        shared_elev_range = [shared_elev_bot, shared_elev_top]

        # Show individual interpretation editors for each borehole on this line
        st.markdown("---")
        st.markdown(f"### Tolkning – Profil {selected_li + 1}")
        st.caption(
            f"Felles høydeintervall: {shared_elev_bot:.1f} – {shared_elev_top:.1f} m. "
            "Borehull med høyere kvote vises høyere opp."
        )

        from components.geotolk_editor import geotolk_editor

        ncols = min(len(idx_list), 4)
        cols = st.columns(ncols)
        for j, pi in enumerate(idx_list):
            fi = points[pi]["file_idx"]
            f = files[fi]
            parsed = f["parsed_data"]
            max_depth = float(parsed.get("max_depth", 10))
            name = points[pi]["name"]
            z_val = points[pi]["z"]
            dist_str = f"{distances[j]:.1f} m" if j > 0 else "0 m"

            with cols[j % ncols]:
                st.markdown(f"**{name}** — {dist_str}")
                st.caption(f"Kvote: {z_val:.1f} m | Dybde: {max_depth:.1f} m")

                # Ødometer checkbox per borehole
                oedo_poly_key = f"oedometer_poly_{fi}"
                if oedo_poly_key not in st.session_state:
                    st.session_state[oedo_poly_key] = f.get("has_oedometer", False)
                has_oedo = st.checkbox(
                    "Ødometer", value=st.session_state[oedo_poly_key],
                    key=f"oedo_pcb_{fi}",
                )
                st.session_state[oedo_poly_key] = has_oedo
                f["has_oedometer"] = has_oedo

                # Per-file layers in session state
                layer_key = f"poly_layers_{fi}"
                if layer_key not in st.session_state:
                    md = max_depth
                    st.session_state[layer_key] = [
                        {"type": "leire", "start": 0.0,        "end": md / 3},
                        {"type": "sand",  "start": md / 3,     "end": 2 * md / 3},
                        {"type": "fjell", "start": 2 * md / 3, "end": md},
                    ]

                updated = geotolk_editor(
                    sounding_data=parsed,
                    layers=st.session_state[layer_key],
                    max_depth=max_depth,
                    materials=GEOTOLK_MATERIALS,
                    colors=GEOTOLK_COLORS,
                    elevation=z_val,
                    elev_range=shared_elev_range,
                    show_y_axis=(j % ncols == 0),
                    key=f"poly_ed_{fi}",
                )
                if updated:
                    st.session_state[layer_key] = updated
                    files[fi]["layers"] = updated

        # Save all interpretations
        st.markdown("---")
        if st.button("💾 Lagre alle tolkninger på profilen", type="primary", use_container_width=True,
                     key="poly_save_all"):
            saved = 0
            for pi in idx_list:
                fi = points[pi]["file_idx"]
                f = files[fi]
                layer_key = f"poly_layers_{fi}"
                file_layers = st.session_state.get(layer_key, [])
                oedo_poly_key = f"oedometer_poly_{fi}"
                has_oedo = st.session_state.get(oedo_poly_key, False)
                if file_layers:
                    f["layers"] = file_layers
                    f["status"] = "interpreted"
                    f["has_oedometer"] = has_oedo
                    res = api.add_geotolk_interpretation(
                        st.session_state.geotolk_session_id,
                        f["filename"],
                        f["parsed_data"],
                        file_layers,
                        has_oedometer=has_oedo,
                        snd_raw_content=f.get("content", ""),
                    )
                    if res.get("success"):
                        saved += 1
                    else:
                        st.warning(f"Feil ved lagring av {f['filename']}: {res.get('error')}")
            st.success(f"✅ {saved}/{len(idx_list)} tolkninger lagret!")

        # Fullfør button (same as single interpretation)
        done = sum(1 for f in files if f.get("status") == "interpreted")
        if st.button(f"✓ Fullfør ({done}/{len(files)} tolket)", use_container_width=True,
                     key="poly_complete"):
            if done > 0:
                _complete_session(files)
            else:
                st.warning("Lagre minst én tolkning før du fullfører")


# ----------------------------------------------------------------------- page

def _load_resumed_session():
    """Load a session from the backend when resuming from home."""
    resume_id = st.session_state.pop("geotolk_resume_session_id", None)
    if not resume_id:
        return
    # Already loaded?
    if st.session_state.geotolk_session_id == resume_id and st.session_state.geotolk_files:
        return

    with st.spinner("Laster tolkningsøkt…"):
        res = api.get_geotolk_session_resume(resume_id)
    if not res.get("success"):
        st.error(f"Kunne ikke laste økt: {res.get('error')}")
        return

    session = res["session"]
    files_data = []
    for fd in session.get("files", []):
        files_data.append({
            "interpretation_id": fd["interpretation_id"],
            "filename":          fd["filename"],
            "content":           fd.get("content", ""),
            "parsed_data":       fd["parsed_data"],
            "layers":            fd.get("layers", []),
            "has_oedometer":     fd.get("has_oedometer", False),
            "status":            fd.get("status", "pending"),
        })

    st.session_state.geotolk_session_id    = resume_id
    st.session_state.geotolk_activity_name = session.get("activity_name", "")
    st.session_state.geotolk_files         = files_data
    st.session_state.geotolk_current_file  = 0
    st.session_state.geotolk_step          = 3
    if files_data:
        first = files_data[0]
        if first.get("layers"):
            st.session_state.geotolk_layers = first["layers"]
        else:
            _init_layers(first)


def main():
    st.markdown("# 🗺️ GeoTolk")

    # Check for resume from home page
    _load_resumed_session()

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
    elif current == 3:
        tab_single, tab_poly = st.tabs(["📊 Enkelttolkning", "📐 polyTolkning"])
        with tab_single:
            show_step3()
        with tab_poly:
            show_poly_tolkning()


main()
