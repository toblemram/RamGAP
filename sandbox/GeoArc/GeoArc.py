from __future__ import annotations

import io
import json
import math
import os
import re
import subprocess
import sys
import tempfile
import time
import uuid
import zipfile
from pathlib import Path
import urllib.request
from urllib.parse import quote, urlencode

import requests as _requests

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import folium
import pandas as pd
import pydeck as pdk
import plotly.graph_objects as go
import streamlit as st
from folium import GeoJson, GeoJsonTooltip
from folium.plugins import BeautifyIcon, Draw, Fullscreen, MarkerCluster, MiniMap, MousePosition
from openai import AzureOpenAI
from pyproj import Transformer
from streamlit_folium import st_folium

from config import METHOD_STYLES, WMS_PRESETS

# Add sandbox to path for snd_parser
BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR / "sandbox"))
from snd_parser import parse_snd_full, parse_snd_header  # noqa: E402

DATA_DIR = BASE_DIR / "data"
FILES_DIR = BASE_DIR / "project_files"

# ---------------------------------------------------------------------------
# Common Norwegian CRS options
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
    "NGO1948 Akse 1 (EPSG:27391)": 27391,
    "NGO1948 Akse 2 (EPSG:27392)": 27392,
    "NGO1948 Akse 3 (EPSG:27393)": 27393,
    "NGO1948 Akse 4 (EPSG:27394)": 27394,
    "NGO1948 Akse 5 (EPSG:27395)": 27395,
}

# Reverse lookup: EPSG code -> CRS label
_EPSG_TO_LABEL = {v: k for k, v in CRS_OPTIONS.items()}


def _guess_ntm_zone(east: float, north: float) -> int | None:
    """Try to guess the NTM zone from the easting value.
    NTM false easting is 100000, so easting is typically 50K-150K.
    We need the longitude which we can estimate from the northing range.
    """
    # NTM zones cover Norway lon 5-30, each zone is 1 degree wide
    # Can't determine zone from coordinates alone without more context
    return None


def _detect_epsg_from_project(folder: Path) -> int | None:
    """Try to detect EPSG from GeoSuite Info.prj file or .kof files."""
    # Look for Info.prj in parent directories
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
                                # GeoSuite code 29: NTM zones. Value N -> NTM zone = 5 + N
                                ntm_zone = 5 + zone_offset
                                if 5 <= ntm_zone <= 30:
                                    return 5100 + ntm_zone  # NTM zone EPSG
                            elif code == 22:
                                return 25832
                            elif code == 23:
                                return 25833
                            elif code == 24:
                                return 25834
                            elif code == 25:
                                return 25835
                        except ValueError:
                            continue
            except Exception:
                pass
    return None


@st.cache_data
def load_points() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / "sample_points.csv")


@st.cache_data
def load_reports() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / "sample_reports.csv")


@st.cache_data
def load_projects() -> dict:
    with open(DATA_DIR / "sample_projects.geojson", "r", encoding="utf-8") as f:
        return json.load(f)


@st.cache_data
def load_project_meta() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / "sample_project_meta.csv")


@st.cache_data
def load_lab_results() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / "sample_lab_results.csv")


@st.cache_data
def load_documents() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / "sample_documents.csv")


# ---------------------------------------------------------------------------
# Project SND loading helpers
# ---------------------------------------------------------------------------

def _convert_coords(x: float, y: float, source_epsg: int) -> tuple[float, float]:
    """Convert projected coordinates to WGS84 (lat, lon)."""
    transformer = Transformer.from_crs(f"EPSG:{source_epsg}", "EPSG:4326", always_xy=True)
    lon, lat = transformer.transform(x, y)
    return lat, lon


def _convex_hull(points: list[tuple[float, float]]) -> list[tuple[float, float]]:
    """Compute convex hull of 2D points (Graham scan). Returns ordered hull vertices."""
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
    """Convex hull with a small outward buffer (in degrees)."""
    hull = _convex_hull(points)
    if len(hull) < 3:
        return hull
    # Compute centroid
    cx = sum(p[0] for p in hull) / len(hull)
    cy = sum(p[1] for p in hull) / len(hull)
    # Push each point slightly outward from centroid
    buffered = []
    for px, py in hull:
        dx, dy = px - cx, py - cy
        dist = math.sqrt(dx * dx + dy * dy) or 1e-9
        buffered.append((px + dx / dist * buffer_deg, py + dy / dist * buffer_deg))
    return buffered


# Module-level cache for heavy borehole graph data (not serialized by Streamlit)
_GRAPH_DATA_CACHE: dict[tuple[str, str], dict] = {}


def _store_graph_data(project_name: str, point_id: str, data: dict) -> None:
    _GRAPH_DATA_CACHE[(project_name, point_id)] = data


def get_graph_data(project_name: str, point_id: str) -> dict | None:
    cached = _GRAPH_DATA_CACHE.get((project_name, point_id))
    if cached:
        return cached
    # Auto-recover: re-parse SND file if available in loaded projects
    loaded = st.session_state.get("loaded_projects", {})
    proj = loaded.get(project_name)
    if not proj:
        return None
    for bh in proj.get("boreholes", []):
        if bh.get("point_id") == point_id and bh.get("file_path"):
            try:
                fp = Path(bh["file_path"])
                if fp.is_file():
                    text = fp.read_text(encoding="utf-8", errors="ignore")
                    data = parse_snd_full(text)
                    graph = {
                        "depth": data["depth"],
                        "c2": data["c2"],
                        "c3": data.get("c3", []),
                        "c4": data.get("c4", []),
                        "spyling": data.get("spyling", []),
                        "slag": data.get("slag", []),
                    }
                    _store_graph_data(project_name, point_id, graph)
                    return graph
            except Exception:
                pass
    return None


def load_snd_project(folder_path: str, source_epsg: int) -> dict | None:
    """
    Load a project from a folder containing an AUTOGRAF subfolder with .SND files.
    Accepts three forms:
      1. Parent folder (e.g. C:\\Projects\\MyProj) containing AUTOGRAF.DBF/ or AUTOGRAF.BDF/
      2. The AUTOGRAF folder itself (e.g. C:\\Projects\\MyProj\\AUTOGRAF.DBF)
      3. Any folder that directly contains .SND files
    The project name is derived from the parent/project folder name.
    If source_epsg is 0, try to auto-detect from Info.prj.
    """
    folder = Path(folder_path)
    if not folder.is_dir():
        return None

    # Determine autograf_dir and project_name
    autograf_dir = None
    folder_upper = folder.name.upper()

    # Case 1: user pointed at the AUTOGRAF folder directly
    if folder_upper.startswith("AUTOGRAF") and list(folder.glob("*.SND")):
        autograf_dir = folder
        project_name = folder.parent.name
    else:
        # Case 2: look for any AUTOGRAF.* subfolder (case-insensitive)
        for child in folder.iterdir():
            if child.is_dir() and child.name.upper().startswith("AUTOGRAF"):
                autograf_dir = child
                break
        project_name = folder.name

    # Case 3: folder itself contains .SND files (no AUTOGRAF subfolder)
    if autograf_dir is None:
        direct_snd = list(folder.glob("*.SND"))
        if direct_snd:
            autograf_dir = folder
            project_name = folder.name

    if autograf_dir is None:
        return None

    # Auto-detect EPSG from Info.prj if available
    detected_epsg = _detect_epsg_from_project(folder)
    if detected_epsg:
        source_epsg = detected_epsg

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
            # Validate transformed coordinates
            if not (math.isfinite(lat) and math.isfinite(lon)
                    and -90 <= lat <= 90 and -180 <= lon <= 180):
                errors.append(f"{snd_path.name}: Ugyldige koordinater etter transformasjon (lat={lat}, lon={lon})")
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
            # Store heavy graph data in module-level cache (not in session_state)
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

    # Build convex hull polygon from borehole positions
    coords = [(bh["lat"], bh["lon"]) for bh in boreholes]
    if len(coords) >= 3:
        hull = _hull_with_buffer(coords)
        polygon = hull + [hull[0]]  # close the ring
    else:
        polygon = coords

    return {
        "project_name": project_name,
        "folder_path": str(folder),
        "epsg": source_epsg,
        "detected_epsg": detected_epsg,
        "boreholes": boreholes,
        "polygon": polygon,  # list of (lat, lon)
        "errors": errors,
    }


def build_sounding_figure(bh: dict, project_name: str = "") -> go.Figure:
    """Build a plotly sounding log figure for a borehole."""
    # Get graph data from cache
    graph = get_graph_data(project_name, bh.get("point_id", ""))
    if not graph:
        return go.Figure().update_layout(title="Ingen grafdata tilgjengelig")

    fig = go.Figure()

    # Main resistance trace
    fig.add_trace(go.Scatter(
        x=graph["c2"],
        y=graph["depth"],
        mode="lines",
        name="Motstand (kN)",
        line=dict(color="black", width=1.2),
    ))

    # Spyling segments (blue bands)
    for i, (d0, d1) in enumerate(graph.get("spyling", [])):
        fig.add_hrect(
            y0=d0, y1=d1,
            fillcolor="rgba(30,120,255,0.18)",
            line_width=0,
            annotation_text="Spyling" if i == 0 else None,
            annotation_position="top left",
        )

    # Slag segments (red bands)
    for i, (d0, d1) in enumerate(graph.get("slag", [])):
        fig.add_hrect(
            y0=d0, y1=d1,
            fillcolor="rgba(220,40,40,0.18)",
            line_width=0,
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
# FieldManager API helpers
# ---------------------------------------------------------------------------
FM_BASE_URL = "https://api.fieldmanager.io/fieldmanager"


def _fm_session(token: str) -> _requests.Session:
    """Create a requests session with Bearer auth for FieldManager."""
    s = _requests.Session()
    s.headers.update({
        "Authorization": f"Bearer {token}",
        "accept": "application/json",
    })
    return s


def _fm_get_projects(session: _requests.Session) -> list[dict]:
    """Fetch all projects from FieldManager (paginated)."""
    all_projects: list[dict] = []
    skip = 0
    limit = 100
    while True:
        resp = session.get(
            f"{FM_BASE_URL}/projects",
            params={"skip": skip, "limit": limit},
            timeout=30,
        )
        if resp.status_code == 401:
            raise PermissionError("Ugyldig eller utgått token.")
        if resp.status_code == 422:
            raise ValueError(f"Valideringsfeil: {resp.json()}")
        resp.raise_for_status()
        chunk = resp.json()
        if not chunk:
            break
        all_projects.extend(chunk)
        if len(chunk) < limit:
            break
        skip += limit
    return all_projects


def _fm_get_locations(session: _requests.Session, project_id: str) -> list[dict]:
    """Fetch all locations for a FieldManager project (paginated)."""
    all_locations: list[dict] = []
    skip = 0
    limit = 100
    while True:
        resp = session.get(
            f"{FM_BASE_URL}/projects/{project_id}/locations",
            params={"skip": skip, "limit": limit},
            timeout=30,
        )
        if resp.status_code == 401:
            raise PermissionError("Ugyldig eller utgått token.")
        if resp.status_code == 422:
            raise ValueError(f"Valideringsfeil: {resp.json()}")
        resp.raise_for_status()
        chunk = resp.json()
        if not chunk:
            break
        all_locations.extend(chunk)
        if len(chunk) < limit:
            break
        skip += limit
    return all_locations


def _fm_export_snd_zip(
    session: _requests.Session,
    project_id: str,
    location_id: str,
    swap_x_y: bool = False,
) -> bytes:
    """Export SND ZIP for a location from FieldManager.

    Handles both direct binary responses and presigned-URL JSON responses.
    Returns raw ZIP bytes.
    """
    resp = session.get(
        f"{FM_BASE_URL}/projects/{project_id}/locations/{location_id}/export",
        params={"export_type": "SND", "swap_x_y": str(swap_x_y).lower()},
        stream=True,
        timeout=60,
    )
    if resp.status_code == 401:
        raise PermissionError("Ugyldig eller utgått token.")
    if resp.status_code == 422:
        raise ValueError(f"Valideringsfeil: {resp.json()}")
    resp.raise_for_status()

    content_type = resp.headers.get("Content-Type", "")
    if "application/json" in content_type:
        body = resp.json()
        if isinstance(body, str):
            url = body
        elif isinstance(body, dict) and "url" in body:
            url = body["url"]
        else:
            raise ValueError(f"Uventet JSON-respons fra FieldManager: {body}")
        # Presigned URL – fetch without auth
        dl_resp = _requests.get(url, timeout=120)
        dl_resp.raise_for_status()
        return dl_resp.content
    else:
        # Direct binary ZIP
        return resp.content


def load_snd_from_zip(zip_bytes: bytes, source_epsg: int, project_name: str) -> dict | None:
    """Load a project from a ZIP file containing SND files.

    Extracts SND files to a temp directory, parses them, and builds
    the same project structure as load_snd_project.
    """
    tmp_dir = Path(tempfile.mkdtemp(prefix="fm_snd_"))
    try:
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            zf.extractall(tmp_dir)

        # Find all .SND files recursively in the extracted contents
        snd_files_set = {p.resolve() for p in tmp_dir.rglob("*.SND")}
        snd_files_set |= {p.resolve() for p in tmp_dir.rglob("*.snd")}
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
                    errors.append(f"{snd_path.name}: Ugyldige koordinater (lat={lat}, lon={lon})")
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
            "folder_path": f"FieldManager: {project_name}",
            "epsg": source_epsg,
            "detected_epsg": None,
            "boreholes": boreholes,
            "polygon": polygon,
            "errors": errors,
        }
    except zipfile.BadZipFile:
        return None


@st.cache_data(ttl=300)
def query_nadag_nearby(lat: float, lon: float, radius_m: int = 3) -> pd.DataFrame:
    # EPSG:4326 er et geografisk CRS (grader) – DWITHIN med meters støttes ikke.
    # Beregner en bbox i grader i stedet (~60°N: 1° lat ≈ 111 km, 1° lon ≈ 55.5 km).
    dlat = radius_m / 111_000
    dlon = radius_m / 55_500
    params = {
        "SERVICE": "WFS",
        "VERSION": "2.0.0",
        "REQUEST": "GetFeature",
        "TYPENAMES": "nadag:GB_standard",
        "outputFormat": "application/json",
        "count": "25",
        "bbox": f"{lon - dlon},{lat - dlat},{lon + dlon},{lat + dlat},EPSG:4326",
        "srsName": "EPSG:4326",
    }
    url = "https://geo.ngu.no/geoserver/nadag/ows?" + urlencode(params)
    try:
        with urllib.request.urlopen(url, timeout=10) as r:
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
def query_nadag_polygon(polygon_coords: tuple[tuple[float, float], ...]) -> pd.DataFrame:
    """Query NADAG WFS for borehull inside the bounding box of a polygon.
    polygon_coords: tuple of (lon, lat) pairs.
    """
    lons = [c[0] for c in polygon_coords]
    lats = [c[1] for c in polygon_coords]
    min_lon, max_lon = min(lons), max(lons)
    min_lat, max_lat = min(lats), max(lats)
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
        with urllib.request.urlopen(url, timeout=15) as r:
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


@st.cache_data(ttl=600)
def fetch_nadag_pdf(url: str) -> bytes | None:
    try:
        with urllib.request.urlopen(url, timeout=15) as r:
            return r.read()
    except Exception:
        return None


# ---------------------------------------------------------------------------
# NADAG – investigation details per borehole (GBU_metode)
# ---------------------------------------------------------------------------
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
        with urllib.request.urlopen(url, timeout=10) as r:
            data = json.loads(r.read())
        features = data.get("features", [])
        if not features:
            return pd.DataFrame()
        rows = [f.get("properties", {}).copy() for f in features]
        return pd.DataFrame(rows)
    except Exception:
        return pd.DataFrame()


# Method symbol → colour mapping for depth chart
_METHOD_COLORS = {
    10: "#2196F3",   # Dreietrykksondering
    20: "#4CAF50",   # Trykksondering
    21: "#66BB6A",   # Trykksondering ENVI
    22: "#388E3C",   # Trykksondering/dreietrykksondering
    25: "#8BC34A",   # CPTU
    26: "#CDDC39",   # CPT
    30: "#FF9800",   # Vingeboring
    40: "#9C27B0",   # Prøvetaking
    50: "#F44336",   # Totalsondering
    60: "#E91E63",   # Dreiesondering
    70: "#795548",   # Fjellkontrollboring
    80: "#607D8B",   # Poretrykksmåling
    100: "#455A64",  # Bergkontrollboring/Kjerneboring
}


def build_nadag_depth_chart(
    investigations: pd.DataFrame,
    borenr: str = "",
    elevation: float | None = None,
) -> io.BytesIO | None:
    """Build a matplotlib depth-summary chart from NADAG GBU_metode data.

    Shows each investigation method as a coloured vertical bar with depth ticks.
    """
    if investigations.empty:
        return None

    # Ensure numeric columns
    df = investigations.copy()
    df["boretlengde"] = pd.to_numeric(df.get("boretlengde"), errors="coerce")
    df["borlengdeberg"] = pd.to_numeric(df.get("borlengdeberg"), errors="coerce")
    df["geotekniskmetodesymbol"] = pd.to_numeric(df.get("geotekniskmetodesymbol"), errors="coerce")
    df = df.dropna(subset=["boretlengde"])
    if df.empty:
        return None

    n = len(df)
    fig, ax = plt.subplots(figsize=(max(3, n * 1.2 + 1), 7))
    max_depth = df["boretlengde"].max()

    for i, (_, row) in enumerate(df.iterrows()):
        total = float(row["boretlengde"])
        rock = float(row["borlengdeberg"]) if pd.notna(row.get("borlengdeberg")) else None
        sym = int(row["geotekniskmetodesymbol"]) if pd.notna(row.get("geotekniskmetodesymbol")) else 0
        method = str(row.get("geotekniskmetode") or "Ukjent")
        color = _METHOD_COLORS.get(sym, "#9E9E9E")

        # Soil portion (above rock)
        soil_depth = rock if rock is not None else total
        ax.bar(i, soil_depth, bottom=0, width=0.6, color=color, alpha=0.7, edgecolor="black", linewidth=0.8)
        # Rock portion (from rock contact to total depth)
        if rock is not None and total > rock:
            ax.bar(i, total - rock, bottom=rock, width=0.6, color="#BDBDBD", alpha=0.6,
                   edgecolor="black", linewidth=0.8, hatch="//")
        # Mark rock contact
        if rock is not None:
            ax.plot([i - 0.35, i + 0.35], [rock, rock], "k-", linewidth=2)
            ax.text(i + 0.35, rock, f" Berg {rock:.1f}m", fontsize=7, va="center")

        # Total depth annotation
        ax.text(i, total + max_depth * 0.02, f"{total:.1f}m", ha="center", fontsize=8, fontweight="bold")

        # Method label at top
        short = method[:18] + ("…" if len(method) > 18 else "")
        ax.text(i, -max_depth * 0.04, short, ha="center", fontsize=7, rotation=30)

    ax.set_ylim(max_depth * 1.15, -max_depth * 0.12)
    ax.set_xlim(-0.5, n - 0.5)
    ax.set_xticks([])
    ax.set_ylabel("Dybde (m)", fontsize=10)
    ax.grid(True, axis="y", alpha=0.3, linestyle=":")

    title = f"NADAG – {borenr}" if borenr else "NADAG borehull"
    if elevation is not None:
        title += f"  (kote {elevation:.1f})"
    ax.set_title(title, fontsize=11)
    plt.tight_layout(pad=0.5)

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=110, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf


def detail_url(kind: str, item_id: str) -> str:
    encoded = quote(str(item_id), safe="")
    return f"?view=detail&kind={kind}&id={encoded}"


def detail_button_html(url: str, label: str = "Åpne arkivside ↗") -> str:
    full_expr = f"window.open(window.top.location.origin + window.top.location.pathname + '{url}', '_blank')"
    return (
        '<button style="margin-top:8px;padding:6px 10px;border:none;border-radius:6px;'
        'background:#1f77b4;color:white;cursor:pointer;" onclick="%s">%s</button>' % (full_expr, label)
    )


def add_base_maps(m: folium.Map) -> None:
    folium.TileLayer("OpenStreetMap", name="OpenStreetMap", control=True).add_to(m)
    folium.TileLayer("CartoDB Positron", name="CartoDB Positron", control=True, show=False).add_to(m)
    folium.TileLayer("CartoDB Voyager", name="CartoDB Voyager", control=True, show=False).add_to(m)
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri",
        name="Esri World Imagery",
        overlay=False,
        control=True,
        show=False,
    ).add_to(m)


# ---------------------------------------------------------------------------
# Point-in-polygon (ray-casting)
# ---------------------------------------------------------------------------
def normalize_polygon_coords(coords: list[list[float]]) -> list[list[float]]:
    """Ensure coords are in GeoJSON [lon, lat] order.
    Leaflet sometimes returns [lat, lon] – detect via Norway lat range (>50°).
    """
    if not coords:
        return coords
    first = coords[0]
    if len(first) >= 2 and first[0] > 50:  # first value looks like lat, not lon
        return [[c[1], c[0]] for c in coords]
    return coords


def point_in_polygon(lat: float, lon: float, polygon_coords: list[list[float]]) -> bool:
    """Ray-casting algorithm. polygon_coords must be in [lon, lat] order."""
    n = len(polygon_coords)
    inside = False
    x, y = lon, lat
    j = n - 1
    for i in range(n):
        xi, yi = polygon_coords[i][0], polygon_coords[i][1]  # lon, lat
        xj, yj = polygon_coords[j][0], polygon_coords[j][1]
        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi) + xi):
            inside = not inside
        j = i
    return inside


def filter_points_in_polygon(df: pd.DataFrame, polygon_coords: list[list[float]],
                              lat_col: str = "lat", lon_col: str = "lon") -> pd.DataFrame:
    if df.empty:
        return df
    mask = [point_in_polygon(float(row[lat_col]), float(row[lon_col]), polygon_coords)
            for _, row in df.iterrows()]
    return df[mask].copy()


# ---------------------------------------------------------------------------
# Azure AI Foundry – area summary
# ---------------------------------------------------------------------------
def call_azure_ai_summary(prompt_text: str) -> str:
    """Call Azure OpenAI (AI Foundry) chat completions endpoint via SDK."""
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "https://aoai-acc-bot-dev.openai.azure.com/")
    api_key = os.getenv("AZURE_OPENAI_API_KEY", "")
    deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4.1")
    api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")

    if not api_key:
        return "⚠️ Azure AI-nøkkel mangler. Sett AZURE_OPENAI_API_KEY som miljøvariabel."

    try:
        client = AzureOpenAI(
            azure_endpoint=endpoint,
            api_key=api_key,
            api_version=api_version,
        )
        response = client.chat.completions.create(
            model=deployment,
            messages=[
                {"role": "system", "content": (
                    "Du er en geoteknisk rådgiver som oppsummerer undersøkelsesdata for et valgt område. "
                    "Gi en konsis, faglig norsk oppsummering med nøkkelfunn, risikoforhold og anbefalinger. "
                    "Bruk markdown-formatering."
                )},
                {"role": "user", "content": prompt_text},
            ],
            max_completion_tokens=13107,
            temperature=1.0,
            top_p=1.0,
            frequency_penalty=0.0,
            presence_penalty=0.0,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"❌ Feil ved kall mot Azure AI: {e}"


def build_area_prompt(points_df: pd.DataFrame, reports_df: pd.DataFrame,
                      projects_geojson: dict, lab_df: pd.DataFrame,
                      project_meta: pd.DataFrame,
                      nadag_df: pd.DataFrame | None = None) -> str:
    """Build a structured prompt from all data within the selected polygon."""
    lines = ["# Data for valgt omr\u00e5de\n"]

    # NADAG borrehull
    if nadag_df is not None and not nadag_df.empty:
        lines.append(f"## NADAG-borehull ({len(nadag_df)} stk)")
        cols_show = ["borenr", "prosjektnavn", "oppdragstaker", "borlengdeberg",
                     "datafangstdato", "kvikkleirepaavisning", "_lat", "_lon"]
        cols_avail = [c for c in cols_show if c in nadag_df.columns]
        for _, r in nadag_df.head(50).iterrows():
            parts = [f"{c}={r[c]}" for c in cols_avail if pd.notna(r.get(c))]
            lines.append(f"- {', '.join(parts)}")
        if len(nadag_df) > 50:
            lines.append(f"  ... og {len(nadag_df) - 50} til")
        lines.append("")

    # Investigation points
    if not points_df.empty:
        lines.append(f"## Undersøkelsespunkter ({len(points_df)} stk)")
        for _, r in points_df.iterrows():
            lines.append(
                f"- **{r['point_id']}**: {r['method']}, dybde {r['depth_m']} m, "
                f"år {r['year']}, status {r['status']}, prosjekt {r['project']}. "
                f"Merknad: {r.get('notes', '')}"
            )
        lines.append("")

    # Lab results for points in area
    area_point_ids = points_df["point_id"].tolist()
    area_lab = lab_df[lab_df["point_id"].isin(area_point_ids)] if not lab_df.empty else pd.DataFrame()
    if not area_lab.empty:
        lines.append(f"## Labresultater ({len(area_lab)} stk)")
        for _, r in area_lab.iterrows():
            lines.append(
                f"- {r['point_id']}/{r['sample_id']}: {r['test_type']} = {r['value']} {r['unit']} "
                f"(dybde {r['depth_from_m']}-{r['depth_to_m']} m)"
            )
        lines.append("")

    # Reports
    if not reports_df.empty:
        lines.append(f"## Rapporter ({len(reports_df)} stk)")
        for _, r in reports_df.iterrows():
            lines.append(f"- **{r['title']}** ({r['category']}, {r['year']})")
        lines.append("")

    # Projects
    area_archive_ids = points_df["archive_id"].unique().tolist() if not points_df.empty else []
    area_projects = project_meta[project_meta["archive_id"].isin(area_archive_ids)] if not project_meta.empty else pd.DataFrame()
    if not area_projects.empty:
        lines.append(f"## Prosjekter ({len(area_projects)} stk)")
        for _, r in area_projects.iterrows():
            lines.append(
                f"- **{r['project']}** ({r['discipline']}, {r['year']}): {r['summary']}"
            )
        lines.append("")

    lines.append("\nGi en oppsummering av området basert på dataene over. "
                 "Inkluder: geotekniske forhold, grunnforhold, eventuelle miljøforhold, "
                 "risikoer og anbefalinger for videre arbeid.")
    return "\n".join(lines)


def polygon_centroid(coordinates: list) -> tuple[float, float]:
    ring = coordinates[0]
    lons = [p[0] for p in ring[:-1]]
    lats = [p[1] for p in ring[:-1]]
    return sum(lats) / len(lats), sum(lons) / len(lons)


# ---------------------------------------------------------------------------
# Kartverket elevation API
# ---------------------------------------------------------------------------
def _fetch_kartverket_elevation(lat: float, lon: float) -> float | None:
    """Get terrain elevation (m.o.h.) from Kartverket Høydedata API."""
    url = (f"https://ws.geonorge.no/hoydedata/v1/punkt"
           f"?nord={lat}&ost={lon}&koordsys=4258")
    req = urllib.request.Request(url, headers={"User-Agent": "OsloGeoArkiv/1.0"})
    try:
        resp = urllib.request.urlopen(req, timeout=10)
        data = json.loads(resp.read())
        pts = data.get("punkter", [])
        if pts and pts[0].get("z") is not None:
            return float(pts[0]["z"])
    except Exception:
        pass
    return None


def _fetch_kartverket_elevations(coords_latlon: list[tuple[float, float]]) -> list[float]:
    """Fetch terrain elevation for a list of (lat, lon) pairs.
    Returns list of Z values; uses 0.0 as fallback where API fails."""
    zs: list[float] = []
    for lat, lon in coords_latlon:
        z = _fetch_kartverket_elevation(lat, lon)
        zs.append(z if z is not None else 0.0)
    return zs


# ---------------------------------------------------------------------------
# Cross-section / Tverrprofil helpers
# ---------------------------------------------------------------------------
def _haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Haversine distance in meters between two lat/lon points."""
    R = 6_371_000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _snap_vertices_to_boreholes(
    vertices: list[tuple[float, float]],
    loaded_projects: dict,
    max_dist_m: float = 100.0,
) -> list[dict | None]:
    """For each vertex (lat, lon), find the nearest project borehole within max_dist_m.
    Also computes cumulative distance along the polyline for each vertex."""
    # Cumulative distances along the polyline
    vertex_dists = [0.0]
    for i in range(1, len(vertices)):
        d = _haversine_m(vertices[i - 1][0], vertices[i - 1][1],
                         vertices[i][0], vertices[i][1])
        vertex_dists.append(vertex_dists[-1] + d)

    results: list[dict | None] = []
    for idx, (vlat, vlon) in enumerate(vertices):
        best = None
        best_dist = float("inf")
        for proj_name, proj in loaded_projects.items():
            for bh in proj.get("boreholes", []):
                d = _haversine_m(vlat, vlon, bh["lat"], bh["lon"])
                if d < best_dist:
                    best_dist = d
                    best = {
                        "borehole": bh,
                        "project_name": proj_name,
                        "snap_dist": d,
                        "distance": vertex_dists[idx],
                        "terrain_z": bh.get("elevation", 0),
                    }
        if best and best_dist <= max_dist_m:
            results.append(best)
        else:
            results.append(None)
    return results


def _interpolate_line_coords(
    vertices: list[tuple[float, float]],
    n_samples: int = 20,
) -> list[tuple[float, float, float]]:
    """Interpolate n_samples evenly spaced points along a polyline.
    Returns list of (lat, lon, cumulative_distance_m)."""
    if len(vertices) < 2:
        return [(vertices[0][0], vertices[0][1], 0.0)] if vertices else []
    seg_lengths = []
    for i in range(len(vertices) - 1):
        seg_lengths.append(_haversine_m(vertices[i][0], vertices[i][1],
                                        vertices[i + 1][0], vertices[i + 1][1]))
    total_length = sum(seg_lengths)
    if total_length < 1:
        return [(vertices[0][0], vertices[0][1], 0.0)]

    points: list[tuple[float, float, float]] = []
    for si in range(n_samples):
        target_d = si * total_length / (n_samples - 1)
        cum = 0.0
        for i, sl in enumerate(seg_lengths):
            if cum + sl >= target_d or i == len(seg_lengths) - 1:
                t = (target_d - cum) / sl if sl > 0 else 0.0
                t = max(0.0, min(1.0, t))
                lat = vertices[i][0] + t * (vertices[i + 1][0] - vertices[i][0])
                lon = vertices[i][1] + t * (vertices[i + 1][1] - vertices[i][1])
                points.append((lat, lon, target_d))
                break
            cum += sl
    return points


def build_cross_section_figure(
    matched_boreholes: list[dict],
    terrain_dists: list[float],
    terrain_zs: list[float],
) -> io.BytesIO:
    """Build a unified cross-section figure with terrain profile and borehole
    sounding diagrams drawn inline at each point's position.

    The sounding resistance (kN) is scaled horizontally and plotted at the
    borehole's position along the profile, with depth mapped to real elevation
    (kote = terrain_z - depth).  This lets the user interpret geology in
    relation to terrain height.
    """
    n_bh = len(matched_boreholes)
    total_dist = max(terrain_dists) if terrain_dists else 1

    fig, ax = plt.subplots(figsize=(max(14, n_bh * 4), 10))

    # --- Terrain profile ---
    ax.fill_between(terrain_dists, terrain_zs,
                    min(terrain_zs) - 5, alpha=0.12, color="#4CAF50")
    ax.plot(terrain_dists, terrain_zs, "-", color="#2E7D32",
            linewidth=2.5, label="Terrengprofil", zorder=3)

    overall_min_elev = min(terrain_zs) if terrain_zs else 0

    # Determine a common horizontal scale-width for sounding traces.
    # Each sounding is drawn as a horizontal deviation from the borehole's
    # x-position on the profile.  We allocate a fraction of the total profile
    # distance per borehole so they don't overlap too much.
    if n_bh >= 2:
        dists_sorted = sorted(info["distance"] for info in matched_boreholes)
        min_gap = min(dists_sorted[i + 1] - dists_sorted[i] for i in range(len(dists_sorted) - 1))
        sounding_width = max(min_gap * 0.45, total_dist * 0.04)
    else:
        sounding_width = total_dist * 0.12

    # Collect max resistance across all boreholes for uniform scaling
    global_max_c2 = 1.0
    for info in matched_boreholes:
        bh = info["borehole"]
        graph = get_graph_data(info.get("project_name", ""), bh.get("point_id", ""))
        if graph and graph.get("c2"):
            mc2 = max(graph["c2"])
            if mc2 > global_max_c2:
                global_max_c2 = mc2

    # --- Draw each borehole's sounding inline ---
    colors_cycle = ["#1565C0", "#C62828", "#2E7D32", "#6A1B9A", "#E65100", "#00838F"]

    for idx, info in enumerate(matched_boreholes):
        bh = info["borehole"]
        dist = info["distance"]
        tz = info.get("terrain_z", bh.get("elevation", 0))
        max_d = bh.get("max_depth", 0)
        bottom_z = tz - max_d
        if bottom_z < overall_min_elev:
            overall_min_elev = bottom_z

        proj_name = info.get("project_name", "")
        trace_color = colors_cycle[idx % len(colors_cycle)]

        # Vertical borehole shaft line
        ax.plot([dist, dist], [tz, bottom_z],
                color="gray", linewidth=0.8, linestyle="--", alpha=0.6, zorder=2)

        # Marker on terrain
        ax.plot(dist, tz, "v", color="#D32F2F", markersize=12, zorder=8)

        # Label
        ax.annotate(
            f"{bh['point_id']}\n{tz:.1f} m.o.h.",
            (dist, tz),
            textcoords="offset points", xytext=(0, 14),
            ha="center", fontsize=9, fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="white",
                      edgecolor="gray", alpha=0.9),
            zorder=10,
        )

        # Get sounding data
        graph = get_graph_data(proj_name, bh.get("point_id", ""))
        if not graph or not graph.get("depth") or not graph.get("c2"):
            # No graph data – just mark the bottom
            ax.plot(dist, bottom_z, "_", color="black", markersize=10, zorder=5)
            continue

        depths = list(graph["depth"])
        c2vals = list(graph["c2"])

        # Convert: depth -> elevation, resistance -> horizontal offset
        elevations = [tz - d for d in depths]
        x_offsets = [dist + (c / global_max_c2) * sounding_width for c in c2vals]

        # Fill area between borehole centerline and resistance trace
        ax.fill_betweenx(elevations, dist, x_offsets,
                         alpha=0.15, color=trace_color, zorder=4)

        # Resistance trace
        ax.plot(x_offsets, elevations, "-", color=trace_color,
                linewidth=1.3, zorder=6,
                label=f"{bh['point_id']} – Motstand" if idx == 0 else None)

        # Spyling segments (blue horizontal bands)
        for s_d, e_d in graph.get("spyling", []):
            z_top_s = tz - s_d
            z_bot_s = tz - e_d
            ax.axhspan(z_bot_s, z_top_s, xmin=0, xmax=1,
                       alpha=0.0, zorder=0)  # invisible full-width
            ax.fill_between(
                [dist - sounding_width * 0.08, dist + sounding_width * 0.08],
                z_bot_s, z_top_s,
                alpha=0.35, color="#2196F3", zorder=5,
            )

        # Slag segments (red horizontal bands)
        for s_d, e_d in graph.get("slag", []):
            z_top_s = tz - s_d
            z_bot_s = tz - e_d
            ax.fill_between(
                [dist - sounding_width * 0.08, dist + sounding_width * 0.08],
                z_bot_s, z_top_s,
                alpha=0.35, color="#F44336", zorder=5,
            )

        # Bottom marker
        ax.plot(dist, bottom_z, "_", color="black", markersize=10, zorder=7)

    # --- Axes & labels ---
    ax.set_xlabel("Avstand langs profil (m)", fontsize=12)
    ax.set_ylabel("Kote (m.o.h.)", fontsize=12)
    ax.set_title("Tverrprofil \u2013 Terreng og sonderingsdata", fontsize=14, fontweight="bold")
    ax.grid(True, alpha=0.3, linestyle=":")

    # Legend
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch
    legend_items = [
        Line2D([0], [0], color="#2E7D32", linewidth=2.5, label="Terrengprofil"),
        Line2D([0], [0], color="gray", linewidth=1, linestyle="--", label="Borehull"),
        Patch(facecolor=colors_cycle[0], alpha=0.3, label="Motstand (kN)"),
        Patch(facecolor="#2196F3", alpha=0.4, label="Spyling"),
        Patch(facecolor="#F44336", alpha=0.4, label="Slag"),
    ]
    ax.legend(handles=legend_items, loc="upper right", fontsize=9)

    # Y limits
    y_pad = max((max(terrain_zs) - overall_min_elev) * 0.12, 3)
    ax.set_ylim(overall_min_elev - y_pad, max(terrain_zs) + y_pad + 8)

    # Scale annotation
    ax.annotate(
        f"Motstandsskala: {global_max_c2:.0f} kN = {sounding_width:.0f} m horisontal bredde",
        xy=(0.01, 0.01), xycoords="axes fraction",
        fontsize=8, color="gray", style="italic",
    )

    plt.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=140, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf


# ---------------------------------------------------------------------------
# IFC 3D ground model generation
# ---------------------------------------------------------------------------
def _generate_ifc_ground_model(
    polygon_coords: list[list[float]],
    area_points: pd.DataFrame,
    area_proj_boreholes: list[dict],
) -> bytes:
    """Generate an IFC file with three stacked soil layers (clay/sand/rock)
    based on borehole depths inside the polygon.

    Terrain elevation is fetched from Kartverket Høydedata API.
    Each borehole depth is split into thirds:
      - Top 1/3  → Clay (Leire)
      - Mid 1/3  → Sand
      - Bot 1/3  → Rock (Fjell)

    The polygon footprint is extruded for each layer.
    Returns IFC file content as bytes.
    """
    import ifcopenshell
    import ifcopenshell.api
    import numpy as np

    # ── Collect borehole depths ─────────────────────────────────────────
    depths: list[float] = []

    if not area_points.empty:
        for _, r in area_points.iterrows():
            depths.append(float(r["depth_m"]))

    for bh in area_proj_boreholes:
        depths.append(float(bh["max_depth"]))

    # ── Fetch real terrain elevation from Kartverket ────────────────────
    # Get elevations at polygon vertices for terrain surface
    poly_latlon = [(c[1], c[0]) for c in polygon_coords]  # [lon,lat] -> (lat,lon)
    vertex_zs = _fetch_kartverket_elevations(poly_latlon)
    avg_terrain_z = float(np.mean(vertex_zs))

    # If we have borehole data, use average depth; otherwise default 20m
    avg_depth = float(np.mean(depths)) if depths else 20.0
    layer_thickness = avg_depth / 3.0

    # Layer boundaries (Z from top to bottom, elevation-relative)
    z_top = avg_terrain_z
    z_clay_bot = z_top - layer_thickness
    z_sand_bot = z_clay_bot - layer_thickness
    z_rock_bot = z_sand_bot - layer_thickness

    # ── Convert polygon coords (lon/lat) to local metric (UTM33) ──────
    transformer = Transformer.from_crs("EPSG:4326", "EPSG:25833", always_xy=True)
    utm_coords = []
    for c in polygon_coords:
        ex, ny = transformer.transform(c[0], c[1])  # lon, lat -> easting, northing
        utm_coords.append((ex, ny))

    # Compute centroid for local origin (keeps IFC coordinates small)
    cx = sum(p[0] for p in utm_coords) / len(utm_coords)
    cy = sum(p[1] for p in utm_coords) / len(utm_coords)
    local_pts = [(p[0] - cx, p[1] - cy) for p in utm_coords]

    # ── Create IFC model ──────────────────────────────────────────────
    model = ifcopenshell.api.run("project.create_file")
    project = ifcopenshell.api.run("root.create_entity", model, ifc_class="IfcProject", name="Grunnmodell")
    ifcopenshell.api.run("unit.assign_unit", model)
    ctx = ifcopenshell.api.run("context.add_context", model, context_type="Model",
                                context_identifier="Body", target_view="MODEL_VIEW")
    site = ifcopenshell.api.run("root.create_entity", model, ifc_class="IfcSite", name="Omraadet")
    ifcopenshell.api.run("aggregate.assign_object", model, relating_object=project, products=[site])
    building = ifcopenshell.api.run("root.create_entity", model, ifc_class="IfcBuilding", name="Grunnmodell")
    ifcopenshell.api.run("aggregate.assign_object", model, relating_object=site, products=[building])
    storey = ifcopenshell.api.run("root.create_entity", model, ifc_class="IfcBuildingStorey", name="Terreng")
    ifcopenshell.api.run("aggregate.assign_object", model, relating_object=building, products=[storey])

    layers = [
        ("Leire", z_top, z_clay_bot, (0.6, 0.45, 0.25)),          # brown
        ("Sand", z_clay_bot, z_sand_bot, (0.9, 0.85, 0.55)),      # yellow
        ("Fjell", z_sand_bot, z_rock_bot, (0.55, 0.55, 0.55)),    # grey
    ]

    for name, ztop, zbot, rgb in layers:
        thickness = abs(ztop - zbot)
        if thickness < 0.01:
            continue

        element = ifcopenshell.api.run("root.create_entity", model,
                                        ifc_class="IfcBuildingElementProxy",
                                        name=name)
        ifcopenshell.api.run("spatial.assign_container", model,
                              relating_structure=storey, products=[element])

        # Build extruded area solid
        pts = [model.createIfcCartesianPoint((p[0], p[1])) for p in local_pts]
        if local_pts[0] != local_pts[-1]:
            pts.append(pts[0])
        polyline = model.createIfcPolyline(pts)
        profile = model.createIfcArbitraryClosedProfileDef("AREA", name, polyline)

        extrusion_dir = model.createIfcDirection((0.0, 0.0, 1.0))
        position = model.createIfcAxis2Placement3D(
            model.createIfcCartesianPoint((0.0, 0.0, zbot)),
            model.createIfcDirection((0.0, 0.0, 1.0)),
            model.createIfcDirection((1.0, 0.0, 0.0)),
        )
        solid = model.createIfcExtrudedAreaSolid(profile, position, extrusion_dir, thickness)

        body_rep = model.createIfcShapeRepresentation(ctx, "Body", "SweptSolid", [solid])
        prod_shape = model.createIfcProductDefinitionShape(None, None, [body_rep])
        element.Representation = prod_shape

        placement_pt = model.createIfcCartesianPoint((0.0, 0.0, 0.0))
        placement = model.createIfcAxis2Placement3D(placement_pt)
        element.ObjectPlacement = model.createIfcLocalPlacement(None, placement)

        # Assign colour
        style = ifcopenshell.api.run("style.add_style", model, name=f"Farge_{name}")
        ifcopenshell.api.run("style.add_surface_style", model,
                              style=style, ifc_class="IfcSurfaceStyleShading",
                              attributes={"SurfaceColour": {
                                  "Name": name,
                                  "Red": rgb[0], "Green": rgb[1], "Blue": rgb[2],
                              }})
        ifcopenshell.api.run("style.assign_representation_styles", model,
                              shape_representation=body_rep, styles=[style])

    # ── Write to bytes ────────────────────────────────────────────────
    tmp = tempfile.NamedTemporaryFile(suffix=".ifc", delete=False)
    tmp.close()
    try:
        model.write(tmp.name)
        return Path(tmp.name).read_bytes()
    finally:
        Path(tmp.name).unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# Bergmodell – fetch stop codes and generate IFC rock surface
# ---------------------------------------------------------------------------
def _fetch_stoppkoder_for_boreholes(nadag_area_df: pd.DataFrame) -> dict[str, list[dict]]:
    """For each NADAG borehole in the area, query GBU_metode and collect
    investigation details including stoppkode.

    Returns dict: lokalid -> list of investigation dicts with keys:
      stoppkode, boretlengde, geotekniskmetode, geotekniskmetodesymbol
    """
    result: dict[str, list[dict]] = {}
    if nadag_area_df.empty:
        return result
    for _, row in nadag_area_df.iterrows():
        lokalid = row.get("lokalid")
        if not lokalid:
            continue
        inv_df = query_nadag_investigations(str(lokalid))
        if inv_df.empty:
            continue
        investigations = []
        for _, inv_row in inv_df.iterrows():
            stop = inv_row.get("stoppkode") or ""
            depth = inv_row.get("boretlengde")
            if pd.notna(depth):
                depth = float(depth)
            else:
                depth = None
            investigations.append({
                "stoppkode": str(stop).strip(),
                "boretlengde": depth,
                "geotekniskmetode": inv_row.get("geotekniskmetode") or "",
            })
        if investigations:
            result[str(lokalid)] = investigations
    return result


def _collect_unique_stoppkoder(inv_by_bh: dict[str, list[dict]]) -> list[str]:
    """Extract unique non-empty stop codes from investigation data."""
    codes = set()
    for invs in inv_by_bh.values():
        for inv in invs:
            code = inv.get("stoppkode", "")
            if code:
                codes.add(code)
    return sorted(codes)


def _generate_ifc_bergmodell(
    nadag_area_df: pd.DataFrame,
    inv_by_bh: dict[str, list[dict]],
    selected_stoppkoder: list[str],
) -> bytes:
    """Generate an IFC file with a triangulated rock surface (bergmodell).

    Only boreholes whose investigations have a matching stoppkode are included.
    The surface Z is computed as: terrain_elevation - boretlengde (bore depth).

    Returns IFC file content as bytes.
    """
    import ifcopenshell
    import ifcopenshell.api
    import numpy as np
    from scipy.spatial import Delaunay

    selected_set = set(selected_stoppkoder)

    # Collect points: (lat, lon, rock_z)
    surface_points: list[tuple[float, float, float, str]] = []  # lat, lon, z, label
    for _, row in nadag_area_df.iterrows():
        lokalid = str(row.get("lokalid") or "")
        if lokalid not in inv_by_bh:
            continue
        invs = inv_by_bh[lokalid]
        # Find investigations matching selected stop codes
        matching_depths = []
        for inv in invs:
            if inv["stoppkode"] in selected_set and inv["boretlengde"] is not None:
                matching_depths.append(inv["boretlengde"])
        if not matching_depths:
            continue

        bore_depth = max(matching_depths)
        lat = row.get("_lat")
        lon = row.get("_lon")
        elevation = row.get("hoeyde")

        if lat is None or lon is None:
            continue

        lat = float(lat)
        lon = float(lon)

        # Terrain elevation: use NADAG hoeyde if available, else fetch from Kartverket
        if elevation is not None and pd.notna(elevation):
            terrain_z = float(elevation)
        else:
            fetched = _fetch_kartverket_elevation(lat, lon)
            terrain_z = fetched if fetched is not None else 0.0

        rock_z = terrain_z - bore_depth
        borenr = str(row.get("borenr") or lokalid)
        surface_points.append((lat, lon, rock_z, borenr))

    if len(surface_points) < 3:
        raise ValueError(
            f"For få borehull med valgte stoppkoder ({len(surface_points)} stk). "
            f"Trenger minst 3 for å lage en flate."
        )

    # Convert to UTM33 for IFC coordinates
    transformer = Transformer.from_crs("EPSG:4326", "EPSG:25833", always_xy=True)
    utm_points = []
    for lat, lon, z, label in surface_points:
        ex, ny = transformer.transform(lon, lat)
        utm_points.append((ex, ny, z, label))

    # Centroid for local origin
    cx = sum(p[0] for p in utm_points) / len(utm_points)
    cy = sum(p[1] for p in utm_points) / len(utm_points)
    local_pts = [(p[0] - cx, p[1] - cy, p[2]) for p in utm_points]

    # Delaunay triangulation on 2D (x, y)
    pts_2d = np.array([(p[0], p[1]) for p in local_pts])
    tri = Delaunay(pts_2d)
    triangles = tri.simplices  # (N, 3) array of vertex indices

    # ── Create IFC model ──────────────────────────────────────────────
    model = ifcopenshell.api.run("project.create_file")
    project = ifcopenshell.api.run("root.create_entity", model,
                                    ifc_class="IfcProject", name="Bergmodell")
    ifcopenshell.api.run("unit.assign_unit", model)
    ctx = ifcopenshell.api.run("context.add_context", model, context_type="Model",
                                context_identifier="Body", target_view="MODEL_VIEW")
    site = ifcopenshell.api.run("root.create_entity", model,
                                 ifc_class="IfcSite", name="Omraadet")
    ifcopenshell.api.run("aggregate.assign_object", model,
                          relating_object=project, products=[site])
    building = ifcopenshell.api.run("root.create_entity", model,
                                     ifc_class="IfcBuilding", name="Bergmodell")
    ifcopenshell.api.run("aggregate.assign_object", model,
                          relating_object=site, products=[building])
    storey = ifcopenshell.api.run("root.create_entity", model,
                                   ifc_class="IfcBuildingStorey", name="Bergoverflate")
    ifcopenshell.api.run("aggregate.assign_object", model,
                          relating_object=building, products=[storey])

    # ── Build triangulated face set ───────────────────────────────────
    # IFC IfcTriangulatedFaceSet: coordinates + triangle indices (1-based)
    coord_list = [model.createIfcCartesianPoint((p[0], p[1], p[2])) for p in local_pts]

    # Create IfcCartesianPointList3D
    coords_tuples = tuple((p[0], p[1], p[2]) for p in local_pts)
    point_list = model.createIfcCartesianPointList3D(coords_tuples)

    # Triangle indices (IFC uses 1-based indexing)
    ifc_triangles = []
    for t in triangles:
        ifc_triangles.append((int(t[0]) + 1, int(t[1]) + 1, int(t[2]) + 1))

    face_set = model.createIfcTriangulatedFaceSet(
        point_list,
        None,  # Normals
        None,  # Closed
        ifc_triangles,
    )

    element = ifcopenshell.api.run("root.create_entity", model,
                                    ifc_class="IfcBuildingElementProxy",
                                    name="Bergoverflate")
    ifcopenshell.api.run("spatial.assign_container", model,
                          relating_structure=storey, products=[element])

    body_rep = model.createIfcShapeRepresentation(ctx, "Body", "Tessellation", [face_set])
    prod_shape = model.createIfcProductDefinitionShape(None, None, [body_rep])
    element.Representation = prod_shape

    placement_pt = model.createIfcCartesianPoint((0.0, 0.0, 0.0))
    placement = model.createIfcAxis2Placement3D(placement_pt)
    element.ObjectPlacement = model.createIfcLocalPlacement(None, placement)

    # Assign grey rock colour
    style = ifcopenshell.api.run("style.add_style", model, name="Farge_Berg")
    ifcopenshell.api.run("style.add_surface_style", model,
                          style=style, ifc_class="IfcSurfaceStyleShading",
                          attributes={"SurfaceColour": {
                              "Name": "Berg",
                              "Red": 0.6, "Green": 0.6, "Blue": 0.65,
                          }})
    ifcopenshell.api.run("style.assign_representation_styles", model,
                          shape_representation=body_rep, styles=[style])

    # ── Write to bytes ────────────────────────────────────────────────
    tmp = tempfile.NamedTemporaryFile(suffix=".ifc", delete=False)
    tmp.close()
    try:
        model.write(tmp.name)
        return Path(tmp.name).read_bytes()
    finally:
        Path(tmp.name).unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# 3D Borehole Viewer (PyDeck)
# ---------------------------------------------------------------------------

def _build_terrain_grid(
    polygon_coords: list[list[float]], resolution: int = 12
) -> list[dict]:
    """Build a grid of elevation points within the polygon bounding box.
    Returns list of dicts with lat, lon, z for PyDeck.
    """
    lons = [c[0] for c in polygon_coords]
    lats = [c[1] for c in polygon_coords]
    min_lon, max_lon = min(lons), max(lons)
    min_lat, max_lat = min(lats), max(lats)

    # Create a grid
    lat_steps = max(3, resolution)
    lon_steps = max(3, resolution)
    grid_points: list[tuple[float, float]] = []
    for i in range(lat_steps + 1):
        for j in range(lon_steps + 1):
            lat = min_lat + (max_lat - min_lat) * i / lat_steps
            lon = min_lon + (max_lon - min_lon) * j / lon_steps
            grid_points.append((lat, lon))

    # Fetch elevations (batch)
    zs = _fetch_kartverket_elevations(grid_points)

    terrain = []
    for (lat, lon), z in zip(grid_points, zs):
        terrain.append({"lat": lat, "lon": lon, "z": z})
    return terrain


def build_3d_sounding_plotly(
    area_proj_boreholes: list[dict],
    nadag_area_df: pd.DataFrame,
    area_points: pd.DataFrame,
    polygon_coords: list[list[float]],
    loaded_projects: dict,
    terrain_grid: list[dict] | None = None,
    terrain_resolution: int = 10,
    graph_azimuth_deg: float = 135.0,
) -> go.Figure:
    """Build a Plotly 3D figure with terrain surface, borehole shafts and
    actual SND resistance curves drawn as 3D curtains.

    graph_azimuth_deg: bearing the resistance curves extend toward
    (0 = North, 90 = East, 180 = South, 270 = West).
    Set this to match the viewer’s current horizontal viewing direction
    to achieve a billboard-like effect.
    """
    import numpy as np
    from scipy.spatial import Delaunay

    fig = go.Figure()

    # ── Local UTM33 coordinate system (metres from polygon centroid) ───
    t2utm = Transformer.from_crs("EPSG:4326", "EPSG:25833", always_xy=True)
    poly_lons = [c[0] for c in polygon_coords]
    poly_lats = [c[1] for c in polygon_coords]
    cx, cy = t2utm.transform(
        sum(poly_lons) / len(poly_lons),
        sum(poly_lats) / len(poly_lats),
    )

    def to_local(lat: float, lon: float) -> tuple[float, float]:
        ex, ny = t2utm.transform(lon, lat)
        return ex - cx, ny - cy

    # Horizontal scale for resistance curves (~15 % of area extent)
    extent_m = max(
        max(poly_lons) - min(poly_lons),
        max(poly_lats) - min(poly_lats),
    ) * 111_000
    res_scale_m = max(extent_m * 0.15, 15.0)

    az_rad = math.radians(graph_azimuth_deg)
    dx_dir = math.sin(az_rad)   # east component in UTM
    dy_dir = math.cos(az_rad)   # north component in UTM

    COLORS = [
        "#1565C0", "#C62828", "#2E7D32", "#6A1B9A",
        "#E65100", "#00838F", "#B45309", "#7C3AED",
    ]

    # ── Terrain Mesh3d ───────────────────────────────────────────────
    if terrain_grid:
        tx, ty, tz_list = [], [], []
        for pt in terrain_grid:
            lx, ly = to_local(pt["lat"], pt["lon"])
            tx.append(lx)
            ty.append(ly)
            tz_list.append(pt["z"])
        pts2d = np.array(list(zip(tx, ty)))
        tri = Delaunay(pts2d)
        fig.add_trace(go.Mesh3d(
            x=tx, y=ty, z=tz_list,
            i=tri.simplices[:, 0].tolist(),
            j=tri.simplices[:, 1].tolist(),
            k=tri.simplices[:, 2].tolist(),
            intensity=tz_list,
            colorscale=[[0, "rgb(90,120,60)"], [0.5, "rgb(140,170,90)"], [1, "rgb(200,190,140)"]],
            showscale=False,
            opacity=0.72,
            name="Terreng",
            hovertemplate="Kote: %{z:.1f} m<extra>Terreng</extra>",
            lighting=dict(ambient=0.8, diffuse=0.5, roughness=0.6),
        ))

    # ── Global max resistance for uniform scaling ──────────────────────
    global_max_c2 = 1.0
    for bh in area_proj_boreholes:
        g = get_graph_data(bh.get("_project", ""), bh.get("point_id", ""))
        if g and g.get("c2"):
            mc2 = max(g["c2"])
            if mc2 > global_max_c2:
                global_max_c2 = mc2

    # ── Project boreholes: sounding curves ───────────────────────────
    for idx, bh in enumerate(area_proj_boreholes):
        bx, by = to_local(bh["lat"], bh["lon"])
        t_z = float(bh.get("elevation", 0.0))
        max_d = float(bh.get("max_depth", 10.0))
        bot_z = t_z - max_d
        pid = bh.get("point_id", f"BH-{idx}")
        proj = bh.get("_project", "")
        color = COLORS[idx % len(COLORS)]
        hx = color.lstrip("#")
        rc, gc_col, bc = int(hx[0:2], 16), int(hx[2:4], 16), int(hx[4:6], 16)

        # Shaft
        fig.add_trace(go.Scatter3d(
            x=[bx, bx], y=[by, by], z=[t_z, bot_z],
            mode="lines",
            line=dict(color=f"rgb({rc},{gc_col},{bc})", width=4),
            showlegend=False,
            hovertemplate=f"<b>{pid}</b><br>Kote: {t_z:.1f} m<br>Dybde: {max_d:.1f} m<extra></extra>",
        ))
        # Top marker + label
        fig.add_trace(go.Scatter3d(
            x=[bx], y=[by], z=[t_z],
            mode="markers+text",
            marker=dict(size=7, color=color, symbol="diamond"),
            text=[pid],
            textposition="top center",
            textfont=dict(size=10, color=color),
            name=pid,
            showlegend=True,
            hovertemplate=(
                f"<b>{pid}</b><br>{bh.get('method_name','')}<br>"
                f"Dybde: {max_d:.1f} m<br>Kote: {t_z:.1f} m<br>"
                f"Dato: {bh.get('date','')}<extra></extra>"
            ),
        ))
        # Bottom marker
        fig.add_trace(go.Scatter3d(
            x=[bx], y=[by], z=[bot_z],
            mode="markers",
            marker=dict(size=4, color="black", symbol="cross"),
            showlegend=False,
            hoverinfo="skip",
        ))

        graph = get_graph_data(proj, pid)
        if not graph or not graph.get("depth") or not graph.get("c2"):
            continue

        depths = list(graph["depth"])
        c2vals = list(graph["c2"])
        n = len(depths)
        elev_list = [t_z - d for d in depths]

        # Resistance curve: lateral offset in azimuth direction
        x_curve = [bx + (c / global_max_c2) * res_scale_m * dx_dir for c in c2vals]
        y_curve = [by + (c / global_max_c2) * res_scale_m * dy_dir for c in c2vals]

        # Resistance trace line
        fig.add_trace(go.Scatter3d(
            x=x_curve, y=y_curve, z=elev_list,
            mode="lines",
            line=dict(color=color, width=2.5),
            showlegend=False,
            customdata=[[f"{c:.0f} kN @ {d:.1f} m"] for c, d in zip(c2vals, depths)],
            hovertemplate="%{customdata[0]}<extra>" + pid + "</extra>",
        ))

        # Filled curtain: Mesh3d strip between shaft-line and resistance curve
        mx = [bx] * n + x_curve
        my = [by] * n + y_curve
        mz = elev_list + elev_list
        i_idx, j_idx, k_idx = [], [], []
        for s in range(n - 1):
            i_idx.append(s);     j_idx.append(s + 1);     k_idx.append(n + s)
            i_idx.append(s + 1); j_idx.append(n + s + 1); k_idx.append(n + s)
        fig.add_trace(go.Mesh3d(
            x=mx, y=my, z=mz,
            i=i_idx, j=j_idx, k=k_idx,
            color=f"rgb({rc},{gc_col},{bc})",
            opacity=0.18,
            showscale=False,
            showlegend=False,
            hoverinfo="skip",
        ))

        # Closing edge (top + bottom connector between shaft and curve tip)
        fig.add_trace(go.Scatter3d(
            x=[bx, x_curve[0]],
            y=[by, y_curve[0]],
            z=[elev_list[0], elev_list[0]],
            mode="lines",
            line=dict(color=f"rgba({rc},{gc_col},{bc},0.4)", width=1),
            showlegend=False, hoverinfo="skip",
        ))
        fig.add_trace(go.Scatter3d(
            x=[bx, x_curve[-1]],
            y=[by, y_curve[-1]],
            z=[elev_list[-1], elev_list[-1]],
            mode="lines",
            line=dict(color=f"rgba({rc},{gc_col},{bc},0.4)", width=1),
            showlegend=False, hoverinfo="skip",
        ))

        # Spyling: thick blue segment on shaft
        for seg_s, seg_e in graph.get("spyling", []):
            fig.add_trace(go.Scatter3d(
                x=[bx, bx], y=[by, by],
                z=[t_z - seg_s, t_z - seg_e],
                mode="lines",
                line=dict(color="#2196F3", width=10),
                showlegend=False,
                hovertemplate=f"Spyling {seg_s:.1f}–{seg_e:.1f} m<extra></extra>",
            ))

        # Slag: thick red segment on shaft
        for seg_s, seg_e in graph.get("slag", []):
            fig.add_trace(go.Scatter3d(
                x=[bx, bx], y=[by, by],
                z=[t_z - seg_s, t_z - seg_e],
                mode="lines",
                line=dict(color="#F44336", width=10),
                showlegend=False,
                hovertemplate=f"Slag {seg_s:.1f}–{seg_e:.1f} m<extra></extra>",
            ))

    # ── NADAG boreholes (shaft + top marker only) ─────────────────────
    if not nadag_area_df.empty:
        n_xs, n_ys, n_zs, n_txt = [], [], [], []
        for _, row in nadag_area_df.iterrows():
            lat = row.get("_lat"); lon = row.get("_lon")
            if lat is None or lon is None:
                continue
            depth = row.get("borlengdeberg")
            depth = float(depth) if isinstance(depth, (int, float)) else 5.0
            elev = row.get("hoeyde")
            elev = float(elev) if isinstance(elev, (int, float)) else 0.0
            nx, ny = to_local(float(lat), float(lon))
            bnr = str(row.get("borenr") or "NADAG")
            fig.add_trace(go.Scatter3d(
                x=[nx, nx], y=[ny, ny], z=[elev, elev - depth],
                mode="lines",
                line=dict(color="rgba(100,100,200,0.55)", width=2),
                showlegend=False,
                hovertemplate=f"<b>{bnr}</b><br>NADAG<br>Dybde: {depth:.1f} m<extra></extra>",
            ))
            n_xs.append(nx); n_ys.append(ny); n_zs.append(elev); n_txt.append(bnr)
        if n_xs:
            fig.add_trace(go.Scatter3d(
                x=n_xs, y=n_ys, z=n_zs,
                mode="markers",
                marker=dict(size=5, color="rgba(100,100,200,0.8)"),
                text=n_txt,
                name="NADAG",
                hovertemplate="<b>%{text}</b><br>NADAG<extra></extra>",
            ))

    # ── Layout ─────────────────────────────────────────────────────
    fig.update_layout(
        scene=dict(
            xaxis_title="Øst (m)",
            yaxis_title="Nord (m)",
            zaxis_title="Kote (m.o.h.)",
            aspectmode="manual",
            aspectratio=dict(x=1, y=1, z=0.4),
            camera=dict(
                eye=dict(x=1.5, y=-1.5, z=0.9),
                up=dict(x=0, y=0, z=1),
            ),
            bgcolor="rgb(235,243,252)",
            xaxis=dict(showbackground=True, backgroundcolor="rgb(220,232,245)"),
            yaxis=dict(showbackground=True, backgroundcolor="rgb(215,227,240)"),
            zaxis=dict(showbackground=True, backgroundcolor="rgb(210,222,235)"),
        ),
        margin=dict(l=0, r=0, t=50, b=0),
        height=720,
        title=dict(
            text="3D Sonderingsvisning – Dra for å rotere | Scroll for å zoome | Klikk for info",
            font=dict(size=13),
        ),
        paper_bgcolor="white",
        legend=dict(
            x=0.01, y=0.99,
            bgcolor="rgba(255,255,255,0.88)",
            bordercolor="#ccc",
            borderwidth=1,
            font=dict(size=11),
        ),
    )
    return fig


def add_project_areas(m: folium.Map, projects_geojson: dict) -> None:
    style = lambda feature: {
        "fillColor": "#5B8FF9",
        "color": "#2953A6",
        "weight": 2,
        "fillOpacity": 0.12,
    }
    highlight = lambda feature: {
        "fillColor": "#FFB703",
        "color": "#8A5A00",
        "weight": 3,
        "fillOpacity": 0.18,
    }
    GeoJson(
        projects_geojson,
        name="Prosjektområder",
        style_function=style,
        highlight_function=highlight,
        tooltip=GeoJsonTooltip(
            fields=["project", "discipline", "year", "archive_id"],
            aliases=["Prosjekt", "Fag", "År", "Arkiv-ID"],
            sticky=False,
        ),
    ).add_to(m)

    fg = folium.FeatureGroup(name="Prosjektinnganger", show=True)
    for feature in projects_geojson["features"]:
        props = feature["properties"]
        lat, lon = polygon_centroid(feature["geometry"]["coordinates"])
        popup_html = f"""
        <div style="font-size:13px; min-width:260px;">
            <div style="font-weight:700;font-size:14px;">{props['project']}</div>
            <div><b>Arkiv-ID:</b> {props['archive_id']}</div>
            <div><b>Fag:</b> {props['discipline']}</div>
            <div><b>År:</b> {props['year']}</div>
            <div><b>Rapporter:</b> {props['report_count']}</div>
            {detail_button_html(detail_url('project', props['archive_id']), 'Åpne prosjektmappe ↗')}
        </div>
        """
        folium.Marker(
            location=[lat, lon],
            popup=folium.Popup(popup_html, max_width=320),
            tooltip=f"Prosjekt: {props['project']}",
            icon=BeautifyIcon(
                icon_shape="marker",
                number="P",
                border_color="#7C3AED",
                background_color="#A78BFA",
                text_color="#FFFFFF",
            ),
        ).add_to(fg)
    fg.add_to(m)


def build_popup_html(row: pd.Series) -> str:
    return f"""
    <div style="font-size: 13px; min-width: 280px;">
        <div style="font-weight:700; font-size:14px;">{row['point_id']}</div>
        <div><b>Prosjekt:</b> {row['project']}</div>
        <div><b>Metode:</b> {row['method']}</div>
        <div><b>Dybde:</b> {row['depth_m']} m</div>
        <div><b>År:</b> {row['year']}</div>
        <div><b>Status:</b> {row['status']}</div>
        <div><b>Arkiv-ID:</b> {row['archive_id']}</div>
        <div><b>Rapport:</b> {row['report_ref']}</div>
        <div style="margin-top:6px;">{row['notes']}</div>
        {detail_button_html(detail_url('point', row['point_id']), 'Åpne boring / prøver ↗')}
    </div>
    """


def add_investigation_points(m: folium.Map, df: pd.DataFrame) -> None:
    cluster = MarkerCluster(name="Undersøkelsespunkter", show=True)
    cluster.add_to(m)
    for _, row in df.iterrows():
        style = METHOD_STYLES.get(row["method"], {"background_color": "#666666", "border_color": "#333333", "text": "?"})
        icon = BeautifyIcon(
            icon_shape="marker",
            number=style["text"],
            border_color=style["border_color"],
            background_color=style["background_color"],
            text_color="#FFFFFF",
        )
        folium.Marker(
            location=[row["lat"], row["lon"]],
            popup=folium.Popup(build_popup_html(row), max_width=360),
            tooltip=f"{row['point_id']} – {row['method']}",
            icon=icon,
        ).add_to(cluster)


def add_report_markers(m: folium.Map, reports_df: pd.DataFrame) -> None:
    fg = folium.FeatureGroup(name="Rapporter / notater", show=False)
    for _, row in reports_df.iterrows():
        popup_html = f"""
        <div style="font-size:13px; min-width:250px;">
            <div style="font-weight:700; font-size:14px;">{row['title']}</div>
            <div><b>Kategori:</b> {row['category']}</div>
            <div><b>År:</b> {row['year']}</div>
            <div><b>Ref:</b> {row['ref']}</div>
            {detail_button_html(detail_url('project', row['archive_id']), 'Åpne prosjekt ↗')}
        </div>
        """
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=7,
            color="#6A1B9A",
            fill=True,
            fill_color="#8E24AA",
            fill_opacity=0.85,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=row["title"],
        ).add_to(fg)
    fg.add_to(m)


def add_wms_layers(m: folium.Map, selected_names: list[str]) -> None:
    for preset in WMS_PRESETS:
        if preset["name"] not in selected_names:
            continue
        folium.raster_layers.WmsTileLayer(
            url=preset["url"],
            name=preset["name"],
            layers=preset["layers"],
            fmt="image/png",
            transparent=True,
            version=preset.get("version", "1.3.0"),
            attr=preset["attr"],
            overlay=True,
            control=True,
            show=True,
        ).add_to(m)


# ---------------------------------------------------------------------------
# NVE Kvikkleire – WFS fetch and map layer
# ---------------------------------------------------------------------------

# Aktsomhetsnivå -> display label + colours
_KVIKK_STYLE: dict[str, dict] = {
    "lav":        {"label": "Lav",        "fill": "#FFF176", "border": "#F9A825"},
    "middels":    {"label": "Middels",    "fill": "#FFB300", "border": "#E65100"},
    "høy":        {"label": "Høy",        "fill": "#EF5350", "border": "#B71C1C"},
    "hoy":        {"label": "Høy",        "fill": "#EF5350", "border": "#B71C1C"},
    "meget høy":  {"label": "Meget høy",  "fill": "#B71C1C", "border": "#7f0000"},
    "meget hoy":  {"label": "Meget høy",  "fill": "#B71C1C", "border": "#7f0000"},
    "farlig":     {"label": "Farlig",     "fill": "#880E4F", "border": "#4a0026"},
}
_KVIKK_DEFAULT = {"label": "Ukjent", "fill": "#FF8F00", "border": "#E65100"}

# NVE ArcGIS REST – layer 1 = Utlopsomrader (faresonekart)
_NVE_KVIKK_URL = (
    "https://gis3.nve.no/arcgis/rest/services/mapservice"
    "/SkredKvikkleireApp_Faktaark/MapServer/1/query"
)


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_nve_quickclay(bbox_wgs84: tuple[float, float, float, float]) -> list[dict]:
    """Fetch NVE kvikkleiresoner via ArcGIS REST for the given bbox (min_lon, min_lat, max_lon, max_lat).
    Returns GeoJSON features list.
    """
    min_lon, min_lat, max_lon, max_lat = bbox_wgs84
    buf = 0.05
    min_lon -= buf; min_lat -= buf; max_lon += buf; max_lat += buf
    params = {
        "f": "geojson",
        "geometry": f"{min_lon},{min_lat},{max_lon},{max_lat}",
        "geometryType": "esriGeometryEnvelope",
        "inSR": "4326",
        "spatialRel": "esriSpatialRelIntersects",
        "outFields": "faregrad,skredOmrNavn,kommune,risiko,areal_km2,rapportURL",
        "outSR": "4326",
        "returnGeometry": "true",
        "resultRecordCount": "500",
    }
    url = _NVE_KVIKK_URL + "?" + urlencode(params)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "GeoArc/1.0"})
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read())
        return data.get("features", [])
    except Exception:
        return []


def add_quickclay_layer(m: folium.Map) -> int:
    """Add NVE kvikkleire polygons to the map. Returns number of zones added.
    Uses a fixed Norway-wide bbox – results are cached for 1 hour.
    """
    # Fixed bbox covering mainland Norway – cached so no re-fetch on every rerun
    bbox: tuple[float, float, float, float] = (4.0, 57.5, 32.0, 71.5)

    features = fetch_nve_quickclay(bbox)
    if not features:
        return 0

    fg = folium.FeatureGroup(name="🟥 NVE Kvikkleiresoner", show=True)
    count = 0

    for feat in features:
        props = feat.get("properties") or {}
        geom  = feat.get("geometry") or {}
        geom_type = geom.get("type", "")
        coords = geom.get("coordinates")
        if not coords:
            continue

        raw = str(props.get("faregrad") or "").strip().lower()
        style = _KVIKK_STYLE.get(raw, _KVIKK_DEFAULT)

        sonenavn    = props.get("skredOmrNavn") or "–"
        kommunenavn = props.get("kommune") or "–"
        areal_km2   = props.get("areal_km2")
        areal_txt   = f"{float(areal_km2) * 100:.1f} daa" if areal_km2 else "–"
        rapport_url = props.get("rapportURL") or ""

        tooltip_html = (
            f"<b>&#128997; Kvikkleiresone</b><br/>"
            f"<b>Navn:</b> {sonenavn}<br/>"
            f"<b>Faregrad:</b> <b>{style['label']}</b><br/>"
            f"<b>Kommune:</b> {kommunenavn}"
        )
        popup_html = (
            f'<div style="font-size:13px;min-width:220px;">'
            f'<b style="color:{style["border"]};">&#128997; Kvikkleiresone</b><br/>'
            f'<b>Navn:</b> {sonenavn}<br/>'
            f'<b>Faregrad:</b> <span style="color:{style["border"]};font-weight:700;">'
            f'{style["label"]}</span><br/>'
            f'<b>Kommune:</b> {kommunenavn}<br/>'
            f'<b>Areal:</b> {areal_txt}'
        )
        if rapport_url:
            popup_html += f'<br/><a href="https://{rapport_url}" target="_blank">&#128196; Rapport</a>'
        popup_html += '</div>'

        def _ring_locs(ring: list) -> list[list[float]]:
            return [[pt[1], pt[0]] for pt in ring]

        try:
            rings: list[list] = []
            if geom_type == "Polygon":
                rings = [_ring_locs(coords[0])]
            elif geom_type == "MultiPolygon":
                rings = [_ring_locs(poly[0]) for poly in coords]
            else:
                continue

            for ring_locs in rings:
                folium.Polygon(
                    locations=ring_locs,
                    color=style["border"],
                    weight=1.5,
                    fill=True,
                    fill_color=style["fill"],
                    fill_opacity=0.45,
                    tooltip=folium.Tooltip(tooltip_html, sticky=True),
                    popup=folium.Popup(popup_html, max_width=280),
                ).add_to(fg)
            count += 1
        except Exception:
            continue

    fg.add_to(m)
    return count


def add_custom_wms(m: folium.Map, enabled: bool, url: str, layers: str, layer_name: str, version: str, fmt: str) -> None:
    if not enabled or not url or not layers:
        return
    folium.raster_layers.WmsTileLayer(
        url=url.strip(),
        name=layer_name.strip() or "Egendefinert WMS",
        layers=layers.strip(),
        fmt=fmt,
        transparent=True,
        version=version,
        attr="Custom WMS",
        overlay=True,
        control=True,
        show=True,
    ).add_to(m)


def add_loaded_projects(m: folium.Map, loaded_projects: dict) -> None:
    """Add uploaded SND project boreholes and polygon outlines to the map."""
    for proj_name, proj in loaded_projects.items():
        fg = folium.FeatureGroup(name=f"Prosjekt: {proj_name}", show=True)

        # Draw project polygon outline (like example projects)
        polygon = proj.get("polygon", [])
        if len(polygon) >= 3:
            folium.Polygon(
                locations=polygon,  # list of (lat, lon)
                color="#E63946",
                weight=2,
                fill=True,
                fill_color="#E63946",
                fill_opacity=0.10,
                tooltip=f"Prosjekt: {proj_name}",
            ).add_to(fg)

        for bh in proj["boreholes"]:
            popup_html = (
                f'<div class="project-borehole" data-project="{proj_name}" data-point="{bh["point_id"]}"'
                f' style="font-size:13px;min-width:220px;">'
                f'<div style="font-weight:700;font-size:14px;">{bh["point_id"]}</div>'
                f'<div><b>Prosjekt:</b> {proj_name}</div>'
                f'<div><b>Metode:</b> {bh.get("method_name", "Ukjent")}</div>'
                f'<div><b>Dybde:</b> {bh["max_depth"]:.1f} m</div>'
                f'<div><b>Terrengkvote:</b> {bh["elevation"]:.1f} m</div>'
                f'<div><b>Dato:</b> {bh.get("date", "–")}</div>'
                f'</div>'
            )
            folium.CircleMarker(
                location=[bh["lat"], bh["lon"]],
                radius=8,
                color="#E63946",
                fill=True,
                fill_color="#E63946",
                fill_opacity=0.85,
                popup=folium.Popup(popup_html, max_width=280),
                tooltip=f"{bh['point_id']} – {bh.get('method_name', '')}",
            ).add_to(fg)
        fg.add_to(m)

def add_legend() -> str:
    rows = []
    for method, style in METHOD_STYLES.items():
        rows.append(
            f"""
            <div style='display:flex;align-items:center;margin-bottom:6px;'>
                <div style='width:18px;height:18px;border-radius:50%;background:{style["background_color"]};border:2px solid {style["border_color"]};margin-right:8px;'></div>
                <span style='font-size:12px;'>{method}</span>
            </div>
            """
        )
    return f"""
    <div style="position: fixed; bottom: 20px; left: 20px; z-index: 9999; background: white; padding: 12px 14px; border: 1px solid #d9d9d9; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.15);">
        <div style="font-weight:700; margin-bottom:8px;">Tegnforklaring</div>
        {''.join(rows)}
    </div>
    """


def parse_clicked_point_id(popup_html: str | None) -> str | None:
    if not popup_html:
        return None
    match = re.search(r'<div style="font-weight:700; font-size:14px;">([^<]+)</div>', popup_html)
    return match.group(1).strip() if match else None


def _parse_project_borehole_click(popup_html: str | None, loaded_projects: dict) -> tuple[str, dict] | None:
    """Detect if a project borehole was clicked. Returns (project_name, borehole_dict) or None."""
    if not popup_html or "project-borehole" not in popup_html:
        return None
    m_proj = re.search(r'data-project="([^"]+)"', popup_html)
    m_point = re.search(r'data-point="([^"]+)"', popup_html)
    if not m_proj or not m_point:
        return None
    proj_name = m_proj.group(1)
    point_id = m_point.group(1)
    proj = loaded_projects.get(proj_name)
    if not proj:
        return None
    for bh in proj["boreholes"]:
        if bh["point_id"] == point_id:
            return proj_name, bh
    return None


def _find_project_borehole_by_coords(
    lat: float, lon: float, loaded_projects: dict, tol: float = 0.0001
) -> tuple[str, dict] | None:
    """Find a loaded project borehole near the given coordinates."""
    for proj_name, proj in loaded_projects.items():
        for bh in proj["boreholes"]:
            if abs(bh["lat"] - lat) < tol and abs(bh["lon"] - lon) < tol:
                return proj_name, bh
    return None


def build_sounding_image(bh: dict, project_name: str = "") -> io.BytesIO | None:
    """Build a matplotlib sounding chart (GeoTolk-style). Returns PNG BytesIO or None."""
    graph = get_graph_data(project_name, bh.get("point_id", ""))
    if not graph or not graph.get("depth") or not graph.get("c2"):
        return None

    depths = list(graph["depth"])
    c2vals = list(graph["c2"])
    max_depth = max(depths) if depths else bh.get("max_depth", 10)
    max_x = max(c2vals) if c2vals else 1000
    if max_x <= 0:
        max_x = 1000

    fig, ax = plt.subplots(figsize=(5, 8))

    # Downsample if too many points
    if len(depths) > 500:
        s = len(depths) // 500
        depths, c2vals = depths[::s], c2vals[::s]

    # Main resistance trace
    ax.plot(c2vals, depths, "k-", linewidth=1.5, zorder=2)

    # Spyling segments (blue)
    for s_d, e_d in graph.get("spyling", []):
        ax.barh(
            [(s_d + e_d) / 2], [max_x * 0.05], left=0,
            height=e_d - s_d, alpha=0.5, color="blue", zorder=2,
        )

    # Slag segments (red)
    for s_d, e_d in graph.get("slag", []):
        ax.barh(
            [(s_d + e_d) / 2], [max_x * 0.05], left=max_x * 0.05,
            height=e_d - s_d, alpha=0.5, color="red", zorder=2,
        )

    ax.set_xlabel("Motstand (kN)", fontsize=10)
    ax.set_ylabel("Dybde (m)", fontsize=10)
    ax.set_xlim(0, max_x)
    ax.set_ylim(max_depth, 0)
    ax.grid(True, alpha=0.3, linestyle=":")
    ax.set_title(f"{bh['point_id']} \u2013 {bh.get('method_name', '')}", fontsize=11)
    plt.tight_layout(pad=0.5)

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=110, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf


def _parse_project_marker_click(popup_html: str | None, loaded_projects: dict) -> str | None:
    """Detect if a project centroid marker was clicked. Returns project_name or None."""
    if not popup_html or "proj-marker" not in popup_html:
        return None
    # Don't match borehole popups
    if "project-borehole" in popup_html:
        return None
    m = re.search(r'data-projname="([^"]+)"', popup_html)
    if not m:
        return None
    proj_name = m.group(1)
    return proj_name if proj_name in loaded_projects else None


def _open_folder(folder_path: str) -> None:
    """Open a folder in the OS file explorer."""
    try:
        p = Path(folder_path)
        if p.is_dir():
            subprocess.Popen(["explorer", str(p)])
    except Exception:
        pass


def build_map(points_df: pd.DataFrame, reports_df: pd.DataFrame, projects_geojson: dict, selected_wms: list[str], enable_custom_wms: bool, custom_wms_url: str, custom_wms_layers: str, custom_wms_name: str, custom_wms_version: str, custom_wms_format: str, loaded_projects: dict | None = None, show_quickclay: bool = False) -> folium.Map:
    center = [59.9139, 10.7522]
    zoom = 11

    # If loaded projects exist, fit map to show their boreholes
    if loaded_projects:
        all_lats = []
        all_lons = []
        for proj in loaded_projects.values():
            for bh in proj.get("boreholes", []):
                lat, lon = bh.get("lat"), bh.get("lon")
                if lat is not None and lon is not None and math.isfinite(lat) and math.isfinite(lon):
                    all_lats.append(lat)
                    all_lons.append(lon)
        if all_lats:
            center = [sum(all_lats) / len(all_lats), sum(all_lons) / len(all_lons)]
            zoom = 12

    m = folium.Map(location=center, zoom_start=zoom, control_scale=True, tiles=None)
    add_base_maps(m)
    add_project_areas(m, projects_geojson)
    add_investigation_points(m, points_df)
    add_report_markers(m, reports_df)
    if loaded_projects:
        add_loaded_projects(m, loaded_projects)
    add_wms_layers(m, selected_wms)
    add_custom_wms(m, enable_custom_wms, custom_wms_url, custom_wms_layers, custom_wms_name, custom_wms_version, custom_wms_format)
    if show_quickclay:
        add_quickclay_layer(m)
    Draw(
        draw_options={
            "polyline": {
                "shapeOptions": {
                    "color": "#ff7800",
                    "weight": 3,
                    "opacity": 0.8,
                },
            },
            "rectangle": True,
            "circle": False,
            "circlemarker": False,
            "marker": False,
            "polygon": {
                "allowIntersection": False,
                "shapeOptions": {
                    "color": "#e63946",
                    "weight": 3,
                    "fillOpacity": 0.15,
                },
            },
        },
        edit_options={"edit": True, "remove": True},
    ).add_to(m)
    # Fit bounds if we have loaded project boreholes
    if loaded_projects:
        all_coords = []
        for proj in loaded_projects.values():
            for bh in proj.get("boreholes", []):
                lat, lon = bh.get("lat"), bh.get("lon")
                if lat is not None and lon is not None and math.isfinite(lat) and math.isfinite(lon):
                    all_coords.append([lat, lon])
        if all_coords:
            m.fit_bounds(all_coords, padding=[30, 30])

    MiniMap(toggle_display=True).add_to(m)
    Fullscreen(position="topright").add_to(m)
    MousePosition(position="bottomright", prefix="Koordinat").add_to(m)
    m.get_root().html.add_child(folium.Element(add_legend()))
    return m


def find_project_by_archive(project_meta: pd.DataFrame, archive_id: str) -> pd.Series | None:
    hit = project_meta.loc[project_meta["archive_id"] == archive_id]
    return hit.iloc[0] if not hit.empty else None


def show_document_block(documents: pd.DataFrame) -> None:
    if documents.empty:
        st.info("Ingen eksempel-dokumenter knyttet til dette objektet.")
        return
    for _, doc in documents.iterrows():
        path = BASE_DIR / doc["file_path"]
        with st.container(border=True):
            st.markdown(f"**{doc['title']}**")
            st.caption(f"{doc['doc_type']} · {doc['year']}")
            st.write(doc["description"])
            if path.exists():
                if path.suffix.lower() in {".md", ".txt"}:
                    st.code(path.read_text(encoding="utf-8"), language="markdown")
                st.download_button(
                    f"Last ned {path.name}",
                    data=path.read_bytes(),
                    file_name=path.name,
                    mime="text/plain" if path.suffix.lower() in {".md", ".txt", ".csv"} else "application/octet-stream",
                    key=f"download-{doc['scope_type']}-{doc['scope_id']}-{path.name}",
                )


def render_detail_page(points_df: pd.DataFrame, project_meta: pd.DataFrame, lab_df: pd.DataFrame, docs_df: pd.DataFrame) -> None:
    st.set_page_config(page_title="GeoArkiv detaljside", page_icon="📁", layout="wide")
    st.title("📁 GeoArkiv detaljside")
    qp = st.query_params
    kind = qp.get("kind", "point")
    item_id = qp.get("id", "")
    if not item_id:
        st.error("Fant ikke objekt-ID i URL-en.")
        if st.button("Tilbake til kart"):
            st.query_params.clear()
            st.rerun()
        return
    cols = st.columns([1, 5])
    with cols[0]:
        if st.button("← Tilbake til kart"):
            st.query_params.clear()
            st.rerun()
    if kind == "point":
        hit = points_df.loc[points_df["point_id"] == item_id]
        if hit.empty:
            st.error(f"Fant ikke boring/prøve med ID {item_id}.")
            return
        row = hit.iloc[0]
        project = find_project_by_archive(project_meta, row["archive_id"])
        st.subheader(f"{row['point_id']} · {row['method']}")
        st.caption(f"Prosjekt: {row['project']} · Arkiv-ID: {row['archive_id']}")
        left, right = st.columns([2, 1])
        with left:
            st.write(row["notes"])
            st.dataframe(pd.DataFrame([row]).drop(columns=["notes"]), use_container_width=True, hide_index=True)
        with right:
            st.metric("Dybde", f"{row['depth_m']} m")
            st.metric("År", int(row["year"]))
            st.metric("Status", row["status"])
        tab1, tab2, tab3 = st.tabs(["Labdata", "Dokumenter", "Prosjektkontekst"])
        with tab1:
            point_lab = lab_df.loc[lab_df["point_id"] == row["point_id"]]
            if point_lab.empty:
                st.info("Ingen labresultater for dette punktet i eksempeldataene.")
            else:
                st.dataframe(point_lab, use_container_width=True, hide_index=True)
        with tab2:
            point_docs = docs_df.loc[(docs_df["scope_type"] == "point") & (docs_df["scope_id"] == row["point_id"])]
            show_document_block(point_docs)
        with tab3:
            if project is not None:
                st.write(project["summary"])
                project_points = points_df.loc[points_df["archive_id"] == row["archive_id"], ["point_id", "method", "depth_m", "year", "status"]]
                st.dataframe(project_points, use_container_width=True, hide_index=True)
                project_docs = docs_df.loc[(docs_df["scope_type"] == "project") & (docs_df["scope_id"] == row["archive_id"])]
                st.markdown("**Prosjektdokumenter**")
                show_document_block(project_docs)
    else:
        project = find_project_by_archive(project_meta, item_id)
        if project is None:
            st.error(f"Fant ikke prosjekt med arkiv-ID {item_id}.")
            return
        st.subheader(f"{project['project']}")
        st.caption(f"Arkiv-ID: {project['archive_id']} · Fag: {project['discipline']} · Kunde: {project['client']}")
        st.write(project["summary"])
        p1, p2, p3 = st.columns(3)
        p1.metric("År", int(project["year"]))
        p2.metric("Rapporter", int(project["report_count"]))
        p3.metric("Punkter", int((points_df["archive_id"] == item_id).sum()))
        tab1, tab2, tab3, tab4 = st.tabs(["Punkter", "Labdata", "Rapporter og filer", "Råmetadata"])
        with tab1:
            project_points = points_df.loc[points_df["archive_id"] == item_id]
            st.dataframe(project_points, use_container_width=True, hide_index=True)
        with tab2:
            project_lab = lab_df.loc[lab_df["archive_id"] == item_id]
            if project_lab.empty:
                st.info("Ingen labresultater for dette prosjektet i eksempeldataene.")
            else:
                st.dataframe(project_lab, use_container_width=True, hide_index=True)
        with tab3:
            project_docs = docs_df.loc[(docs_df["scope_type"] == "project") & (docs_df["scope_id"] == item_id)]
            show_document_block(project_docs)
        with tab4:
            st.json(project.to_dict())


def render_map_page(points_df: pd.DataFrame, reports_df: pd.DataFrame, projects_geojson: dict,
                    lab_df: pd.DataFrame, project_meta: pd.DataFrame) -> None:
    st.set_page_config(page_title="Oslo GeoArkiv MVP v3", page_icon="🗺️", layout="wide")
    st.title("🗺️ Oslo GeoArkiv MVP v3")

    # --- Topp-faner ---
    tab_kart, tab_prosjekter, tab_legg_til, tab_test2 = st.tabs(["🗺️ Kart", "📁 Prosjekter", "📂 Legg til prosjekter", "Test 2"])

    with tab_prosjekter:
        st.info("Prosjektoversikt kommer her.")

    # ---------------------------------------------------------------
    # Tab: Legg til prosjekter (upload folder with SND files)
    # ---------------------------------------------------------------
    with tab_legg_til:
        if "loaded_projects" not in st.session_state:
            st.session_state["loaded_projects"] = {}

        add_src = st.radio(
            "Kilde",
            ["📁 Fra lokal mappe", "☁️ Fra FieldManager"],
            horizontal=True,
            label_visibility="collapsed",
        )

        # ── Lokal mappe ───────────────────────────────────────────────
        if add_src == "📁 Fra lokal mappe":
            st.subheader("Legg til prosjekt fra mappe")
            st.caption("Velg prosjektmappe (inneholder AUTOGRAF.DBF/ med .SND-filer), eller lim inn stien direkte til AUTOGRAF-mappen.")

            ltp_col1, ltp_col2 = st.columns([3, 1])
            with ltp_col1:
                folder_path = st.text_input(
                    "Mappesti",
                    placeholder=r"C:\Prosjekter\MittProsjekt",
                    help="Sti til prosjektmappen (med AUTOGRAF.DBF/ undermappe) eller direkte til AUTOGRAF-mappen. Mappenavnet blir prosjektnavnet.",
                )
            with ltp_col2:
                crs_labels = ["Auto-detekter (Info.prj)"] + list(CRS_OPTIONS.keys())
                source_crs_label = st.selectbox("Koordinatsystem", crs_labels, index=0)
                if source_crs_label == "Auto-detekter (Info.prj)":
                    source_epsg = 0  # signal to auto-detect
                else:
                    source_epsg = CRS_OPTIONS[source_crs_label]

            if st.button("📥 Last inn prosjekt", type="primary", disabled=not folder_path):
                actual_epsg = source_epsg
                # If auto-detect, try to find EPSG from project files first
                if actual_epsg == 0:
                    detected = _detect_epsg_from_project(Path(folder_path.strip()))
                    if detected:
                        actual_epsg = detected
                    else:
                        st.error("Kunne ikke auto-detektere koordinatsystem. Velg manuelt fra nedtrekksmenyen.")
                        actual_epsg = 0
                if actual_epsg != 0:
                    with st.spinner("Leser SND-filer..."):
                        result = load_snd_project(folder_path.strip(), actual_epsg)
                    if result is None:
                        st.error("Kunne ikke laste prosjektet. Sjekk at:\n- Mappen finnes\n- Den inneholder en AUTOGRAF.DBF/ (eller AUTOGRAF.BDF/) undermappe med .SND-filer\n- Eller at du limer inn stien direkte til AUTOGRAF-mappen")
                    else:
                        st.session_state["loaded_projects"][result["project_name"]] = result
                        crs_info = _EPSG_TO_LABEL.get(result["epsg"], f"EPSG:{result['epsg']}")
                        detected_note = " (auto-detektert)" if result.get("detected_epsg") else ""
                        st.success(f"Lastet **{result['project_name']}** med {len(result['boreholes'])} borringer. CRS: {crs_info}{detected_note}")
                        if result.get("errors"):
                            with st.expander(f"⚠️ {len(result['errors'])} filer med feil"):
                                for err in result["errors"]:
                                    st.text(err)

        # ── FieldManager ──────────────────────────────────────────────
        else:
            st.subheader("Importer fra FieldManager")
            st.caption("Koble til FieldManager API, velg prosjekt – alle lokasjoner lastes ned og importeres automatisk.")

            fm_token = st.text_input(
                "API Bearer Token",
                type="password",
                help="Lim inn din FieldManager API bearer-token.",
                key="fm_token_input",
            )

            # Step 1: Fetch projects
            if st.button("🔗 Hent prosjekter", type="primary", disabled=not fm_token, key="fm_fetch_projects_btn"):
                try:
                    with st.spinner("Henter prosjektliste fra FieldManager..."):
                        sess = _fm_session(fm_token.strip())
                        projects = _fm_get_projects(sess)
                    st.session_state["fm_projects"] = projects
                    st.session_state["fm_token"] = fm_token.strip()
                    st.success(f"Fant {len(projects)} prosjekter.")
                except PermissionError:
                    st.error("Ugyldig eller utgått token. Sjekk at tokenet er korrekt.")
                except Exception as e:
                    st.error(f"Feil ved henting av prosjekter: {e}")

            fm_projects = st.session_state.get("fm_projects", [])
            if fm_projects:
                proj_labels = [
                    f"{p.get('name', 'Ukjent')} ({p.get('external_id', '') or p.get('project_id', '')[:8]})"
                    for p in fm_projects
                ]
                sel_proj_idx = st.selectbox(
                    "Velg prosjekt",
                    range(len(proj_labels)),
                    format_func=lambda i: proj_labels[i],
                    key="fm_project_select",
                )
                sel_fm_proj = fm_projects[sel_proj_idx]

                fm_col1, fm_col2 = st.columns([1, 1])
                with fm_col1:
                    fm_swap_xy = st.checkbox("Bytt X/Y-koordinater", value=False, key="fm_swap_xy")
                with fm_col2:
                    fm_crs_labels = ["Auto (fra SRID)"] + list(CRS_OPTIONS.keys())
                    fm_crs_sel = st.selectbox("Koordinatsystem", fm_crs_labels, index=0, key="fm_crs_select")

                # Step 2: Fetch all locations, download all, import
                if st.button("📥 Importer alle lokasjoner", type="primary", key="fm_import_all_btn"):
                    try:
                        sess = _fm_session(st.session_state.get("fm_token", ""))
                        project_id = sel_fm_proj["project_id"]
                        proj_name_raw = sel_fm_proj.get("name", "FM")
                        proj_name = re.sub(r'[^\w\s\-.]', '', proj_name_raw).strip() or "FM_import"

                        # 2a: Fetch locations
                        with st.spinner("Henter lokasjoner..."):
                            locations = _fm_get_locations(sess, project_id)

                        if not locations:
                            st.warning("Ingen lokasjoner funnet i dette prosjektet.")
                        else:
                            # Determine EPSG from first location's SRID (or manual)
                            if fm_crs_sel == "Auto (fra SRID)":
                                srid = locations[0].get("srid")
                                if srid and str(srid).isdigit():
                                    fm_epsg = int(srid)
                                else:
                                    st.error(f"Kunne ikke tolke SRID '{srid}'. Velg koordinatsystem manuelt.")
                                    fm_epsg = 0
                            else:
                                fm_epsg = CRS_OPTIONS[fm_crs_sel]

                            if fm_epsg != 0:
                                # 2b: Download all location exports and merge
                                all_boreholes: list[dict] = []
                                all_errors: list[str] = []
                                progress_bar = st.progress(0, text="Laster ned lokasjoner...")
                                for i, loc in enumerate(locations):
                                    loc_name = loc.get("name", "?")
                                    progress_bar.progress(
                                        (i + 1) / len(locations),
                                        text=f"Laster ned {loc_name} ({i+1}/{len(locations)})...",
                                    )
                                    try:
                                        zip_bytes = _fm_export_snd_zip(
                                            sess, project_id, loc["location_id"],
                                            swap_x_y=fm_swap_xy,
                                        )
                                        result = load_snd_from_zip(zip_bytes, fm_epsg, proj_name)
                                        if result:
                                            all_boreholes.extend(result["boreholes"])
                                            all_errors.extend(result.get("errors", []))
                                        else:
                                            all_errors.append(f"{loc_name}: Ingen SND-filer i ZIP")
                                    except Exception as e:
                                        all_errors.append(f"{loc_name}: {e}")

                                progress_bar.empty()

                                if not all_boreholes:
                                    st.error("Ingen borringer ble importert fra noen lokasjoner.")
                                else:
                                    # Build combined project
                                    coords = [(bh["lat"], bh["lon"]) for bh in all_boreholes]
                                    if len(coords) >= 3:
                                        hull = _hull_with_buffer(coords)
                                        polygon = hull + [hull[0]]
                                    else:
                                        polygon = coords

                                    combined = {
                                        "project_name": proj_name,
                                        "folder_path": f"FieldManager: {proj_name_raw}",
                                        "epsg": fm_epsg,
                                        "detected_epsg": None,
                                        "boreholes": all_boreholes,
                                        "polygon": polygon,
                                        "errors": all_errors,
                                    }
                                    st.session_state["loaded_projects"][proj_name] = combined
                                    crs_info = _EPSG_TO_LABEL.get(fm_epsg, f"EPSG:{fm_epsg}")
                                    st.success(
                                        f"Importert **{proj_name}** – "
                                        f"{len(all_boreholes)} borringer fra "
                                        f"{len(locations)} lokasjoner. CRS: {crs_info}"
                                    )
                                    if all_errors:
                                        with st.expander(f"⚠️ {len(all_errors)} feil"):
                                            for err in all_errors:
                                                st.text(err)
                    except PermissionError:
                        st.error("Ugyldig eller utgått token.")
                    except Exception as e:
                        st.error(f"Feil ved import fra FieldManager: {e}")

        # Show loaded projects (shared between both sources)
        loaded_projects = st.session_state.get("loaded_projects", {})
        if loaded_projects:
            st.markdown("---")
            st.subheader("Innlastede prosjekter")
            for pname, pdata in loaded_projects.items():
                with st.container(border=True):
                    pc1, pc2, pc3 = st.columns([3, 1, 1])
                    pc1.markdown(f"**{pname}**")
                    epsg_label = _EPSG_TO_LABEL.get(pdata['epsg'], f"EPSG:{pdata['epsg']}")
                    pc1.caption(f"{len(pdata['boreholes'])} borringer · {epsg_label}")
                    pc2.caption(pdata["folder_path"])
                    if pc3.button("🗑️ Fjern", key=f"rm_proj_{pname}"):
                        del st.session_state["loaded_projects"][pname]
                        st.rerun()
                    # Show borehole table
                    bh_rows = [{
                        "Punkt-ID": bh["point_id"],
                        "Metode": bh.get("method_name", ""),
                        "Dybde (m)": round(bh["max_depth"], 1),
                        "Terrengkvote": round(bh["elevation"], 1),
                        "Lat": round(bh["lat"], 6),
                        "Lon": round(bh["lon"], 6),
                        "Dato": bh.get("date", ""),
                    } for bh in pdata["boreholes"]]
                    st.dataframe(pd.DataFrame(bh_rows), use_container_width=True, hide_index=True)
        else:
            st.info("Ingen prosjekter lastet ennå.")

    with tab_test2:
        st.subheader("Test: Last inn testdata")
        if st.button("🧪 Last inn testprosjekt 1350054497"):
            test_bh = [
                {"point_id": "1", "lat": 64.392065, "lon": 11.401163, "max_depth": 30.4, "elevation": 20.6, "method_name": "Totalsondering", "date": "18.04.2023"},
                {"point_id": "10", "lat": 64.401842, "lon": 11.426962, "max_depth": 10.1, "elevation": 43.8, "method_name": "Totalsondering", "date": "25.04.2023"},
                {"point_id": "11", "lat": 64.403878, "lon": 11.436043, "max_depth": 7.6, "elevation": 41.5, "method_name": "Totalsondering", "date": "03.05.2023"},
                {"point_id": "12", "lat": 64.404583, "lon": 11.440239, "max_depth": 9.8, "elevation": 47.3, "method_name": "Totalsondering", "date": "25.04.2023"},
                {"point_id": "13", "lat": 64.405477, "lon": 11.45242, "max_depth": 12.2, "elevation": 60.2, "method_name": "Totalsondering", "date": "25.04.2023"},
                {"point_id": "14", "lat": 64.405663, "lon": 11.457447, "max_depth": 27.2, "elevation": 57.1, "method_name": "Totalsondering", "date": "27.04.2023"},
                {"point_id": "15", "lat": 64.405566, "lon": 11.457899, "max_depth": 19.6, "elevation": 53.9, "method_name": "Totalsondering", "date": "27.04.2023"},
                {"point_id": "17", "lat": 64.405627, "lon": 11.461057, "max_depth": 6.9, "elevation": 51.4, "method_name": "Totalsondering", "date": "03.05.2023"},
                {"point_id": "19", "lat": 64.405476, "lon": 11.466075, "max_depth": 13.6, "elevation": 48.4, "method_name": "Totalsondering", "date": "02.05.2023"},
                {"point_id": "2", "lat": 64.392088, "lon": 11.400891, "max_depth": 24.4, "elevation": 17.2, "method_name": "Totalsondering", "date": "03.05.2023"},
                {"point_id": "20", "lat": 64.406587, "lon": 11.470286, "max_depth": 24.9, "elevation": 48.5, "method_name": "Totalsondering", "date": "27.04.2023"},
                {"point_id": "21", "lat": 64.406327, "lon": 11.470114, "max_depth": 23.3, "elevation": 41.6, "method_name": "Totalsondering", "date": "02.05.2023"},
                {"point_id": "22", "lat": 64.407787, "lon": 11.47482, "max_depth": 3.9, "elevation": 67.7, "method_name": "Totalsondering", "date": "19.04.2023"},
                {"point_id": "23", "lat": 64.408992, "lon": 11.478087, "max_depth": 15.2, "elevation": 61.6, "method_name": "Totalsondering", "date": "18.04.2023"},
                {"point_id": "24", "lat": 64.407931, "lon": 11.474553, "max_depth": 6.3, "elevation": 64.7, "method_name": "Totalsondering", "date": "27.04.2023"},
                {"point_id": "25", "lat": 64.392853, "lon": 11.402867, "max_depth": 29.5, "elevation": 21.0, "method_name": "Totalsondering", "date": "23.05.2023"},
                {"point_id": "3", "lat": 64.393128, "lon": 11.401686, "max_depth": 29.8, "elevation": 16.6, "method_name": "Totalsondering", "date": "03.05.2023"},
                {"point_id": "4", "lat": 64.393865, "lon": 11.402239, "max_depth": 8.8, "elevation": 14.3, "method_name": "Totalsondering", "date": "24.04.2023"},
                {"point_id": "5", "lat": 64.395961, "lon": 11.403797, "max_depth": 23.1, "elevation": 14.0, "method_name": "Totalsondering", "date": "24.04.2023"},
                {"point_id": "6", "lat": 64.397271, "lon": 11.405459, "max_depth": 19.3, "elevation": 15.1, "method_name": "Totalsondering", "date": "24.04.2023"},
                {"point_id": "8", "lat": 64.400109, "lon": 11.414408, "max_depth": 8.1, "elevation": 37.1, "method_name": "Totalsondering", "date": "25.04.2023"},
                {"point_id": "9", "lat": 64.400486, "lon": 11.419471, "max_depth": 12.0, "elevation": 36.8, "method_name": "Totalsondering", "date": "25.04.2023"},
                {"point_id": "NO20-1", "lat": 64.392818, "lon": 11.399157, "max_depth": 22.6, "elevation": 11.9, "method_name": "Totalsondering", "date": "07.09.2020"},
                {"point_id": "NO20-10", "lat": 64.39819, "lon": 11.405935, "max_depth": 7.5, "elevation": 11.4, "method_name": "Totalsondering", "date": "10.09.2020"},
                {"point_id": "NO20-2", "lat": 64.393316, "lon": 11.400701, "max_depth": 25.2, "elevation": 10.2, "method_name": "Totalsondering", "date": "07.09.2020"},
                {"point_id": "NO20-3", "lat": 64.39374, "lon": 11.400248, "max_depth": 47.0, "elevation": 7.0, "method_name": "Totalsondering", "date": "07.09.2020"},
                {"point_id": "NO20-4", "lat": 64.393685, "lon": 11.40159, "max_depth": 38.5, "elevation": 10.2, "method_name": "Totalsondering", "date": "06.09.2020"},
                {"point_id": "NO20-5", "lat": 64.394659, "lon": 11.402301, "max_depth": 9.0, "elevation": 14.5, "method_name": "Totalsondering", "date": "06.09.2020"},
                {"point_id": "NO20-6", "lat": 64.395179, "lon": 11.402602, "max_depth": 3.7, "elevation": 14.7, "method_name": "Totalsondering", "date": "06.09.2020"},
                {"point_id": "NO20-7", "lat": 64.396058, "lon": 11.403451, "max_depth": 16.7, "elevation": 14.8, "method_name": "Totalsondering", "date": "05.09.2020"},
                {"point_id": "NO20-8", "lat": 64.39723, "lon": 11.404871, "max_depth": 19.4, "elevation": 14.4, "method_name": "Totalsondering", "date": "05.09.2020"},
                {"point_id": "NO20-9", "lat": 64.397722, "lon": 11.405225, "max_depth": 13.6, "elevation": 14.9, "method_name": "Totalsondering", "date": "05.09.2020"},
            ]
            coords = [(bh["lat"], bh["lon"]) for bh in test_bh]
            hull = _hull_with_buffer(coords)
            polygon = hull + [hull[0]]
            st.session_state["loaded_projects"]["1350054497"] = {
                "project_name": "1350054497",
                "folder_path": r"C:\Users\TBLM\Downloads\OneDrive_1_3-26-2026\1350054497",
                "epsg": 5111,
                "detected_epsg": 5111,
                "boreholes": test_bh,
                "polygon": polygon,
                "errors": [],
            }
            st.success("Testprosjekt 1350054497 lastet med 32 borringer!")
            st.rerun()

    with tab_kart:
        # --- Sidebar ---
        st.sidebar.header("Filtrering")
        methods = sorted(points_df["method"].unique().tolist())
        year_range = st.sidebar.slider("År", int(points_df["year"].min()), int(points_df["year"].max()), (int(points_df["year"].min()), int(points_df["year"].max())))
        selected_methods = st.sidebar.multiselect("Metoder", methods, default=methods)
        show_reports = st.sidebar.checkbox("Vis rapportmarkører", value=True)

        st.sidebar.header("Kartlag")
        selected_wms = st.sidebar.multiselect(
            "Aktiver WMS-lag",
            options=[p["name"] for p in WMS_PRESETS],
            default=[],
        )
        show_quickclay = st.sidebar.checkbox(
            "🟥 NVE Kvikkleiresoner",
            value=False,
            help=(
                "Henter kvikkleiresoner fra NVE WFS og viser dem som fargede polygoner. "
                "Gul = lav · Oransje = middels · Rød = høy · Mørkerød = meget høy. "
                "Klikk på en sone for detaljinfo."
            ),
        )
        with st.sidebar.expander("Egendefinert WMS"):
            enable_custom_wms = st.checkbox("Aktiver egendefinert WMS", value=False)
            custom_wms_name = st.text_input("Lagnavn i kartet", value="Egendefinert WMS")
            custom_wms_url = st.text_input("WMS-URL", value="")
            custom_wms_layers = st.text_input("Layers / native layer name", value="")
            custom_wms_version = st.selectbox("WMS-versjon", ["1.3.0", "1.1.1"], index=0)
            custom_wms_format = st.selectbox("Bildeformat", ["image/png", "image/jpeg"], index=0)

        filtered_points = points_df[
            points_df["method"].isin(selected_methods)
            & points_df["year"].between(year_range[0], year_range[1])
        ].copy()
        filtered_reports = reports_df if show_reports else reports_df.iloc[0:0].copy()

        loaded_projects = st.session_state.get("loaded_projects", {})

        try:
            m = build_map(
                filtered_points,
                filtered_reports,
                projects_geojson,
                selected_wms,
                enable_custom_wms,
                custom_wms_url,
                custom_wms_layers,
                custom_wms_name,
                custom_wms_version,
                custom_wms_format,
                loaded_projects=loaded_projects,
                show_quickclay=show_quickclay,
            )
        except Exception as e:
            st.error(f"Feil ved bygging av kart: {e}")
            m = folium.Map(location=[59.9139, 10.7522], zoom_start=11)

        col1, col2 = st.columns([3, 1], gap="large")
        with col1:
            try:
                map_data = st_folium(m, width=900, height=760, returned_objects=["last_object_clicked_popup", "last_object_clicked", "last_clicked", "all_drawings", "last_active_drawing"])
            except Exception as e:
                st.error(f"Feil ved rendering av kart: {e}")
                map_data = {}

        with col2:
            nadag_active = any("NADAG" in name for name in selected_wms)
            popup_html = map_data.get("last_object_clicked_popup") if map_data else None
            clicked_point_id = parse_clicked_point_id(popup_html)

            # Check if a loaded project borehole was clicked
            # Try popup-based detection first, then coordinate-based fallback
            proj_bh_click = _parse_project_borehole_click(popup_html, loaded_projects)
            if not proj_bh_click:
                last_obj = map_data.get("last_object_clicked") if map_data else None
                if last_obj and last_obj.get("lat"):
                    proj_bh_click = _find_project_borehole_by_coords(
                        last_obj["lat"], last_obj["lng"], loaded_projects
                    )

            if proj_bh_click:
                proj_name, bh = proj_bh_click
                st.subheader(f"📍 {bh['point_id']}")
                st.caption(f"Prosjekt: {proj_name}")
                st.metric("Metode", bh.get("method_name", "Ukjent"))
                st.metric("Dybde", f"{bh['max_depth']:.1f} m")
                st.metric("Terrengkvote", f"{bh['elevation']:.1f} m")
                st.caption(f"Dato: {bh.get('date', '–')}")
                # Show sounding diagram (matplotlib, GeoTolk-style)
                chart_buf = build_sounding_image(bh, project_name=proj_name)
                if chart_buf:
                    st.image(chart_buf, use_container_width=True)
                    st.caption("🔵 Spyling | 🔴 Slag")
                else:
                    st.info("Ingen grafdata for denne borringen.")
            elif clicked_point_id and clicked_point_id in filtered_points["point_id"].values:
                row = filtered_points.loc[filtered_points["point_id"] == clicked_point_id].iloc[0]
                st.subheader(f"📍 {clicked_point_id}")
                st.caption(row["method"])
                st.metric("Dybde", f"{row['depth_m']} m")
                st.metric("År", int(row["year"]))
                st.metric("Status", row["status"])
                st.metric("Prosjekt", row["project"])
                st.caption(f"Arkiv-ID: {row['archive_id']}\nRapport: {row['report_ref']}")
                if row.get("notes"):
                    st.write(row["notes"])
                st.link_button("↗ Åpne detaljside", detail_url("point", row["point_id"]))
            elif nadag_active:
                last_clicked = map_data.get("last_clicked") if map_data else None
                if last_clicked and last_clicked.get("lat"):
                    clat, clng = last_clicked["lat"], last_clicked["lng"]
                    with st.spinner("Henter NADAG-data..."):
                        nadag_df = query_nadag_nearby(clat, clng)
                    if nadag_df.empty:
                        st.info(f"Ingen borehull funnet ved ({clat:.5f}, {clng:.5f}).")
                    else:
                        st.subheader("📋 NADAG")
                        _cols = ["borenr", "prosjektnavn", "oppdragstaker",
                                 "borlengdeberg", "datafangstdato", "kvikkleirepaavisning", "_lat", "_lon"]
                        _show = [c for c in _cols if c in nadag_df.columns]
                        st.caption(f"{len(nadag_df)} borehull ved ({clat:.5f}, {clng:.5f}):")
                        st.dataframe(nadag_df[_show], use_container_width=True, hide_index=True)

                        # --- Select a borehole to inspect ---
                        bh_labels = []
                        for idx, r2 in nadag_df.iterrows():
                            bnr = r2.get("borenr") or "?"
                            depth = r2.get("borlengdeberg")
                            label = f"{bnr}"
                            if depth is not None:
                                label += f"  ({depth}m)"
                            bh_labels.append(label)
                        sel_idx = st.selectbox(
                            "Velg borehull for detaljer",
                            range(len(bh_labels)),
                            format_func=lambda i: bh_labels[i],
                            key=f"nadag_bh_sel_{clat}_{clng}",
                        )
                        sel_row = nadag_df.iloc[sel_idx]
                        sel_lokalid = sel_row.get("lokalid")
                        sel_borenr = sel_row.get("borenr") or "?"
                        sel_elevation = sel_row.get("hoeyde")
                        sel_profil_url = sel_row.get("boreprofil")

                        # Depth chart from GBU_metode
                        if sel_lokalid:
                            inv_df = query_nadag_investigations(str(sel_lokalid))
                            if not inv_df.empty:
                                chart_buf = build_nadag_depth_chart(
                                    inv_df,
                                    borenr=str(sel_borenr),
                                    elevation=float(sel_elevation) if sel_elevation is not None else None,
                                )
                                if chart_buf:
                                    st.image(chart_buf, use_container_width=True)
                                # Investigation metadata
                                for _, inv_row in inv_df.iterrows():
                                    method = inv_row.get("geotekniskmetode") or "Ukjent"
                                    stop = inv_row.get("stoppkode") or ""
                                    st.caption(f"**{method}** — {stop}")
                            else:
                                st.info("Ingen undersøkelsesdata (GBU_metode) for dette borehullet.")

                        # PDF profile — download + inline view
                        if sel_profil_url:
                            pdf_data = fetch_nadag_pdf(sel_profil_url)
                            if pdf_data:
                                import base64
                                b64 = base64.b64encode(pdf_data).decode()
                                st.markdown("**Boreprofil (PDF):**")
                                st.download_button(
                                    label=f"📥 Last ned profil – {sel_borenr}",
                                    data=pdf_data,
                                    file_name=f"nadag_{sel_borenr}.pdf",
                                    mime="application/pdf",
                                    key=f"pdf_sel_{sel_borenr}_{clat}",
                                    use_container_width=True,
                                )
                                st.markdown(
                                    f'<iframe src="data:application/pdf;base64,{b64}" '
                                    f'width="100%" height="500" style="border:1px solid #ccc;border-radius:4px;"></iframe>',
                                    unsafe_allow_html=True,
                                )
                            else:
                                st.link_button(f"↗ Åpne profil – {sel_borenr}", sel_profil_url, use_container_width=True)
                else:
                    st.info("Klikk i kartet for NADAG-borehull eller punktinformasjon.")
            else:
                st.info("Klikk på et punkt i kartet for å se informasjon her.")

        # ---------------------------------------------------------------
        # Polygon area analysis
        # ---------------------------------------------------------------
        all_drawings = (map_data or {}).get("all_drawings")
        last_active = (map_data or {}).get("last_active_drawing")

        # Debug: vis rådata fra kartet (kan skrus av)
        with st.expander("🔍 Debug – kartdata (slå av når alt virker)", expanded=False):
            st.json({
                "last_active_drawing": last_active,
                "all_drawings": all_drawings,
                "session_polygon_set": "area_polygon" in st.session_state,
            })

        def extract_polygon_coords(feature: dict) -> list | None:
            """Extract outer ring coords from a GeoJSON Feature or Geometry dict."""
            if not isinstance(feature, dict):
                return None
            # GeoJSON Feature
            if feature.get("type") == "Feature":
                geom = feature.get("geometry") or {}
            else:
                geom = feature
            if isinstance(geom, dict) and geom.get("type") == "Polygon":
                coords = geom.get("coordinates")
                if coords and len(coords) > 0:
                    return normalize_polygon_coords(coords[0])
            return None

        # Prioriter last_active_drawing, fall back to all_drawings
        found_coords = None
        if last_active:
            found_coords = extract_polygon_coords(last_active)
        if not found_coords and isinstance(all_drawings, list) and all_drawings:
            for drawing in reversed(all_drawings):
                c = extract_polygon_coords(drawing)
                if c:
                    found_coords = c
                    break

        if found_coords:
            st.session_state["area_polygon"] = found_coords
        elif isinstance(all_drawings, list) and all_drawings == [] and last_active is None:
            st.session_state.pop("area_polygon", None)

        polygon_coords = st.session_state.get("area_polygon")

        if polygon_coords:
            st.markdown("---")
            col_hdr, col_clr = st.columns([5, 1])
            col_hdr.subheader("📐 Områdeanalyse")
            if col_clr.button("🗑️ Fjern", help="Fjern valgt polygon"):
                st.session_state.pop("area_polygon", None)
                st.rerun()

            # Lokale data i polygon
            area_points = filter_points_in_polygon(filtered_points, polygon_coords)
            area_reports = filter_points_in_polygon(filtered_reports, polygon_coords) if not filtered_reports.empty else pd.DataFrame()

            # Project boreholes inside polygon
            area_proj_boreholes = []
            for pname, pdata in loaded_projects.items():
                for bh in pdata["boreholes"]:
                    if point_in_polygon(bh["lat"], bh["lon"], polygon_coords):
                        area_proj_boreholes.append({**bh, "_project": pname})

            # NADAG WFS-data i polygon bbox
            poly_key = tuple(tuple(c) for c in polygon_coords)
            with st.spinner("Henter NADAG-data for området..."):
                nadag_area_df = query_nadag_polygon(poly_key)

            ac1, ac2, ac3, ac4, ac5 = st.columns(5)
            ac1.metric("Lokale borepunkter", len(area_points))
            ac2.metric("Prosjekt-borringer", len(area_proj_boreholes))
            ac3.metric("NADAG-borehull", len(nadag_area_df))
            ac4.metric("Rapporter", len(area_reports))
            n_projects = area_points["archive_id"].nunique() if not area_points.empty else 0
            ac5.metric("Prosjekter", n_projects)

            # Project boreholes in polygon
            if area_proj_boreholes:
                with st.expander(f"Prosjekt-borringer ({len(area_proj_boreholes)} stk)", expanded=False):
                    pbh_rows = [{
                        "Punkt-ID": bh["point_id"],
                        "Prosjekt": bh["_project"],
                        "Metode": bh.get("method_name", ""),
                        "Dybde (m)": round(bh["max_depth"], 1),
                        "Terrengkvote": round(bh["elevation"], 1),
                    } for bh in area_proj_boreholes]
                    st.dataframe(pd.DataFrame(pbh_rows), use_container_width=True, hide_index=True)

                    # Let user pick a borehole to see graph
                    bh_options = [bh["point_id"] for bh in area_proj_boreholes]
                    sel_bh = st.selectbox("Vis sonderingsgraf", bh_options, key="area_proj_bh_select")
                    if sel_bh:
                        sel_data = next((bh for bh in area_proj_boreholes if bh["point_id"] == sel_bh), None)
                        if sel_data:
                            fig = build_sounding_figure(sel_data, project_name=sel_data.get("_project", ""))
                            st.plotly_chart(fig, use_container_width=True)

            if not nadag_area_df.empty:
                with st.expander(f"NADAG-borehull ({len(nadag_area_df)} stk)", expanded=False):
                    _cols = ["borenr", "prosjektnavn", "oppdragstaker",
                             "borlengdeberg", "datafangstdato", "kvikkleirepaavisning", "_lat", "_lon"]
                    _show = [c for c in _cols if c in nadag_area_df.columns]
                    st.dataframe(nadag_area_df[_show] if _show else nadag_area_df, use_container_width=True, hide_index=True)

                    # Select a NADAG borehole for detail view
                    na_labels = []
                    for _i, _r in nadag_area_df.iterrows():
                        _bnr = _r.get("borenr") or "?"
                        _d = _r.get("borlengdeberg")
                        _lbl = f"{_bnr}" + (f"  ({_d}m)" if _d is not None else "")
                        na_labels.append(_lbl)
                    na_sel = st.selectbox("Vis detaljer", range(len(na_labels)),
                                         format_func=lambda i: na_labels[i],
                                         key="nadag_area_bh_sel")
                    na_row = nadag_area_df.iloc[na_sel]
                    na_lid = na_row.get("lokalid")
                    if na_lid:
                        na_inv = query_nadag_investigations(str(na_lid))
                        if not na_inv.empty:
                            na_chart = build_nadag_depth_chart(
                                na_inv,
                                borenr=str(na_row.get("borenr") or "?"),
                                elevation=float(na_row["hoeyde"]) if na_row.get("hoeyde") is not None else None,
                            )
                            if na_chart:
                                st.image(na_chart, use_container_width=True)
                    na_profil = na_row.get("boreprofil")
                    if na_profil:
                        na_pdf = fetch_nadag_pdf(na_profil)
                        if na_pdf:
                            st.download_button(
                                f"📥 Profil – {na_row.get('borenr') or '?'}",
                                data=na_pdf,
                                file_name=f"nadag_{na_row.get('borenr') or na_sel}.pdf",
                                mime="application/pdf",
                                key=f"nadag_area_pdf_{na_sel}",
                                use_container_width=True,
                            )

            if not area_points.empty:
                with st.expander(f"Lokale punkter ({len(area_points)} stk)", expanded=False):
                    st.dataframe(
                        area_points[["point_id", "project", "method", "depth_m", "year", "status", "notes"]],
                        use_container_width=True, hide_index=True,
                    )

            if not area_points.empty or not area_reports.empty or not nadag_area_df.empty or area_proj_boreholes:
                if st.button("🤖 Generer AI-oppsummering av området", type="primary", use_container_width=True):
                    with st.spinner("Genererer oppsummering med Azure AI..."):
                        prompt = build_area_prompt(area_points, area_reports, projects_geojson, lab_df, project_meta, nadag_area_df)
                        summary = call_azure_ai_summary(prompt)
                    st.markdown("### 🧠 AI-oppsummering")
                    st.markdown(summary)
            else:
                st.info("Ingen datapunkter funnet i det markerte området.")

            # ── Interactive 3D Sounding Viewer ───────────────────────
            st.markdown("---")
            st.markdown("### 🌐 Interaktiv 3D-visning")
            st.caption(
                "SND-kurver og terreng i 3D. Dra for å rotere, scroll for å zoome, klikk for detaljer."
            )

            _3d_c1, _3d_c2 = st.columns([1, 1])
            with _3d_c1:
                show_terrain_3d = st.checkbox("Vis terrengoverflate", value=True, key="3d_terrain_chk")
            with _3d_c2:
                terrain_res = st.select_slider(
                    "Terrengoppløsning",
                    options=[6, 8, 10, 12, 15],
                    value=8,
                    key="3d_terrain_res",
                    help="Høyere = finere terreng, men tregere lasting.",
                )

            if st.button("🌐 Generer 3D-visning", type="primary", use_container_width=True, key="gen_3d_btn"):
                terrain_grid_data = None
                if show_terrain_3d:
                    with st.spinner("Henter terrengdata fra Kartverket …"):
                        terrain_grid_data = _build_terrain_grid(polygon_coords, resolution=terrain_res)
                st.session_state["3d_terrain_grid"] = terrain_grid_data
                st.session_state["3d_terrain_res_saved"] = terrain_res
                st.session_state["3d_ready"] = True

            if st.session_state.get("3d_ready"):
                az_col, tip_col = st.columns([3, 1])
                with az_col:
                    graph_azimuth = st.slider(
                        "↩️ Grafer-retning (°) – tilpass din visningsvinkel",
                        min_value=0, max_value=359, value=135, step=5,
                        key="3d_azimuth",
                        help=(
                            "SND-kurvene strekkes ut i denne himmelretningen. "
                            "Roter 3D-visningen til ønsket vinkel, juster så slideren "
                            "til kurvene peker mot deg – gir billboard-effekt."
                        ),
                    )
                with tip_col:
                    st.caption(
                        "💡 **Billboard-tips:**\n"
                        "1. Roter 3D med musen\n"
                        "2. Juster grader til kurven peker mot deg\n"
                        "3. Slider oppdaterer live"
                    )

                fig_3d = build_3d_sounding_plotly(
                    area_proj_boreholes=area_proj_boreholes,
                    nadag_area_df=nadag_area_df,
                    area_points=area_points,
                    polygon_coords=polygon_coords,
                    loaded_projects=loaded_projects,
                    terrain_grid=st.session_state.get("3d_terrain_grid"),
                    terrain_resolution=st.session_state.get("3d_terrain_res_saved", 8),
                    graph_azimuth_deg=float(graph_azimuth),
                )
                st.plotly_chart(fig_3d, use_container_width=True)

                # Find global max c2 for scale caption
                _max_c2_disp = 0.0
                for _bh_tmp in area_proj_boreholes:
                    _g = get_graph_data(_bh_tmp.get("_project", ""), _bh_tmp.get("point_id", ""))
                    if _g and _g.get("c2"):
                        _max_c2_disp = max(_max_c2_disp, max(_g["c2"]))
                if _max_c2_disp > 0:
                    st.caption(
                        f"📏 Skala: {_max_c2_disp:.0f} kN = maks bredde på sonderingskurve &nbsp;|&nbsp;"
                        " 🔵 Spyling &nbsp;|&nbsp; 🔴 Slag &nbsp;|&nbsp; 🟣 NADAG"
                    )

            # ── IFC 3D ground model (always available with polygon) ───
            st.markdown("---")
            st.markdown("### 🏗️ 3D Grunnmodell (IFC)")
            st.caption(
                "Genererer en forenklet 3D-modell"
            )
            if st.button("🏗️ Generer 3D grunnmodell (IFC)", use_container_width=True):
                with st.spinner("Henter terrengdata fra Kartverket og bygger IFC-modell …"):
                    try:
                        ifc_bytes = _generate_ifc_ground_model(
                            polygon_coords, area_points, area_proj_boreholes,
                        )
                        st.session_state["ifc_data"] = ifc_bytes
                        st.success("IFC-modell generert!")
                    except Exception as e:
                        st.error(f"Feil ved IFC-generering: {e}")
            if st.session_state.get("ifc_data"):
                st.download_button(
                    "📥 Last ned IFC-fil",
                    data=st.session_state["ifc_data"],
                    file_name="grunnmodell.ifc",
                    mime="application/x-step",
                    use_container_width=True,
                )

            # ── IFC Bergmodell (rock surface from NADAG stop codes) ───
            if not nadag_area_df.empty:
                st.markdown("---")
                st.markdown("### 🪨 Bergmodell (IFC)")
                st.caption(
                    "Henter stoppkoder fra NADAG for hvert borehull i området. "
                    "Velg hvilke stoppkoder som skal inkluderes, og generer en "
                    "triangulert bergoverflate basert på boredybdene."
                )

                # Fetch stoppkoder for all NADAG boreholes in polygon
                if st.button("🔍 Hent stoppkoder fra NADAG", use_container_width=True,
                              key="fetch_stoppkoder_btn"):
                    with st.spinner("Henter undersøkelsesdata for hvert borehull …"):
                        inv_data = _fetch_stoppkoder_for_boreholes(nadag_area_df)
                        st.session_state["berg_inv_data"] = inv_data
                        codes = _collect_unique_stoppkoder(inv_data)
                        st.session_state["berg_stoppkoder"] = codes
                        n_with_inv = len(inv_data)
                        st.success(
                            f"Hentet data for {n_with_inv} borehull. "
                            f"Fant {len(codes)} unike stoppkoder."
                        )

                inv_data = st.session_state.get("berg_inv_data", {})
                available_codes = st.session_state.get("berg_stoppkoder", [])

                if available_codes:
                    selected_codes = st.multiselect(
                        "Velg stoppkoder som skal inkluderes",
                        options=available_codes,
                        default=available_codes,
                        key="berg_selected_codes",
                    )

                    # Count how many boreholes match selection
                    if selected_codes:
                        sel_set = set(selected_codes)
                        n_match = 0
                        for lid, invs in inv_data.items():
                            for inv in invs:
                                if inv["stoppkode"] in sel_set and inv["boretlengde"] is not None:
                                    n_match += 1
                                    break
                        st.info(f"{n_match} borehull matcher valgte stoppkoder.")

                    if selected_codes and st.button(
                        "🪨 Lag IFC bergmodell", use_container_width=True,
                        key="generate_bergmodell_btn",
                    ):
                        with st.spinner("Bygger bergoverflate …"):
                            try:
                                berg_bytes = _generate_ifc_bergmodell(
                                    nadag_area_df, inv_data, selected_codes,
                                )
                                st.session_state["ifc_berg_data"] = berg_bytes
                                st.success("Bergmodell generert!")
                            except Exception as e:
                                st.error(f"Feil ved bergmodell-generering: {e}")

                if st.session_state.get("ifc_berg_data"):
                    st.download_button(
                        "📥 Last ned bergmodell (IFC)",
                        data=st.session_state["ifc_berg_data"],
                        file_name="bergmodell.ifc",
                        mime="application/x-step",
                        use_container_width=True,
                        key="download_bergmodell_btn",
                    )

        # ---------------------------------------------------------------
        # Polyline cross-section (Tverrprofil)
        # ---------------------------------------------------------------
        def extract_linestring_coords(feature: dict) -> list | None:
            """Extract coordinates from a GeoJSON LineString feature."""
            if not isinstance(feature, dict):
                return None
            if feature.get("type") == "Feature":
                geom = feature.get("geometry") or {}
            else:
                geom = feature
            if isinstance(geom, dict) and geom.get("type") == "LineString":
                coords = geom.get("coordinates")
                if coords and len(coords) >= 2:
                    return normalize_polygon_coords(coords)
            return None

        line_coords = None
        if last_active:
            line_coords = extract_linestring_coords(last_active)
        if not line_coords and isinstance(all_drawings, list) and all_drawings:
            for drawing in reversed(all_drawings):
                lc = extract_linestring_coords(drawing)
                if lc:
                    line_coords = lc
                    break

        if line_coords:
            st.session_state["profile_line"] = line_coords
        elif isinstance(all_drawings, list) and len(all_drawings) == 0 and last_active is None:
            st.session_state.pop("profile_line", None)

        profile_line = st.session_state.get("profile_line")

        if profile_line and loaded_projects:
            st.markdown("---")
            ph_col, pc_col = st.columns([5, 1])
            ph_col.subheader("📏 Tverrprofil / Snitt")
            if pc_col.button("🗑️ Fjern", key="remove_profile_line", help="Fjern profillinje"):
                st.session_state.pop("profile_line", None)
                st.session_state.pop("profile_image", None)
                st.rerun()

            # Convert line coords from [lon, lat] to (lat, lon)
            vertices = [(c[1], c[0]) for c in profile_line]

            # Snap to nearest boreholes
            snap_results = _snap_vertices_to_boreholes(vertices, loaded_projects, max_dist_m=100.0)
            matched = [r for r in snap_results if r is not None]

            # Remove duplicates (keep first occurrence)
            seen_ids: set[str] = set()
            unique_matched: list[dict] = []
            for m in matched:
                pid = m["borehole"]["point_id"] + "_" + m["project_name"]
                if pid not in seen_ids:
                    seen_ids.add(pid)
                    unique_matched.append(m)

            if len(unique_matched) < 2:
                st.warning(
                    "Fant færre enn 2 borepunkter nær profilens knekkpunkter. "
                    "Tegn polylinjen gjennom minst 2 borepunkter (maks 100 m avstand)."
                )
            else:
                st.success(f"Fant {len(unique_matched)} borepunkter langs profilen:")
                for um in unique_matched:
                    bh = um["borehole"]
                    st.caption(
                        f"  **{bh['point_id']}** ({um['project_name']}) – "
                        f"avst. fra linje: {um['snap_dist']:.0f} m, "
                        f"dybde: {bh['max_depth']:.1f} m, kote: {bh.get('elevation', 0):.1f} m"
                    )

                if st.button("📊 Generer tverrprofil", type="primary",
                             use_container_width=True, key="gen_profile_btn"):
                    with st.spinner("Henter terrengdata og bygger profil …"):
                        # Interpolate sample points along the polyline
                        sample_pts = _interpolate_line_coords(vertices, n_samples=20)

                        # Fetch terrain elevations for sample points
                        sample_latlon = [(p[0], p[1]) for p in sample_pts]
                        terrain_zs = _fetch_kartverket_elevations(sample_latlon)
                        terrain_dists = [p[2] for p in sample_pts]

                        # Sort boreholes by distance along profile
                        unique_matched.sort(key=lambda x: x["distance"])

                        # Build figure
                        profile_buf = build_cross_section_figure(
                            unique_matched, terrain_dists, terrain_zs
                        )
                        st.session_state["profile_image"] = profile_buf.getvalue()

                if st.session_state.get("profile_image"):
                    st.image(st.session_state["profile_image"], use_container_width=True)
                    st.download_button(
                        "📥 Last ned tverrprofil (PNG)",
                        data=st.session_state["profile_image"],
                        file_name="tverrprofil.png",
                        mime="image/png",
                        use_container_width=True,
                        key="download_profile_png",
                    )
                    st.caption("🔵 Spyling | 🔴 Slag | Svart kurve: Motstand (kN)")


def main() -> None:
    points_df = load_points()
    reports_df = load_reports()
    projects_geojson = load_projects()
    project_meta = load_project_meta()
    lab_df = load_lab_results()
    docs_df = load_documents()
    view = st.query_params.get("view", "map")
    if view == "detail":
        render_detail_page(points_df, project_meta, lab_df, docs_df)
    else:
        render_map_page(points_df, reports_df, projects_geojson, lab_df, project_meta)


if __name__ == "__main__":
    main()
