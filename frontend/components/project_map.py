# -*- coding: utf-8 -*-
"""
Project Map Helpers
===================
Functions for loading SND boreholes from project folders, querying NADAG,
building 2D folium maps and 3D plotly figures.

Extracted from sandbox/GeoArc/GeoArc.py for use in the main RamGAP app.
"""
from __future__ import annotations

import json
import math
import sys
import urllib.request
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

import folium
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from folium.plugins import Fullscreen, MarkerCluster, MiniMap, MousePosition
from pyproj import Transformer

# Ensure snd_parser is importable from sandbox/GeoArc/
_SANDBOX_DIR = Path(__file__).resolve().parent.parent.parent / "sandbox" / "GeoArc"
if str(_SANDBOX_DIR) not in sys.path:
    sys.path.insert(0, str(_SANDBOX_DIR))
from snd_parser import parse_snd_full  # noqa: E402

# ---------------------------------------------------------------------------
# CRS options (Norwegian projected coordinate systems)
# ---------------------------------------------------------------------------
CRS_OPTIONS = {
    "EUREF89 NTM5 (EPSG:5105)": 5105,
    "EUREF89 NTM6 (EPSG:5106)": 5106,
    "EUREF89 NTM7 (EPSG:5107)": 5107,
    "EUREF89 NTM8 (EPSG:5108)": 5108,
    "EUREF89 NTM9 (EPSG:5109)": 5109,
    "EUREF89 NTM10 (EPSG:5110)": 5110,
    "EUREF89 NTM11 (EPSG:5111)": 5111,
    "EUREF89 NTM12 (EPSG:5112)": 5112,
    "EUREF89 NTM13 (EPSG:5113)": 5113,
    "EUREF89 NTM14 (EPSG:5114)": 5114,
    "EUREF89 NTM15 (EPSG:5115)": 5115,
    "EUREF89 NTM16 (EPSG:5116)": 5116,
    "EUREF89 NTM17 (EPSG:5117)": 5117,
    "EUREF89 NTM18 (EPSG:5118)": 5118,
    "EUREF89 NTM19 (EPSG:5119)": 5119,
    "EUREF89 NTM20 (EPSG:5120)": 5120,
    "EUREF89 NTM21 (EPSG:5121)": 5121,
    "EUREF89 NTM22 (EPSG:5122)": 5122,
    "EUREF89 NTM23 (EPSG:5123)": 5123,
    "EUREF89 UTM32 (EPSG:25832)": 25832,
    "EUREF89 UTM33 (EPSG:25833)": 25833,
}

# Method style for map markers
METHOD_MARKER_COLORS = {
    "Totalsondering": "#E63946",
    "Fjellkontrollboring": "#795548",
    "Dreietrykksondering": "#2E7D32",
    "Dreiesondering": "#1565C0",
    "Enkel sondering": "#6A1B9A",
    "CPT": "#E65100",
}

# Module-level cache for graph data (not serialized by Streamlit)
_GRAPH_DATA_CACHE: dict[tuple[str, str], dict] = {}


def _store_graph_data(project_name: str, point_id: str, data: dict) -> None:
    _GRAPH_DATA_CACHE[(project_name, point_id)] = data


def get_graph_data(project_name: str, point_id: str) -> dict | None:
    return _GRAPH_DATA_CACHE.get((project_name, point_id))


# ---------------------------------------------------------------------------
# Coordinate helpers
# ---------------------------------------------------------------------------

def _convert_coords(x: float, y: float, source_epsg: int) -> tuple[float, float]:
    """Convert projected coordinates to WGS84 (lat, lon)."""
    transformer = Transformer.from_crs(f"EPSG:{source_epsg}", "EPSG:4326", always_xy=True)
    lon, lat = transformer.transform(x, y)
    return lat, lon


def _convex_hull(points: list[tuple[float, float]]) -> list[tuple[float, float]]:
    pts = sorted(set(points))
    if len(pts) <= 2:
        return pts

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lower = []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    upper = []
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return lower[:-1] + upper[:-1]


def _hull_with_buffer(points: list[tuple[float, float]], buffer_deg: float = 0.0002) -> list[tuple[float, float]]:
    hull = _convex_hull(points)
    if len(hull) < 3:
        return hull
    cx = sum(p[0] for p in hull) / len(hull)
    cy = sum(p[1] for p in hull) / len(hull)
    buffered = []
    for px, py in hull:
        dx, dy = px - cx, py - cy
        dist = math.sqrt(dx * dx + dy * dy) or 1e-9
        buffered.append((px + dx / dist * buffer_deg, py + dy / dist * buffer_deg))
    return buffered


def _detect_epsg_from_project(folder: Path) -> int | None:
    """Try to detect EPSG from GeoSuite Info.prj file."""
    for search_dir in [folder, folder.parent, folder.parent.parent]:
        prj = search_dir / "Info.prj"
        if prj.is_file():
            try:
                lines = prj.read_text(encoding="utf-8", errors="ignore").splitlines()
                for ln in lines:
                    parts = ln.strip().split()
                    if len(parts) >= 5:
                        try:
                            code = int(parts[4])
                            if code == 29 and len(parts) >= 6:
                                zone_offset = int(parts[5])
                                ntm_zone = 5 + zone_offset
                                if 5 <= ntm_zone <= 30:
                                    return 5100 + ntm_zone
                            elif code == 22:
                                return 25832
                            elif code == 23:
                                return 25833
                        except ValueError:
                            continue
            except Exception:
                pass
    return None


# ---------------------------------------------------------------------------
# SND project loading
# ---------------------------------------------------------------------------

def load_snd_project(folder_path: str, source_epsg: int = 0) -> dict | None:
    """
    Load boreholes from a folder containing SND files.
    Looks for AUTOGRAF subfolder or .SND files directly.
    Auto-detects EPSG from Info.prj if source_epsg is 0.
    """
    folder = Path(folder_path)
    if not folder.is_dir():
        return None

    autograf_dir = None
    folder_upper = folder.name.upper()

    if folder_upper.startswith("AUTOGRAF") and list(folder.glob("*.SND")):
        autograf_dir = folder
        project_name = folder.parent.name
    else:
        for child in folder.iterdir():
            if child.is_dir() and child.name.upper().startswith("AUTOGRAF"):
                autograf_dir = child
                break
        project_name = folder.name

    if autograf_dir is None:
        direct_snd = list(folder.glob("*.SND")) + list(folder.glob("*.snd"))
        if direct_snd:
            autograf_dir = folder
            project_name = folder.name

    if autograf_dir is None:
        return None

    detected_epsg = _detect_epsg_from_project(folder)
    if detected_epsg:
        source_epsg = detected_epsg
    if source_epsg == 0:
        source_epsg = 25833  # default to UTM33

    snd_files_set = {p.resolve() for p in autograf_dir.glob("*.SND")}
    snd_files_set |= {p.resolve() for p in autograf_dir.glob("*.snd")}
    snd_files = sorted(snd_files_set, key=lambda p: p.name)
    if not snd_files:
        return None

    boreholes = []
    errors = []
    for snd_path in snd_files:
        try:
            text = snd_path.read_text(encoding="utf-8", errors="ignore")
            data = parse_snd_full(text)
            lat, lon = _convert_coords(data["x"], data["y"], source_epsg)
            if not (math.isfinite(lat) and math.isfinite(lon)
                    and -90 <= lat <= 90 and -180 <= lon <= 180):
                errors.append(f"{snd_path.name}: Ugyldige koordinater")
                continue
            bh = {
                "point_id": snd_path.stem,
                "file_path": str(snd_path),
                "lat": lat,
                "lon": lon,
                "elevation": data["z"],
                "method_code": data.get("method_code"),
                "method_name": data.get("method_name", "Ukjent"),
                "date": data.get("date"),
                "max_depth": data.get("max_depth", 0),
            }
            boreholes.append(bh)
            _store_graph_data(project_name, snd_path.stem, {
                "depth": data["depth"],
                "c2": data["c2"],
                "c3": data.get("c3", []),
                "c4": data.get("c4", []),
                "spyling": data.get("spyling", []),
                "slag": data.get("slag", []),
            })
        except Exception as e:
            errors.append(f"{snd_path.name}: {e}")

    if not boreholes:
        return None

    coords = [(bh["lat"], bh["lon"]) for bh in boreholes]
    if len(coords) >= 3:
        hull = _hull_with_buffer(coords)
        polygon = hull + [hull[0]]
    else:
        polygon = coords

    return {
        "project_name": project_name,
        "folder_path": str(folder),
        "epsg": source_epsg,
        "detected_epsg": detected_epsg,
        "boreholes": boreholes,
        "polygon": polygon,
        "errors": errors,
    }


# ---------------------------------------------------------------------------
# NADAG WFS queries (NGU borehole database)
# ---------------------------------------------------------------------------

@st.cache_data(ttl=300)
def query_nadag_bbox(min_lat: float, min_lon: float, max_lat: float, max_lon: float) -> pd.DataFrame:
    """Query NADAG WFS for boreholes inside a bounding box."""
    params = {
        "SERVICE": "WFS",
        "VERSION": "2.0.0",
        "REQUEST": "GetFeature",
        "TYPENAMES": "nadag:GB_standard",
        "outputFormat": "application/json",
        "count": "200",
        "bbox": f"{min_lon},{min_lat},{max_lon},{max_lat},EPSG:4326",
        "srsName": "EPSG:4326",
    }
    url = "https://geo.ngu.no/geoserver/nadag/ows?" + urlencode(params)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "RamGAP/1.0"})
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read())
        features = data.get("features", [])
        if not features:
            return pd.DataFrame()
        rows = []
        for f in features:
            props = f.get("properties", {}).copy()
            coords = (f.get("geometry") or {}).get("coordinates")
            if coords:
                props["_lat"] = round(coords[1], 6)
                props["_lon"] = round(coords[0], 6)
            rows.append(props)
        return pd.DataFrame(rows)
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=300)
def query_nadag_investigations(lokalid: str) -> pd.DataFrame:
    """Query NADAG WFS GBU_metode for a specific borehole by its lokalid."""
    params = {
        "SERVICE": "WFS",
        "VERSION": "2.0.0",
        "REQUEST": "GetFeature",
        "TYPENAMES": "nadag:GBU_metode",
        "outputFormat": "application/json",
        "count": "20",
        "srsName": "EPSG:4326",
        "CQL_FILTER": f"geotekniskborehullfkid='{lokalid}'",
    }
    url = "https://geo.ngu.no/geoserver/nadag/ows?" + urlencode(params)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "RamGAP/1.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
        features = data.get("features", [])
        if not features:
            return pd.DataFrame()
        rows = [f.get("properties", {}).copy() for f in features]
        return pd.DataFrame(rows)
    except Exception:
        return pd.DataFrame()


def query_nadag_for_project(boreholes: list[dict], buffer_deg: float = 0.005) -> pd.DataFrame:
    """Query NADAG for the bounding box of a project's boreholes + buffer."""
    if not boreholes:
        return pd.DataFrame()
    lats = [bh["lat"] for bh in boreholes]
    lons = [bh["lon"] for bh in boreholes]
    return query_nadag_bbox(
        min(lats) - buffer_deg, min(lons) - buffer_deg,
        max(lats) + buffer_deg, max(lons) + buffer_deg,
    )


# ---------------------------------------------------------------------------
# 2D Folium map
# ---------------------------------------------------------------------------

def build_project_map(
    boreholes: list[dict],
    nadag_df: pd.DataFrame | None = None,
    polygon: list[tuple[float, float]] | None = None,
    project_name: str = "",
) -> folium.Map:
    """Build a 2D folium map centred on the project boreholes."""
    if not boreholes:
        return folium.Map(location=[59.9, 10.75], zoom_start=10)

    lats = [bh["lat"] for bh in boreholes]
    lons = [bh["lon"] for bh in boreholes]
    center = [sum(lats) / len(lats), sum(lons) / len(lons)]

    m = folium.Map(location=center, zoom_start=14, control_scale=True, tiles=None)

    # Base maps
    folium.TileLayer("OpenStreetMap", name="OpenStreetMap", control=True).add_to(m)
    folium.TileLayer("CartoDB Positron", name="CartoDB Positron", control=True, show=False).add_to(m)
    folium.TileLayer(
        tiles="https://opencache.statkart.no/gatekeeper/gk/gk.open_nib_web_mercator_wmts_v2"
              "?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=Nibcache_web_mercator_v2"
              "&STYLE=default&FORMAT=image/jpgpng&TILEMATRIXSET=default028mm"
              "&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}",
        attr="Kartverket",
        name="Norge i bilder",
        overlay=False,
        control=True,
        show=False,
    ).add_to(m)
    folium.TileLayer(
        tiles="https://cache.kartverket.no/v1/wmts/1.0.0/topo/default/webmercator/{z}/{y}/{x}.png",
        attr="Kartverket",
        name="Norgeskart",
        overlay=False,
        control=True,
        show=False,
    ).add_to(m)

    # Project polygon
    if polygon and len(polygon) >= 3:
        folium.Polygon(
            locations=polygon,
            color="#E63946",
            weight=2,
            fill=True,
            fill_color="#E63946",
            fill_opacity=0.10,
            tooltip=f"Prosjekt: {project_name}",
        ).add_to(m)

    # Project boreholes
    fg_proj = folium.FeatureGroup(name=f"Borehull – {project_name}", show=True)
    for bh in boreholes:
        color = METHOD_MARKER_COLORS.get(bh.get("method_name", ""), "#E63946")
        popup_html = (
            f'<div style="font-size:13px;min-width:200px;">'
            f'<b style="font-size:14px;">{bh["point_id"]}</b><br>'
            f'<b>Metode:</b> {bh.get("method_name", "Ukjent")}<br>'
            f'<b>Dybde:</b> {bh["max_depth"]:.1f} m<br>'
            f'<b>Terrengkvote:</b> {bh["elevation"]:.1f} m<br>'
            f'<b>Dato:</b> {bh.get("date", "–")}'
            f'</div>'
        )
        folium.CircleMarker(
            location=[bh["lat"], bh["lon"]],
            radius=8,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.85,
            popup=folium.Popup(popup_html, max_width=280),
            tooltip=f"{bh['point_id']} – {bh.get('method_name', '')}",
        ).add_to(fg_proj)
    fg_proj.add_to(m)

    # NADAG boreholes
    if nadag_df is not None and not nadag_df.empty:
        fg_nadag = folium.FeatureGroup(name="NADAG (NGU)", show=True)
        for _, row in nadag_df.iterrows():
            lat = row.get("_lat")
            lon = row.get("_lon")
            if lat is None or lon is None:
                continue
            borenr = str(row.get("borenr", "NADAG"))
            depth = row.get("boretlengde", "?")
            popup_html = (
                f'<div style="font-size:13px;min-width:180px;">'
                f'<b>{borenr}</b> (NADAG)<br>'
                f'<b>Dybde:</b> {depth} m<br>'
                f'<b>Metode:</b> {row.get("geotekniskmetodetekst", "–")}'
                f'</div>'
            )
            folium.CircleMarker(
                location=[float(lat), float(lon)],
                radius=6,
                color="#5B8FF9",
                fill=True,
                fill_color="#5B8FF9",
                fill_opacity=0.7,
                popup=folium.Popup(popup_html, max_width=260),
                tooltip=f"NADAG: {borenr}",
            ).add_to(fg_nadag)
        fg_nadag.add_to(m)

    # Fit to bounds
    all_coords = [[bh["lat"], bh["lon"]] for bh in boreholes]
    if nadag_df is not None and not nadag_df.empty:
        for _, row in nadag_df.iterrows():
            if row.get("_lat") is not None and row.get("_lon") is not None:
                all_coords.append([float(row["_lat"]), float(row["_lon"])])
    if all_coords:
        m.fit_bounds(all_coords, padding=[30, 30])

    folium.LayerControl(collapsed=False).add_to(m)
    MiniMap(toggle_display=True).add_to(m)
    Fullscreen(position="topright").add_to(m)
    MousePosition(position="bottomright", prefix="Koordinat").add_to(m)
    return m


# ---------------------------------------------------------------------------
# Sounding figure (2D plotly)
# ---------------------------------------------------------------------------

def build_sounding_figure(bh: dict, project_name: str = "") -> go.Figure:
    """Build a plotly sounding log figure for a borehole."""
    graph = get_graph_data(project_name, bh.get("point_id", ""))
    if not graph:
        # Try re-parsing from file
        fp = bh.get("file_path")
        if fp and Path(fp).is_file():
            try:
                text = Path(fp).read_text(encoding="utf-8", errors="ignore")
                data = parse_snd_full(text)
                graph = {
                    "depth": data["depth"], "c2": data["c2"],
                    "c3": data.get("c3", []), "c4": data.get("c4", []),
                    "spyling": data.get("spyling", []), "slag": data.get("slag", []),
                }
                _store_graph_data(project_name, bh["point_id"], graph)
            except Exception:
                pass
    if not graph:
        return go.Figure().update_layout(title="Ingen grafdata tilgjengelig")

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=graph["c2"], y=graph["depth"],
        mode="lines", name="Motstand (kN)",
        line=dict(color="black", width=1.2),
    ))

    for i, (d0, d1) in enumerate(graph.get("spyling", [])):
        fig.add_hrect(
            y0=d0, y1=d1,
            fillcolor="rgba(30,120,255,0.18)", line_width=0,
            annotation_text="Spyling" if i == 0 else None,
            annotation_position="top left",
        )

    for i, (d0, d1) in enumerate(graph.get("slag", [])):
        fig.add_hrect(
            y0=d0, y1=d1,
            fillcolor="rgba(220,40,40,0.18)", line_width=0,
            annotation_text="Slag" if i == 0 else None,
            annotation_position="top left",
        )

    fig.update_layout(
        title=f"{bh['point_id']} – {bh.get('method_name', '')}",
        yaxis=dict(autorange="reversed", title="Dybde (m)"),
        xaxis=dict(title="Motstand (kN)", side="top"),
        height=550,
        margin=dict(l=40, r=20, t=60, b=20),
        showlegend=False,
    )
    return fig


# ---------------------------------------------------------------------------
# 3D plotly figure
# ---------------------------------------------------------------------------

def _fetch_kartverket_elevation(lat: float, lon: float) -> float | None:
    url = (f"https://ws.geonorge.no/hoydedata/v1/punkt"
           f"?nord={lat}&ost={lon}&koordsys=4258")
    req = urllib.request.Request(url, headers={"User-Agent": "RamGAP/1.0"})
    try:
        resp = urllib.request.urlopen(req, timeout=10)
        data = json.loads(resp.read())
        pts = data.get("punkter", [])
        if pts and pts[0].get("z") is not None:
            return float(pts[0]["z"])
    except Exception:
        pass
    return None


def _build_terrain_grid(
    boreholes: list[dict], resolution: int = 10,
) -> list[dict]:
    """Build a grid of elevation points for the borehole area."""
    lats = [bh["lat"] for bh in boreholes]
    lons = [bh["lon"] for bh in boreholes]
    buf = 0.001
    min_lat, max_lat = min(lats) - buf, max(lats) + buf
    min_lon, max_lon = min(lons) - buf, max(lons) + buf

    grid_points = []
    for i in range(resolution + 1):
        for j in range(resolution + 1):
            lat = min_lat + (max_lat - min_lat) * i / resolution
            lon = min_lon + (max_lon - min_lon) * j / resolution
            grid_points.append((lat, lon))

    terrain = []
    for lat, lon in grid_points:
        z = _fetch_kartverket_elevation(lat, lon)
        terrain.append({"lat": lat, "lon": lon, "z": z if z is not None else 0.0})
    return terrain


def build_3d_figure(
    boreholes: list[dict],
    nadag_df: pd.DataFrame | None = None,
    project_name: str = "",
    terrain_grid: list[dict] | None = None,
) -> go.Figure:
    """Build a 3D plotly figure with borehole shafts and SND resistance curves."""
    import numpy as np
    from scipy.spatial import Delaunay

    fig = go.Figure()

    t2utm = Transformer.from_crs("EPSG:4326", "EPSG:25833", always_xy=True)
    all_lats = [bh["lat"] for bh in boreholes]
    all_lons = [bh["lon"] for bh in boreholes]
    cx, cy = t2utm.transform(
        sum(all_lons) / len(all_lons),
        sum(all_lats) / len(all_lats),
    )

    def to_local(lat: float, lon: float) -> tuple[float, float]:
        ex, ny = t2utm.transform(lon, lat)
        return ex - cx, ny - cy

    extent_m = max(
        max(all_lons) - min(all_lons),
        max(all_lats) - min(all_lats),
    ) * 111_000
    res_scale_m = max(extent_m * 0.15, 15.0)
    az_rad = math.radians(135.0)
    dx_dir = math.sin(az_rad)
    dy_dir = math.cos(az_rad)

    COLORS = [
        "#1565C0", "#C62828", "#2E7D32", "#6A1B9A",
        "#E65100", "#00838F", "#B45309", "#7C3AED",
    ]

    # Terrain mesh
    if terrain_grid:
        tx, ty, tz_list = [], [], []
        for pt in terrain_grid:
            lx, ly = to_local(pt["lat"], pt["lon"])
            tx.append(lx); ty.append(ly); tz_list.append(pt["z"])
        pts2d = np.array(list(zip(tx, ty)))
        tri = Delaunay(pts2d)
        fig.add_trace(go.Mesh3d(
            x=tx, y=ty, z=tz_list,
            i=tri.simplices[:, 0].tolist(),
            j=tri.simplices[:, 1].tolist(),
            k=tri.simplices[:, 2].tolist(),
            intensity=tz_list,
            colorscale=[[0, "rgb(90,120,60)"], [0.5, "rgb(140,170,90)"], [1, "rgb(200,190,140)"]],
            showscale=False, opacity=0.72, name="Terreng",
            hovertemplate="Kote: %{z:.1f} m<extra>Terreng</extra>",
        ))

    # Global max resistance for scaling
    global_max_c2 = 1.0
    for bh in boreholes:
        g = get_graph_data(project_name, bh.get("point_id", ""))
        if g and g.get("c2"):
            mc2 = max(g["c2"])
            if mc2 > global_max_c2:
                global_max_c2 = mc2

    # Project boreholes
    for idx, bh in enumerate(boreholes):
        bx, by = to_local(bh["lat"], bh["lon"])
        t_z = float(bh.get("elevation", 0.0))
        max_d = float(bh.get("max_depth", 10.0))
        bot_z = t_z - max_d
        pid = bh.get("point_id", f"BH-{idx}")
        color = COLORS[idx % len(COLORS)]
        hx = color.lstrip("#")
        rc, gc_col, bc = int(hx[0:2], 16), int(hx[2:4], 16), int(hx[4:6], 16)

        # Shaft
        fig.add_trace(go.Scatter3d(
            x=[bx, bx], y=[by, by], z=[t_z, bot_z],
            mode="lines", line=dict(color=f"rgb({rc},{gc_col},{bc})", width=4),
            showlegend=False,
            hovertemplate=f"<b>{pid}</b><br>Kote: {t_z:.1f} m<br>Dybde: {max_d:.1f} m<extra></extra>",
        ))
        # Top marker
        fig.add_trace(go.Scatter3d(
            x=[bx], y=[by], z=[t_z],
            mode="markers+text",
            marker=dict(size=7, color=color, symbol="diamond"),
            text=[pid], textposition="top center",
            textfont=dict(size=10, color=color),
            name=pid, showlegend=True,
            hovertemplate=(
                f"<b>{pid}</b><br>{bh.get('method_name','')}<br>"
                f"Dybde: {max_d:.1f} m<br>Kote: {t_z:.1f} m<extra></extra>"
            ),
        ))

        graph = get_graph_data(project_name, pid)
        if not graph or not graph.get("depth") or not graph.get("c2"):
            continue

        depths = list(graph["depth"])
        c2vals = list(graph["c2"])
        n = len(depths)
        elev_list = [t_z - d for d in depths]

        x_curve = [bx + (c / global_max_c2) * res_scale_m * dx_dir for c in c2vals]
        y_curve = [by + (c / global_max_c2) * res_scale_m * dy_dir for c in c2vals]

        fig.add_trace(go.Scatter3d(
            x=x_curve, y=y_curve, z=elev_list,
            mode="lines", line=dict(color=color, width=2.5),
            showlegend=False,
            customdata=[[f"{c:.0f} kN @ {d:.1f} m"] for c, d in zip(c2vals, depths)],
            hovertemplate="%{customdata[0]}<extra>" + pid + "</extra>",
        ))

        # Curtain mesh
        mx = [bx] * n + x_curve
        my = [by] * n + y_curve
        mz = elev_list + elev_list
        i_idx, j_idx, k_idx = [], [], []
        for s in range(n - 1):
            i_idx.append(s); j_idx.append(s + 1); k_idx.append(n + s)
            i_idx.append(s + 1); j_idx.append(n + s + 1); k_idx.append(n + s)
        fig.add_trace(go.Mesh3d(
            x=mx, y=my, z=mz, i=i_idx, j=j_idx, k=k_idx,
            color=f"rgb({rc},{gc_col},{bc})", opacity=0.18,
            showscale=False, showlegend=False, hoverinfo="skip",
        ))

        # Spyling segments
        for seg_s, seg_e in graph.get("spyling", []):
            fig.add_trace(go.Scatter3d(
                x=[bx, bx], y=[by, by], z=[t_z - seg_s, t_z - seg_e],
                mode="lines", line=dict(color="#2196F3", width=10),
                showlegend=False,
                hovertemplate=f"Spyling {seg_s:.1f}–{seg_e:.1f} m<extra></extra>",
            ))

        # Slag segments
        for seg_s, seg_e in graph.get("slag", []):
            fig.add_trace(go.Scatter3d(
                x=[bx, bx], y=[by, by], z=[t_z - seg_s, t_z - seg_e],
                mode="lines", line=dict(color="#F44336", width=10),
                showlegend=False,
                hovertemplate=f"Slag {seg_s:.1f}–{seg_e:.1f} m<extra></extra>",
            ))

    # NADAG boreholes
    if nadag_df is not None and not nadag_df.empty:
        for _, row in nadag_df.iterrows():
            lat = row.get("_lat"); lon = row.get("_lon")
            if lat is None or lon is None:
                continue
            depth = float(row.get("boretlengde", 5.0) or 5.0)
            elev = float(row.get("hoeyde", 0.0) or 0.0)
            nx, ny = to_local(float(lat), float(lon))
            bnr = str(row.get("borenr") or "NADAG")
            fig.add_trace(go.Scatter3d(
                x=[nx, nx], y=[ny, ny], z=[elev, elev - depth],
                mode="lines", line=dict(color="rgba(100,100,200,0.55)", width=2),
                showlegend=False,
                hovertemplate=f"<b>{bnr}</b><br>NADAG<br>Dybde: {depth:.1f} m<extra></extra>",
            ))

    fig.update_layout(
        scene=dict(
            xaxis_title="Øst (m)", yaxis_title="Nord (m)", zaxis_title="Kote (m.o.h.)",
            aspectmode="manual", aspectratio=dict(x=1, y=1, z=0.4),
            camera=dict(eye=dict(x=1.5, y=-1.5, z=0.9), up=dict(x=0, y=0, z=1)),
            bgcolor="rgb(235,243,252)",
        ),
        margin=dict(l=0, r=0, t=50, b=0), height=650,
        title=dict(text="3D Sonderingsvisning", font=dict(size=13)),
        paper_bgcolor="white",
        legend=dict(x=0.01, y=0.99, bgcolor="rgba(255,255,255,0.88)", bordercolor="#ccc", borderwidth=1),
    )
    return fig
