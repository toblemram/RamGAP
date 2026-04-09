# -*- coding: utf-8 -*-
"""
Knowledge Retrieval — Filbasert
======================================
Henter Plaxis API-dokumentasjon fra lokale markdown-filer
(docs/plaxis_2d_commands.md og docs/plaxis_2d_reference.md).

Flyt:
  1. Leser plaxis_2d_commands.md og parser ut seksjoner per kommando
  2. Matcher brukerspørsmål mot kommandonavn via nøkkelord-scoring
  3. Returnerer de mest relevante seksjonene som kontekst til LLM-en

Ingen Jupyter-server, ingen nettverkstilkoblinger for docs.
"""

import os
import re
from typing import Dict, List, Optional

# Sti til docs-mappen relativt til denne filen
_DOCS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "docs")
_COMMANDS_FILE = os.path.join(_DOCS_DIR, "plaxis_2d_commands.md")
_REFERENCE_FILE = os.path.join(_DOCS_DIR, "plaxis_2d_reference.md")

# ---------------------------------------------------------------------------
# Cache i minnet for sesjonen
# ---------------------------------------------------------------------------
_command_index: Optional[Dict[str, str]] = None  # name -> section content


# ---------------------------------------------------------------------------
# Markdown-parser: del opp plaxis_2d_commands.md i seksjoner per kommando
# ---------------------------------------------------------------------------

def _parse_commands_md() -> Dict[str, str]:
    """
    Les plaxis_2d_commands.md og bygg en mapping  kommando-navn -> innhold.

    Filen har seksjoner på formen:
      ## INPUT: kommando-navn
    eller
      ## OUTPUT: kommando-navn

    Alt mellom to slike overskrifter hører til én kommando.
    """
    path = os.path.normpath(_COMMANDS_FILE)
    if not os.path.isfile(path):
        raise RuntimeError(
            f"Fant ikke {path}. Sjekk at docs/plaxis_2d_commands.md finnes."
        )

    with open(path, "r", encoding="utf-8") as f:
        text = f.read()

    # Splitt på ## INPUT: xxx  eller  ## OUTPUT: xxx
    section_re = re.compile(
        r'^## (?:INPUT|OUTPUT):\s*(\w+)',
        re.MULTILINE,
    )

    matches = list(section_re.finditer(text))
    index: Dict[str, str] = {}

    for i, m in enumerate(matches):
        name = m.group(1).strip().lower()
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        content = text[start:end].strip()
        # Hvis kommandoen dukker opp flere ganger (input + output), slå sammen
        if name in index:
            index[name] += "\n\n---\n\n" + content
        else:
            index[name] = content

    return index


def _build_command_index() -> Dict[str, str]:
    """Bygg (eller returner cachet) kommandoindeks fra markdown-filen."""
    global _command_index
    if _command_index is not None:
        return _command_index

    _command_index = _parse_commands_md()
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
# Offentlig API (brukes av service.py)
# ---------------------------------------------------------------------------

def retrieve_docs(query: str, k: int = 4) -> List[Dict]:
    """
    Finn de k mest relevante Plaxis-kommando-seksjonene for spørringen.

    Returnerer liste av dicts:
        {"name": str, "path": "plaxis_2d_commands.md", "content": str}
    """
    index = _build_command_index()
    matched_names = _score_commands(query, index, k=k)

    docs = []
    for name in matched_names:
        content = index[name]
        docs.append({"name": name, "path": "plaxis_2d_commands.md", "content": content})
    return docs


def build_api_cards(docs: List[Dict], max_per_doc: int = 2000, max_total: int = 8000) -> str:
    """Formater hentede kommandoseksjoner som kompakte API-kort til LLM-prompten."""
    parts, total = [], 0
    for d in docs:
        header = f"### Plaxis-kommando: `{d['name']}`"
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
    """Verifiser at markdown-filen finnes og kan parses."""
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
