# -*- coding: utf-8 -*-
"""
Standarder Routes
=================
Flask Blueprint for managing uploaded technical standards (PDF),
searching their contents, and running AI compliance checks.

Endpoints:
    POST   /api/standarder/upload                        — Upload a standard PDF
    GET    /api/standarder/documents                     — List uploaded standards
    DELETE /api/standarder/documents/<doc_id>             — Delete a standard
    GET    /api/standarder/documents/<doc_id>/sections    — Get parsed sections
    GET    /api/standarder/search                        — Full-text search
    POST   /api/standarder/check                         — AI compliance check
    POST   /api/standarder/explain                       — AI explanation of a section
"""

from __future__ import annotations

import json
import os
import shutil
import uuid
from datetime import datetime, timezone

from flask import Blueprint, jsonify, request
from openai import AzureOpenAI

from .parser import extract_text_from_pdf, extract_text_from_pdf_file, parse_sections

standarder_bp = Blueprint("standarder", __name__, url_prefix="/api/standarder")

# Local storage for uploaded standards
_STORAGE_DIR = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "standarder"
)
os.makedirs(_STORAGE_DIR, exist_ok=True)

_INDEX_FILE = os.path.join(_STORAGE_DIR, "index.json")

# Azure OpenAI (reuse same env vars as GeoGPT)
_AZURE_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "")
_AZURE_KEY = os.getenv("AZURE_OPENAI_API_KEY", "")
_AZURE_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")
_DEPLOYMENT = (
    os.getenv("GEOGPT_DEPLOYMENT")
    or os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")
)


def _get_ai_client() -> AzureOpenAI | None:
    if not _AZURE_ENDPOINT or not _AZURE_KEY:
        return None
    return AzureOpenAI(
        azure_endpoint=_AZURE_ENDPOINT,
        api_key=_AZURE_KEY,
        api_version=_AZURE_API_VERSION,
    )


# ---------------------------------------------------------------------------
# Index helpers
# ---------------------------------------------------------------------------

def _load_index() -> list[dict]:
    if not os.path.exists(_INDEX_FILE):
        return []
    with open(_INDEX_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_index(index: list[dict]) -> None:
    with open(_INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)


# ── Upload ────────────────────────────────────────────────────────────────

@standarder_bp.route("/upload", methods=["POST"])
def upload_standard():
    """Upload a standard PDF, extract text and parse into sections."""
    if "file" not in request.files:
        return jsonify({"error": "Ingen fil vedlagt"}), 400

    file = request.files["file"]
    if not file.filename:
        return jsonify({"error": "Tomt filnavn"}), 400

    name = request.form.get("name", "").strip() or file.filename
    pdf_bytes = file.read()

    # Extract and parse
    extraction = extract_text_from_pdf(pdf_bytes)
    sections = parse_sections(extraction)

    # Unique id
    doc_id = uuid.uuid4().hex[:8]
    doc_dir = os.path.join(_STORAGE_DIR, doc_id)
    os.makedirs(doc_dir, exist_ok=True)

    # Save PDF
    pdf_path = os.path.join(doc_dir, file.filename)
    with open(pdf_path, "wb") as f:
        f.write(pdf_bytes)

    # Save parsed sections
    sections_data = [s.to_dict() for s in sections]
    with open(os.path.join(doc_dir, "sections.json"), "w", encoding="utf-8") as f:
        json.dump(sections_data, f, ensure_ascii=False, indent=2)

    # Save raw text
    with open(os.path.join(doc_dir, "raw_text.txt"), "w", encoding="utf-8") as f:
        f.write(extraction.full_text)

    # Update index
    index = _load_index()
    entry = {
        "id": doc_id,
        "name": name,
        "filename": file.filename,
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
        "section_count": len(sections),
        "size_bytes": len(pdf_bytes),
        "page_count": extraction.page_count,
        "is_scanned": extraction.is_scanned,
    }
    index.append(entry)
    _save_index(index)

    return jsonify({"success": True, "document": entry})


# ── List / Delete ─────────────────────────────────────────────────────────

@standarder_bp.route("/documents", methods=["GET"])
def list_documents():
    return jsonify({"documents": _load_index()})


@standarder_bp.route("/documents/<doc_id>", methods=["DELETE"])
def delete_document(doc_id: str):
    index = _load_index()
    entry = next((d for d in index if d["id"] == doc_id), None)
    if not entry:
        return jsonify({"error": "Dokument ikke funnet"}), 404

    doc_dir = os.path.join(_STORAGE_DIR, doc_id)
    if os.path.isdir(doc_dir):
        shutil.rmtree(doc_dir)

    index = [d for d in index if d["id"] != doc_id]
    _save_index(index)
    return jsonify({"success": True})


# ── Sections ──────────────────────────────────────────────────────────────

@standarder_bp.route("/documents/<doc_id>/sections", methods=["GET"])
def get_sections(doc_id: str):
    sections_file = os.path.join(_STORAGE_DIR, doc_id, "sections.json")
    if not os.path.exists(sections_file):
        return jsonify({"error": "Dokument ikke funnet"}), 404
    with open(sections_file, "r", encoding="utf-8") as f:
        sections = json.load(f)
    return jsonify({"sections": sections})


# ── Search ────────────────────────────────────────────────────────────────

@standarder_bp.route("/search", methods=["GET"])
def search_standards():
    """Full-text search across all uploaded standards."""
    q = request.args.get("q", "").strip().lower()
    doc_id_filter = request.args.get("doc_id", "")
    if not q:
        return jsonify({"results": []})

    results: list[dict] = []
    for doc in _load_index():
        if doc_id_filter and doc["id"] != doc_id_filter:
            continue
        sections_file = os.path.join(_STORAGE_DIR, doc["id"], "sections.json")
        if not os.path.exists(sections_file):
            continue
        with open(sections_file, "r", encoding="utf-8") as f:
            sections = json.load(f)
        for sec in sections:
            haystack = f"{sec.get('id', '')} {sec.get('title', '')} {sec.get('content', '')}".lower()
            if q in haystack:
                results.append({
                    "doc_id": doc["id"],
                    "doc_name": doc["name"],
                    "section_id": sec["id"],
                    "title": sec["title"],
                    "snippet": _snippet(sec["content"], q),
                    "level": sec["level"],
                })
    return jsonify({"results": results[:50]})


def _snippet(text: str, query: str, ctx: int = 150) -> str:
    lower = text.lower()
    pos = lower.find(query)
    if pos == -1:
        return text[:300]
    start = max(0, pos - ctx)
    end = min(len(text), pos + len(query) + ctx)
    snippet = text[start:end]
    if start > 0:
        snippet = "…" + snippet
    if end < len(text):
        snippet += "…"
    return snippet


# ── AI: Compliance check ─────────────────────────────────────────────────

@standarder_bp.route("/check", methods=["POST"])
def check_compliance():
    """AI compliance check: compare project data against a standard."""
    body = request.get_json() or {}
    doc_id = body.get("doc_id", "")
    project_summary = body.get("project_summary", "")
    section_ids = body.get("section_ids", [])

    if not doc_id or not project_summary:
        return jsonify({"error": "doc_id og project_summary er påkrevd"}), 400

    sections_file = os.path.join(_STORAGE_DIR, doc_id, "sections.json")
    if not os.path.exists(sections_file):
        return jsonify({"error": "Standard ikke funnet"}), 404

    with open(sections_file, "r", encoding="utf-8") as f:
        all_sections = json.load(f)

    if section_ids:
        sections = [s for s in all_sections if s["id"] in section_ids]
    else:
        sections = all_sections[:30]

    standard_text = "\n\n".join(
        f"§{s['id']} {s['title']}\n{s['content'][:800]}" for s in sections
    )

    client = _get_ai_client()
    if not client:
        return jsonify({"error": "Azure OpenAI er ikke konfigurert. Sett AZURE_OPENAI_ENDPOINT og AZURE_OPENAI_API_KEY."}), 503

    system = (
        "Du er en norsk geoteknisk rådgiver. Analyser prosjektdataene opp mot "
        "den gitte standarden. For hver relevant paragraf i standarden:\n"
        "1. Vurder om kravene er oppfylt, delvis oppfylt, eller ikke oppfylt\n"
        "2. Gi en kort begrunnelse\n"
        "3. Foreslå eventuelle tiltak\n\n"
        "Svar i strukturert format med emoji-indikatorer:\n"
        "✅ = oppfylt, ⚠️ = delvis/usikker, ❌ = ikke oppfylt\n\n"
        "Svar alltid på norsk."
    )
    user_msg = (
        f"=== PROSJEKTDATA ===\n{project_summary}\n\n"
        f"=== STANDARD ===\n{standard_text}"
    )

    try:
        response = client.chat.completions.create(
            model=_DEPLOYMENT,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user_msg},
            ],
        )
        answer = response.choices[0].message.content
        return jsonify({"result": answer, "sections_checked": len(sections)})
    except Exception as exc:
        return jsonify({"error": f"AI-feil: {exc}"}), 500


# ── AI: Explain section ──────────────────────────────────────────────────

@standarder_bp.route("/explain", methods=["POST"])
def explain_section():
    """AI explanation of a standard section in context of project data."""
    body = request.get_json() or {}
    doc_id = body.get("doc_id", "")
    section_id = body.get("section_id", "")
    project_context = body.get("project_context", "")

    if not doc_id or not section_id:
        return jsonify({"error": "doc_id og section_id er påkrevd"}), 400

    sections_file = os.path.join(_STORAGE_DIR, doc_id, "sections.json")
    if not os.path.exists(sections_file):
        return jsonify({"error": "Standard ikke funnet"}), 404

    with open(sections_file, "r", encoding="utf-8") as f:
        all_sections = json.load(f)

    section = next((s for s in all_sections if s["id"] == section_id), None)
    if not section:
        return jsonify({"error": f"Seksjon {section_id} ikke funnet"}), 404

    client = _get_ai_client()
    if not client:
        return jsonify({"error": "Azure OpenAI er ikke konfigurert."}), 503

    system = (
        "Du er en norsk geoteknisk rådgiver som forklarer standarder. "
        "Forklar den gitte paragrafen på en enkel og praktisk måte. "
        "Hvis prosjektdata er gitt, relater forklaringen til prosjektet. "
        "Bruk eksempler der det er nyttig. Svar alltid på norsk."
    )
    user_parts = [
        f"=== PARAGRAF §{section['id']} — {section['title']} ===",
        section["content"],
    ]
    if project_context:
        user_parts.insert(0, f"=== PROSJEKTKONTEKST ===\n{project_context}\n")

    try:
        response = client.chat.completions.create(
            model=_DEPLOYMENT,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": "\n\n".join(user_parts)},
            ],
        )
        return jsonify({
            "explanation": response.choices[0].message.content,
            "section": section,
        })
    except Exception as exc:
        return jsonify({"error": f"AI-feil: {exc}"}), 500


# ── Re-parse ──────────────────────────────────────────────────────────────

@standarder_bp.route("/documents/<doc_id>/reparse", methods=["POST"])
def reparse_document(doc_id: str):
    """Re-parse an already uploaded document with the improved parser."""
    index = _load_index()
    entry = next((d for d in index if d["id"] == doc_id), None)
    if not entry:
        return jsonify({"error": "Dokument ikke funnet"}), 404

    doc_dir = os.path.join(_STORAGE_DIR, doc_id)
    pdf_path = os.path.join(doc_dir, entry.get("filename", ""))
    if not os.path.exists(pdf_path):
        return jsonify({"error": "PDF-fil ikke funnet"}), 404

    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()

    extraction = extract_text_from_pdf(pdf_bytes)
    sections = parse_sections(extraction)

    sections_data = [s.to_dict() for s in sections]
    with open(os.path.join(doc_dir, "sections.json"), "w", encoding="utf-8") as f:
        json.dump(sections_data, f, ensure_ascii=False, indent=2)

    with open(os.path.join(doc_dir, "raw_text.txt"), "w", encoding="utf-8") as f:
        f.write(extraction.full_text)

    # Update index metadata
    entry["section_count"] = len(sections)
    entry["page_count"] = extraction.page_count
    entry["is_scanned"] = extraction.is_scanned
    _save_index(index)

    return jsonify({
        "success": True,
        "section_count": len(sections),
        "page_count": extraction.page_count,
        "is_scanned": extraction.is_scanned,
    })


# ── Extract report text from project folder ──────────────────────────────

@standarder_bp.route("/extract-report", methods=["POST"])
def extract_report():
    """Extract text from a PDF/text file in the project folder.

    Body: {"file_path": "/absolute/path/to/report.pdf"}
    Returns: {"text": "...", "page_count": N, "is_scanned": bool}
    """
    body = request.get_json() or {}
    file_path = body.get("file_path", "").strip()

    if not file_path:
        return jsonify({"error": "file_path er påkrevd"}), 400

    if not os.path.isfile(file_path):
        return jsonify({"error": f"Filen finnes ikke: {file_path}"}), 404

    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".pdf":
        extraction = extract_text_from_pdf_file(file_path)
        return jsonify({
            "text": extraction.full_text[:50000],  # limit for API
            "page_count": extraction.page_count,
            "is_scanned": extraction.is_scanned,
            "truncated": len(extraction.full_text) > 50000,
        })
    elif ext in {".txt", ".md", ".csv", ".json", ".xml"}:
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                text = f.read(50000)
            return jsonify({
                "text": text,
                "page_count": 0,
                "is_scanned": False,
                "truncated": len(text) >= 50000,
            })
        except Exception as exc:
            return jsonify({"error": f"Lesefeil: {exc}"}), 500
    elif ext in {".docx"}:
        try:
            import zipfile
            import xml.etree.ElementTree as ET
            parts: list[str] = []
            with zipfile.ZipFile(file_path) as z:
                with z.open("word/document.xml") as doc_xml:
                    tree = ET.parse(doc_xml)
                    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
                    for para in tree.iter(f"{{{ns['w']}}}p"):
                        texts = [t.text for t in para.iter(f"{{{ns['w']}}}t") if t.text]
                        if texts:
                            parts.append("".join(texts))
            text = "\n".join(parts)
            return jsonify({
                "text": text[:50000],
                "page_count": 0,
                "is_scanned": False,
                "truncated": len(text) > 50000,
            })
        except Exception as exc:
            return jsonify({"error": f"Lesefeil: {exc}"}), 500
    else:
        return jsonify({"error": f"Filtype {ext} støttes ikke. Bruk PDF, DOCX, TXT, MD, CSV eller JSON."}), 400
