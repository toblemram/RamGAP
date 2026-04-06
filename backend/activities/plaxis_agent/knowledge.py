# -*- coding: utf-8 -*-
"""
Knowledge Retrieval — Jupyter-basert
======================================
Henter all Plaxis API-dokumentasjon direkte fra den kjørende Jupyter-serveren
på http://localhost:8888.

Flyt:
  1. Auto-henter Jupyter-token fra %APPDATA%\\jupyter\\runtime\\nbserver-*.json
  2. Henter contents_2d.ipynb for å bygge en oversikt over alle tilgjengelige
     kommandoer og hvilke notebooks de bor i
  3. Matcher brukerspørsmål mot kommandonavn via nøkkelord-scoring
  4. Henter de relevante notatbøkene og pakker ut celleinnhold
  5. Returnerer formatert innhold som kontekst til LLM-en

Ingen lokale JSON-filer, ingen FAISS-indekser.
"""

import glob
import json
import os
import re
import urllib.error
import urllib.request
from typing import Dict, List, Optional, Tuple

JUPYTER_BASE = "http://localhost:8888"
CONTENTS_INDEX_PATH = "contents_2d.ipynb"

# ---------------------------------------------------------------------------
# Cache i minnet for sesjonen
# ---------------------------------------------------------------------------
_token: Optional[str] = None
_command_index: Optional[Dict[str, str]] = None  # name -> notebook path


# ---------------------------------------------------------------------------
# Token-oppdagelse
# ---------------------------------------------------------------------------

def _find_token(force_refresh: bool = False) -> str:
    """Les Jupyter-token fra runtime JSON-fil i %APPDATA%\\jupyter\\runtime\\."""
    global _token, _command_index
    if _token and not force_refresh:
        return _token

    if force_refresh:
        _command_index = None  # Token endret → indeksen kan også være stale

    appdata = os.environ.get("APPDATA", "")
    runtime_dir = os.path.join(appdata, "jupyter", "runtime")
    pattern = os.path.join(runtime_dir, "nbserver-*.json")
    files = glob.glob(pattern)

    if not files:
        raise RuntimeError(
            f"Fant ingen kjørende Jupyter-server i {runtime_dir}. "
            "Start Plaxis 2D slik at Jupyter-serveren starter på port 8888."
        )

    # Sort by modification time — newest first
    files.sort(key=os.path.getmtime, reverse=True)

    # Try each file until we find one with port 8888
    for fpath in files:
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                data = json.load(f)
            if data.get("port") == 8888 and data.get("token"):
                _token = data["token"]
                return _token
        except (json.JSONDecodeError, OSError):
            continue

    # Fallback: just use the newest file
    with open(files[0], "r", encoding="utf-8") as f:
        data = json.load(f)

    token = data.get("token", "")
    if not token:
        raise RuntimeError("Jupyter-serveren har ingen token (ukjent konfigurasjon).")

    _token = token
    return _token


# ---------------------------------------------------------------------------
# Jupyter API-hjelper
# ---------------------------------------------------------------------------

def _fetch_jupyter(path: str) -> dict:
    """Hent innhold fra Jupyter contents API."""
    token = _find_token()
    url = f"{JUPYTER_BASE}/api/contents/{path}?token={token}"
    req = urllib.request.Request(
        url,
        headers={"Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:  # noqa: S310
            return json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        if exc.code == 403:
            # Token might be stale — force refresh and retry once
            old_token = token
            new_token = _find_token(force_refresh=True)
            retry_url = f"{JUPYTER_BASE}/api/contents/{path}?token={new_token}"
            retry_req = urllib.request.Request(
                retry_url, headers={"Accept": "application/json"})
            try:
                with urllib.request.urlopen(retry_req, timeout=15) as resp:  # noqa: S310
                    return json.loads(resp.read())
            except urllib.error.HTTPError as retry_exc:
                raise RuntimeError(
                    f"Jupyter svarte {retry_exc.code} for '{path}' "
                    f"(også etter token-refresh): {retry_exc.reason}"
                )
        raise RuntimeError(f"Jupyter svarte {exc.code} for '{path}': {exc.reason}")
    except OSError as exc:
        raise RuntimeError(
            f"Kunne ikke nå Jupyter på {JUPYTER_BASE}. Kjører serveren? ({exc})"
        )


def _extract_cells(notebook_data: dict) -> List[Tuple[str, str]]:
    """Returner liste av (cell_type, source) fra en notatbok."""
    cells = notebook_data.get("content", {}).get("cells", [])
    result = []
    for cell in cells:
        source = cell.get("source", "")
        if isinstance(source, list):
            source = "".join(source)
        cell_type = cell.get("cell_type", "code")
        if source.strip():
            result.append((cell_type, source.strip()))
    return result


# ---------------------------------------------------------------------------
# Kommandoindeks bygget fra contents_2d.ipynb
# ---------------------------------------------------------------------------

def _build_command_index() -> Dict[str, str]:
    """
    Hent contents_2d.ipynb og bygg en mapping  kommando-navn -> notatbok-sti.
    Notatboken inneholder markdown-lister med lenker på formen:
      - [activate](input_notebooks/2d-python-inputcommands-activate.ipynb)
    """
    global _command_index
    if _command_index is not None:
        return _command_index

    data = _fetch_jupyter(CONTENTS_INDEX_PATH)
    cells = _extract_cells(data)

    index: Dict[str, str] = {}
    link_re = re.compile(r'\[([^\]]+)\]\(([^)]+\.ipynb)\)')

    for cell_type, source in cells:
        for name, path in link_re.findall(source):
            index[name.strip().lower()] = path.strip()

    _command_index = index
    return _command_index


def get_all_commands() -> List[str]:
    """Returner liste over alle kjente Plaxis-kommandoer."""
    return sorted(_build_command_index().keys())


# ---------------------------------------------------------------------------
# Nøkkelord-scoring: finn relevante kommandoer for en spørring
# ---------------------------------------------------------------------------

# Semantisk mapping: brede spørsmål → relevante kommandoer
_INTENT_MAP: Dict[str, List[str]] = {
    # Prosjektinfo / oversikt
    "prosjekt|project|info|oversikt|modell|hent alt|vis alt|beskriv": [
        "dumpboreholes", "dumpmaterials", "dumpphases", "dumpplates",
        "dumplines", "dumppoints", "dumpgroups",
    ],
    # Strukturer
    "spunt|plate|vegg|struktur|konstruksjon": [
        "plate", "platemat", "dumpplates", "setmaterial",
    ],
    # Ankere
    "anker|anchor|stag|forankring": [
        "fixedendanchor", "n2nanchor", "anchormat", "dumpfixedendanchors", "dumpn2nanchors",
    ],
    # Faser
    "fase|phase|beregning|steg|kalkuler": [
        "phase", "dumpphases", "calculate", "setcurrentphase",
    ],
    # Materialer
    "material|jord|leire|sand|soil": [
        "soilmat", "dumpmaterials", "setmaterial", "soillayer",
    ],
    # Resultater
    "resultat|result|kraft|moment|forskyvning|deformasjon": [
        "getresults", "getcurveresults", "tabulate", "filter",
    ],
    # Geometri
    "geometri|punkt|linje|polygon|borehole|borehull": [
        "point", "line", "polygon", "borehole", "dumppoints", "dumplines",
    ],
    # Mesh
    "mesh|element|nett": [
        "mesh", "meshd", "gotomesh", "refine", "coarsen",
    ],
}


def _score_commands(query: str, index: Dict[str, str], k: int = 4) -> List[str]:
    """
    Scorer alle kommandoer mot spørringen og returnerer de k beste.

    Bruker:
    - Intent-mapping for brede spørsmål
    - Eksakt-treff og delstreng-matching for spesifikke kommandoer
    """
    query_lower = query.lower()
    query_words = set(re.findall(r'\w+', query_lower))

    scores: Dict[str, float] = {}

    # Intent-basert scoring: boost kommandoer som matcher brede konsepter
    for pattern, commands in _INTENT_MAP.items():
        keywords = pattern.split("|")
        if any(kw in query_lower for kw in keywords):
            for cmd in commands:
                if cmd in index:
                    scores[cmd] = scores.get(cmd, 0.0) + 4.0

    # Direkte nøkkelord-matching
    for name in index:
        s = 0.0
        if name in query_lower:
            s += 3.0
        for word in query_words:
            if len(word) >= 3 and word in name:
                s += 2.0
            if len(word) >= 4 and name in word:
                s += 1.0
        if s > 0:
            scores[name] = scores.get(name, 0.0) + s

    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [name for name, _ in ranked[:k]]


# ---------------------------------------------------------------------------
# Hent og formater notatbokinnhold
# ---------------------------------------------------------------------------

def _fetch_notebook_content(nb_path: str) -> str:
    """Hent en notatbok og returner innholdet som lesbar tekst."""
    data = _fetch_jupyter(nb_path)
    cells = _extract_cells(data)

    parts = []
    for cell_type, source in cells:
        if cell_type == "code":
            parts.append(f"```python\n{source}\n```")
        else:
            parts.append(source)
    return "\n\n".join(parts)


# ---------------------------------------------------------------------------
# Offentlig API (brukes av service.py)
# ---------------------------------------------------------------------------

def retrieve_docs(query: str, k: int = 4) -> List[Dict]:
    """
    Finn og hent de k mest relevante Plaxis-kommando-notatbøkene for spørringen.

    Returnerer liste av dicts:
        {"name": str, "path": str, "content": str}
    """
    index = _build_command_index()
    matched_names = _score_commands(query, index, k=k)

    docs = []
    for name in matched_names:
        path = index[name]
        try:
            content = _fetch_notebook_content(path)
            docs.append({"name": name, "path": path, "content": content})
        except Exception as exc:
            docs.append({"name": name, "path": path, "content": f"[Kunne ikke hente: {exc}]"})
    return docs


def build_api_cards(docs: List[Dict], max_per_doc: int = 2000, max_total: int = 8000) -> str:
    """Formater hentede notatbøker som kompakte API-kort til LLM-prompten."""
    parts, total = [], 0
    for d in docs:
        header = f"### Plaxis-kommando: `{d['name']}`  ({d['path']})"
        body = d.get("content", "")
        card = f"{header}\n\n{body}"
        if len(card) > max_per_doc:
            card = card[:max_per_doc] + "\n… (avkortet)"
        if total + len(card) > max_total:
            break
        parts.append(card)
        total += len(card)
    return "\n\n---\n\n".join(parts)


def ensure_loaded():
    """Verifiser at Jupyter-serveren er tilgjengelig og indeksen kan bygges."""
    _build_command_index()


# ---------------------------------------------------------------------------
# PDF-tekst-ekstraksjon (for brukerens opplastede filer)
# ---------------------------------------------------------------------------

def extract_pdf_text(pdf_bytes: bytes) -> str:
    """Pakk ut tekst fra en PDF.  Feiler mykt om pypdf mangler."""
    try:
        import io
        from pypdf import PdfReader  # type: ignore[import-untyped]
        reader = PdfReader(io.BytesIO(pdf_bytes))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    except ImportError:
        return "[PDF-parsing krever pypdf-pakken.  Installer med: pip install pypdf]"
    except Exception as exc:
        return f"[Kunne ikke parse PDF: {exc}]"
