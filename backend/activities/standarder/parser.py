# -*- coding: utf-8 -*-
"""PDF parser for technical standards — extracts sections and paragraphs.

Supports multiple extraction strategies:
  1. PyMuPDF (fitz) — handles the widest range of PDFs
  2. pypdf          — fallback if fitz is unavailable
  3. Page-based chunking when no structured headings are detected

For scanned / image-based PDFs the parser returns per-page sections so the
content is still navigable, and flags ``is_scanned=True`` in the metadata.
"""

from __future__ import annotations

import io
import re
from dataclasses import dataclass, field
from typing import NamedTuple


@dataclass
class Section:
    """A section/paragraph from a standard document."""

    id: str          # e.g. "7.6.2.3" or "side-5"
    title: str       # e.g. "Materialfaktorer for jordegenskaper"
    level: int       # heading depth (1=chapter, 2=section, …)
    content: str     # full text of this section
    page: int = 0    # 1-based page number (0 = unknown)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "level": self.level,
            "content": self.content,
            "page": self.page,
        }


class ExtractionResult(NamedTuple):
    """Raw text + per-page texts + metadata from PDF extraction."""
    full_text: str
    pages: list[str]          # one entry per page
    page_count: int
    is_scanned: bool          # True if no readable text was found


# ---------------------------------------------------------------------------
# Text extraction — multi-strategy
# ---------------------------------------------------------------------------

def _extract_with_fitz(pdf_bytes: bytes) -> ExtractionResult | None:
    """Try PyMuPDF (fitz) — best quality for most PDFs."""
    try:
        import fitz  # noqa: F811
    except ImportError:
        return None

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    pages: list[str] = []
    char_count = 0
    for page in doc:
        text = page.get_text("text") or ""
        pages.append(text)
        char_count += len(text.strip())
    doc.close()

    is_scanned = char_count < 100  # essentially no readable text
    full = "\n\n".join(pages)
    return ExtractionResult(full, pages, len(pages), is_scanned)


def _extract_with_pypdf(pdf_bytes: bytes) -> ExtractionResult | None:
    """Fallback: use pypdf."""
    try:
        from pypdf import PdfReader
    except ImportError:
        return None

    reader = PdfReader(io.BytesIO(pdf_bytes))
    pages: list[str] = []
    char_count = 0
    for p in reader.pages:
        text = p.extract_text() or ""
        pages.append(text)
        char_count += len(text.strip())

    is_scanned = char_count < 100
    full = "\n\n".join(pages)
    return ExtractionResult(full, pages, len(pages), is_scanned)


def extract_text_from_pdf(pdf_bytes: bytes) -> ExtractionResult:
    """Extract text using the best available library.

    Returns an ``ExtractionResult`` with per-page text and metadata.
    """
    result = _extract_with_fitz(pdf_bytes)
    if result is not None:
        return result

    result = _extract_with_pypdf(pdf_bytes)
    if result is not None:
        return result

    # Nothing available
    return ExtractionResult("", [], 0, True)


# ---------------------------------------------------------------------------
# Heading patterns — ordered by specificity
# ---------------------------------------------------------------------------

# Pattern 1: "NA.2.4 Title" or "7.6.2.3 Title"
_PAT_NUMBERED = re.compile(
    r"^((?:NA\.)?(?:\d+\.)*\d+)\s+(.{3,120})$",
    re.MULTILINE,
)

# Pattern 2: "Kapittel 7 — Geoteknisk prosjektering" (Norwegian chapter style)
_PAT_KAPITTEL = re.compile(
    r"^(?:Kapittel|Kap\.?|Chapter|Avsnitt)\s+(\d+(?:\.\d+)*)\s*[—–:\-]?\s*(.{3,120})$",
    re.MULTILINE | re.IGNORECASE,
)

# Pattern 3: "§ 7.6.2 Title" (paragraph sign)
_PAT_PARAGRAPH = re.compile(
    r"^§\s*((?:\d+\.)*\d+)\s+(.{3,120})$",
    re.MULTILINE,
)

# Pattern 4: "Tabell NA.A.6" / "Figur 2.1" (tables and figures as section markers)
_PAT_TABLE_FIG = re.compile(
    r"^((?:Tabell|Table|Figur|Figure)\s+(?:NA\.)?[A-Z]?\d+(?:\.\d+)*)\s*[—–:\-]?\s*(.{0,120})$",
    re.MULTILINE | re.IGNORECASE,
)


def _is_plausible_title(text: str) -> bool:
    """Filter out lines that look like data rather than headings."""
    t = text.strip()
    # Too short or too long
    if len(t) < 2 or len(t) > 150:
        return False
    # Mostly digits / punctuation (e.g. table row "1.2  3.4  5.6")
    alpha = sum(1 for c in t if c.isalpha())
    if alpha < 2:
        return False
    # Starts with common non-heading patterns
    if re.match(r"^\d+[,\.]\d+\s*(?:kN|kPa|m\b|mm\b|%)", t):
        return False
    return True


def _find_headings(text: str) -> list[tuple[int, str, str, str]]:
    """Find all heading candidates.

    Returns list of (position, section_id, title, pattern_name).
    """
    candidates: list[tuple[int, str, str, str]] = []

    for m in _PAT_NUMBERED.finditer(text):
        sec_id, title = m.group(1), m.group(2).strip()
        if _is_plausible_title(title):
            candidates.append((m.start(), sec_id, title, "numbered"))

    for m in _PAT_KAPITTEL.finditer(text):
        sec_id, title = m.group(1), m.group(2).strip()
        if _is_plausible_title(title):
            candidates.append((m.start(), sec_id, title, "kapittel"))

    for m in _PAT_PARAGRAPH.finditer(text):
        sec_id, title = m.group(1), m.group(2).strip()
        if _is_plausible_title(title):
            candidates.append((m.start(), sec_id, title, "paragraph"))

    for m in _PAT_TABLE_FIG.finditer(text):
        sec_id, title = m.group(1), m.group(2).strip() or "(uten tittel)"
        candidates.append((m.start(), sec_id, title, "table_fig"))

    # Sort by position & deduplicate overlapping matches
    candidates.sort(key=lambda c: c[0])
    return _deduplicate(candidates)


def _deduplicate(
    candidates: list[tuple[int, str, str, str]],
    min_gap: int = 5,
) -> list[tuple[int, str, str, str]]:
    """Remove near-overlapping candidates (keep earliest per position)."""
    if not candidates:
        return candidates
    out = [candidates[0]]
    for c in candidates[1:]:
        if c[0] - out[-1][0] >= min_gap:
            out.append(c)
    return out


# ---------------------------------------------------------------------------
# Section building
# ---------------------------------------------------------------------------

def _level_from_id(sec_id: str) -> int:
    """Compute nesting level from a section id like '7.6.2'."""
    return sec_id.count(".") + 1


def _sections_from_headings(
    text: str,
    headings: list[tuple[int, str, str, str]],
) -> list[Section]:
    """Build Section objects by slicing text between heading positions."""
    sections: list[Section] = []
    for i, (pos, sec_id, title, _pat) in enumerate(headings):
        # Content starts after the heading line
        line_end = text.find("\n", pos)
        start = (line_end + 1) if line_end != -1 else pos + len(title)
        end = headings[i + 1][0] if i + 1 < len(headings) else len(text)
        content = text[start:end].strip()
        sections.append(Section(
            id=sec_id,
            title=title,
            level=_level_from_id(sec_id),
            content=content,
        ))
    return sections


def _sections_from_pages(pages: list[str]) -> list[Section]:
    """Fallback: create one section per page."""
    sections: list[Section] = []
    for i, page_text in enumerate(pages, 1):
        text = page_text.strip()
        if not text:
            continue
        # Try to extract first line as title
        first_line = text.split("\n", 1)[0].strip()[:100]
        rest = text.split("\n", 1)[1].strip() if "\n" in text else ""
        sections.append(Section(
            id=f"side-{i}",
            title=first_line or f"Side {i}",
            level=1,
            content=rest or text,
            page=i,
        ))
    return sections


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def parse_sections(extraction: ExtractionResult | str) -> list[Section]:
    """Parse extracted text into structured sections.

    Accepts either an ``ExtractionResult`` (preferred) or a plain text
    string (legacy compatibility).

    Strategy:
      1. Try to find numbered headings in the full text
      2. If enough headings found → split by headings
      3. Otherwise → fall back to per-page chunking
      4. If pages are empty (scanned PDF) → return a single info section
    """
    if isinstance(extraction, str):
        # Legacy call — wrap in ExtractionResult
        text = extraction
        pages: list[str] = []
        is_scanned = len(text.strip()) < 100
    else:
        text = extraction.full_text
        pages = extraction.pages
        is_scanned = extraction.is_scanned

    # Scanned / image PDF — no usable text
    if is_scanned or len(text.strip()) < 50:
        if pages:
            return [Section(
                id="info",
                title="Skannet PDF — ingen tekst funnet",
                level=1,
                content=(
                    f"Denne PDF-en ser ut til å være skannet (bilde-basert) og "
                    f"inneholder {len(pages)} sider uten lesbar tekst.\n\n"
                    "For å bruke denne standarden i RamGAP kan du:\n"
                    "• Bruke en digital (søkbar) versjon av standarden\n"
                    "• Konvertere PDF-en med OCR-programvare (f.eks. Adobe Acrobat)\n"
                    "• Laste opp seksjoner manuelt som tekst"
                ),
                page=0,
            )]
        return [Section(id="1", title="Fulltekst", level=1, content=text.strip())]

    # Try heading detection
    headings = _find_headings(text)

    # Need at least 3 headings to consider it a real structure
    if len(headings) >= 3:
        sections = _sections_from_headings(text, headings)
        if sections:
            return sections

    # Fallback: page-based chunking
    if pages and len(pages) > 1:
        page_sections = _sections_from_pages(pages)
        if page_sections:
            return page_sections

    # Last resort: split long text into ~2000-char chunks
    if len(text) > 3000:
        return _chunk_text(text, chunk_size=2000)

    return [Section(id="1", title="Fulltekst", level=1, content=text.strip())]


def _chunk_text(text: str, chunk_size: int = 2000) -> list[Section]:
    """Split text into roughly equal chunks, breaking at paragraph boundaries."""
    paragraphs = re.split(r"\n\s*\n", text)
    sections: list[Section] = []
    current = ""
    idx = 1

    for para in paragraphs:
        if len(current) + len(para) > chunk_size and current:
            first_line = current.strip().split("\n", 1)[0][:80]
            sections.append(Section(
                id=f"del-{idx}",
                title=first_line or f"Del {idx}",
                level=1,
                content=current.strip(),
            ))
            idx += 1
            current = para
        else:
            current = current + "\n\n" + para if current else para

    if current.strip():
        first_line = current.strip().split("\n", 1)[0][:80]
        sections.append(Section(
            id=f"del-{idx}",
            title=first_line or f"Del {idx}",
            level=1,
            content=current.strip(),
        ))

    return sections


def extract_text_from_pdf_file(file_path: str) -> ExtractionResult:
    """Convenience: extract from a file path instead of bytes."""
    with open(file_path, "rb") as f:
        return extract_text_from_pdf(f.read())
