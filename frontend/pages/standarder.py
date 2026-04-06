# -*- coding: utf-8 -*-
"""Standarder — interaktiv standard-leser med AI-forklaringer og samsvarskontroll.

Prosjektdata hentes fra den lokale prosjektmappen (folder_path), ikke fra
databasen.  Mappen skannes for SND-filer, Excel-rapporter, PDF-er, CSV-er
og andre relevante dokumenter som brukes som kontekst for AI-analysen.
"""

from __future__ import annotations

import csv
import os
from pathlib import Path
from typing import Any

import streamlit as st
from components.api_client import APIClient
from components.auth import require_username

USERNAME = require_username()
api = APIClient()

# ── Styling ───────────────────────────────────────────────────────────────

st.markdown("""
<style>
.std-banner {
    background: linear-gradient(135deg, #1b3a5c 0%, #2e7d32 100%);
    border-radius: 14px;
    padding: 26px 32px;
    color: white;
    margin-bottom: 20px;
}
.std-banner h2 { margin: 0 0 6px 0; font-size: 1.65rem; font-weight: 700; }
.std-banner p  { margin: 0; opacity: 0.82; font-size: 0.93rem; }
.section-id    { color: #1565c0; font-weight: 700; font-size: 0.95rem; }
.section-title { font-weight: 600; font-size: 0.92rem; margin-left: 8px; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="std-banner">
    <h2>📚 Standarder</h2>
    <p>Last opp tekniske standarder, bla i paragrafer, og sjekk prosjektet
    ditt mot kravene med AI — basert på filene i prosjektmappen.</p>
</div>
""", unsafe_allow_html=True)


# ── Helpers — project folder scanning ─────────────────────────────────────

def _get_project() -> dict | None:
    return st.session_state.get("selected_project")


def _scan_folder_files(folder: str) -> dict[str, list[str]]:
    """Return {extension: [filename, …]} for every file in *folder* (recursive)."""
    groups: dict[str, list[str]] = {}
    root = Path(folder)
    if not root.is_dir():
        return groups
    for p in root.rglob("*"):
        if p.is_file():
            ext = p.suffix.upper() or "(ingen)"
            groups.setdefault(ext, []).append(str(p.relative_to(root)))
    return groups


def _read_text_file(path: str, max_chars: int = 3000) -> str:
    """Read a text file, returning at most *max_chars* characters."""
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read(max_chars)
    except Exception:
        return ""


def _read_csv_summary(path: str, max_rows: int = 20) -> str:
    """Return a short textual summary of a CSV file."""
    try:
        rows: list[list[str]] = []
        with open(path, "r", encoding="utf-8-sig", errors="replace") as f:
            reader = csv.reader(f, delimiter=";")
            for i, row in enumerate(reader):
                if i >= max_rows:
                    break
                rows.append(row)
        if not rows:
            return ""
        header = " | ".join(rows[0])
        body = "\n".join(" | ".join(r) for r in rows[1:])
        return f"{header}\n{body}"
    except Exception:
        return ""


def _read_snd_summary(path: str) -> str:
    """Return first ~40 lines of an SND file (header + some data)."""
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            lines = [f.readline() for _ in range(40)]
        return "".join(lines)
    except Exception:
        return ""


def _build_project_summary_from_folder(project: dict) -> str:
    """Build a textual summary of the project based on its local folder.

    Scans the folder for SND-files, CSVs, Excel files, text files and
    other documents and assembles a context string for the AI.
    """
    folder = project.get("folder_path", "")
    parts: list[str] = [f"Prosjekt: {project.get('name', 'Ukjent')}"]
    if project.get("description"):
        parts.append(f"Beskrivelse: {project['description']}")
    parts.append(f"Prosjektmappe: {folder}")

    if not folder or not os.path.isdir(folder):
        parts.append("(Prosjektmappen finnes ikke eller er ikke satt.)")
        return "\n".join(parts)

    groups = _scan_folder_files(folder)

    # ---- Overview ----
    total = sum(len(v) for v in groups.values())
    parts.append(f"\nTotalt {total} filer i prosjektmappen.")
    for ext, files in sorted(groups.items()):
        parts.append(f"  {ext}: {len(files)} fil(er)")

    root = Path(folder)

    # ---- SND files (boreholes) ----
    snd_files = groups.get(".SND", []) + groups.get(".snd", [])
    if snd_files:
        parts.append(f"\n=== SND-filer ({len(snd_files)} stk) ===")
        for snd in snd_files[:10]:
            summary = _read_snd_summary(str(root / snd))
            if summary:
                parts.append(f"\n--- {snd} ---\n{summary}")

    # ---- CSV files (e.g. geotolk output, lab data) ----
    csv_files = groups.get(".CSV", []) + groups.get(".csv", [])
    if csv_files:
        parts.append(f"\n=== CSV-filer ({len(csv_files)} stk) ===")
        for cf in csv_files[:5]:
            summary = _read_csv_summary(str(root / cf))
            if summary:
                parts.append(f"\n--- {cf} ---\n{summary}")

    # ---- Text / Markdown ----
    txt_files = (
        groups.get(".TXT", []) + groups.get(".txt", [])
        + groups.get(".MD", []) + groups.get(".md", [])
    )
    if txt_files:
        parts.append(f"\n=== Tekstfiler ({len(txt_files)} stk) ===")
        for tf in txt_files[:5]:
            content = _read_text_file(str(root / tf))
            if content:
                parts.append(f"\n--- {tf} ---\n{content}")

    # ---- JSON reports ----
    json_files = groups.get(".JSON", []) + groups.get(".json", [])
    if json_files:
        parts.append(f"\n=== JSON-rapporter ({len(json_files)} stk) ===")
        for jf in json_files[:3]:
            content = _read_text_file(str(root / jf), max_chars=4000)
            if content:
                parts.append(f"\n--- {jf} ---\n{content}")

    # ---- Excel files (just list them) ----
    xls_files = (
        groups.get(".XLSX", []) + groups.get(".xlsx", [])
        + groups.get(".XLS", []) + groups.get(".xls", [])
    )
    if xls_files:
        parts.append(f"\n=== Excel-filer ({len(xls_files)} stk) ===")
        for xf in xls_files:
            parts.append(f"  - {xf}")

    # ---- PDF files (just list them) ----
    pdf_files = groups.get(".PDF", []) + groups.get(".pdf", [])
    if pdf_files:
        parts.append(f"\n=== PDF-filer ({len(pdf_files)} stk) ===")
        for pf in pdf_files:
            parts.append(f"  - {pf}")

    return "\n".join(parts)


# ── Cached helpers ────────────────────────────────────────────────────────

@st.cache_data(ttl=30)
def _cached_standards():
    return api.get_standards()


@st.cache_data(ttl=60)
def _cached_sections(doc_id: str):
    return api.get_standard_sections(doc_id)


# ── Tabs ──────────────────────────────────────────────────────────────────

tab_browse, tab_check, tab_manage = st.tabs([
    "📖 Bla i standarder",
    "✅ Samsvarskontroll",
    "⚙️ Administrer",
])

# ══════════════════════════════════════════════════════════════════════════
# TAB 1: Bla i standarder
# ══════════════════════════════════════════════════════════════════════════

with tab_browse:
    standards = _cached_standards()

    if not standards:
        st.info(
            "Ingen standarder er lastet opp ennå. "
            "Gå til **Administrer**-fanen for å laste opp en PDF."
        )
    else:
        # Standard selector
        std_options = {s["name"]: s for s in standards}
        selected_name = st.selectbox(
            "Velg standard", options=list(std_options.keys()), key="browse_std"
        )
        selected_std = std_options[selected_name]
        doc_id = selected_std["id"]

        # Search bar
        search_q = st.text_input(
            "🔍 Søk i standarden",
            placeholder="F.eks. materialfaktor, bæreevne, grunnundersøkelser …",
            key="browse_search",
        )

        sections = _cached_sections(doc_id)

        # Filter
        if search_q:
            q_lower = search_q.lower()
            sections = [
                s for s in sections
                if q_lower in s.get("id", "").lower()
                or q_lower in s.get("title", "").lower()
                or q_lower in s.get("content", "").lower()
            ]
            st.caption(f"{len(sections)} treff for «{search_q}»")

        if not sections:
            st.warning("Ingen seksjoner funnet.")
        else:
            # Table of Contents
            with st.expander("📑 Innholdsfortegnelse", expanded=False):
                for s in sections:
                    indent = "&nbsp;" * (s.get("level", 1) - 1) * 4
                    st.markdown(
                        f'{indent}<span class="section-id">§{s["id"]}</span>'
                        f'<span class="section-title">{s["title"]}</span>',
                        unsafe_allow_html=True,
                    )

            # Display sections
            for s in sections:
                level = s.get("level", 1)
                htag = f"h{min(level + 2, 6)}"
                with st.container(border=True):
                    st.markdown(
                        f"<{htag}>§{s['id']}  {s['title']}</{htag}>",
                        unsafe_allow_html=True,
                    )

                    # Show content (truncate very long sections)
                    content = s.get("content", "")
                    if len(content) <= 2000:
                        st.markdown(content)
                    else:
                        st.markdown(content[:2000])
                        with st.expander("Vis mer …"):
                            st.markdown(content[2000:])

                    # AI explain button
                    project = _get_project()
                    btn_label = "🤖 Forklar med AI"
                    if project:
                        btn_label += f"  (kontekst: {project['name']})"

                    if st.button(btn_label, key=f"explain_{doc_id}_{s['id']}"):
                        ctx = ""
                        if project:
                            with st.spinner("Leser prosjektmappen …"):
                                ctx = _build_project_summary_from_folder(project)
                        with st.spinner("GeoGPT analyserer …"):
                            result = api.explain_standard_section(
                                doc_id, s["id"], ctx
                            )
                        if result.get("error"):
                            st.error(result["error"])
                        else:
                            st.markdown("---")
                            st.markdown("**🤖 GeoGPT-forklaring:**")
                            st.markdown(
                                result.get("explanation", "Ingen forklaring.")
                            )


# ══════════════════════════════════════════════════════════════════════════
# TAB 2: Samsvarskontroll
# ══════════════════════════════════════════════════════════════════════════

with tab_check:
    project = _get_project()
    standards = _cached_standards()

    if not standards:
        st.info("Last opp minst én standard i **Administrer**-fanen.")
    elif not project:
        st.warning(
            "⚠️ Velg et prosjekt fra **Prosjekter**-siden for å kjøre samsvarskontroll.\n\n"
            "Gå til 🏠 Prosjekter, velg et prosjekt, og kom tilbake hit."
        )
    else:
        folder = project.get("folder_path", "")
        st.subheader(f"Samsvarskontroll — {project['name']}")
        if folder:
            st.caption(f"📁 Prosjektmappe: `{folder}`")
        else:
            st.warning("Prosjektet har ingen prosjektmappe. Sett en mappe i Prosjektinnstillinger.")

        # Select standard
        std_options = {s["name"]: s for s in standards}
        std_name = st.selectbox(
            "Velg standard å sjekke mot",
            list(std_options.keys()),
            key="check_std_select",
        )
        std = std_options[std_name]
        doc_id = std["id"]

        # Select sections
        all_sections = _cached_sections(doc_id)
        section_labels = {
            f"§{s['id']} {s['title']}": s["id"] for s in all_sections
        }
        selected_secs = st.multiselect(
            "Velg seksjoner å sjekke (tom = alle relevante)",
            options=list(section_labels.keys()),
            key="check_sec_select",
        )
        chosen_ids = [section_labels[lbl] for lbl in selected_secs]

        st.divider()

        # ── Data source selection ────────────────────────────────────
        st.markdown("#### 📋 Prosjektdata for samsvarskontroll")
        st.caption("Velg hva som skal sjekkes mot standarden.")

        data_source = st.radio(
            "Datakilde",
            options=["📄 Velg rapport fra prosjektmappen", "📁 Skann hele prosjektmappen", "✏️ Skriv inn manuelt"],
            horizontal=True,
            key="check_data_source",
        )

        summary = ""

        if data_source == "📄 Velg rapport fra prosjektmappen":
            # ── Report file picker ───────────────────────────────
            if not folder or not os.path.isdir(folder):
                st.warning("Prosjektmappen finnes ikke eller er ikke satt.")
            else:
                root = Path(folder)
                # Find all report-like files
                report_extensions = {".pdf", ".docx", ".txt", ".md", ".json", ".csv"}
                report_files: list[str] = []
                for p in root.rglob("*"):
                    if p.is_file() and p.suffix.lower() in report_extensions:
                        report_files.append(str(p.relative_to(root)))

                if not report_files:
                    st.info("Ingen rapport-filer funnet i prosjektmappen.")
                else:
                    # Group by extension for easier browsing
                    report_files.sort(key=lambda f: (Path(f).suffix.lower(), f))
                    selected_reports = st.multiselect(
                        "Velg rapport(er) å sjekke",
                        options=report_files,
                        key="check_report_files",
                        help="Velg én eller flere filer. Teksten trekkes ut og sendes til AI.",
                    )

                    if selected_reports:
                        parts: list[str] = [f"Prosjekt: {project.get('name', 'Ukjent')}"]
                        for rel_path in selected_reports:
                            abs_path = str(root / rel_path)
                            with st.spinner(f"Leser {rel_path} …"):
                                result = api.extract_report_text(abs_path)

                            if result.get("error"):
                                st.warning(f"⚠️ {rel_path}: {result['error']}")
                            else:
                                text = result.get("text", "")
                                if result.get("is_scanned"):
                                    st.warning(f"⚠️ {rel_path} er en skannet PDF uten lesbar tekst.")
                                elif text:
                                    parts.append(f"\n=== {rel_path} ===")
                                    parts.append(text)
                                    if result.get("truncated"):
                                        st.caption(f"ℹ️ {rel_path} ble avkortet (for stor fil).")

                        summary = "\n".join(parts)

                        with st.expander(f"👁️ Forhåndsvisning ({len(summary)} tegn)", expanded=False):
                            st.text(summary[:8000])
                            if len(summary) > 8000:
                                st.caption(f"… (viser 8000 av {len(summary)} tegn)")

        elif data_source == "📁 Skann hele prosjektmappen":
            # ── Full folder scan ─────────────────────────────────
            with st.expander("📋 Prosjektdata fra mappen", expanded=False):
                with st.spinner("Skanner prosjektmappen …"):
                    summary = _build_project_summary_from_folder(project)
                st.text(summary[:5000])
                if len(summary) > 5000:
                    st.caption(f"… ({len(summary)} tegn totalt)")

        else:
            # ── Manual input ─────────────────────────────────────
            summary = st.text_area(
                "Beskriv prosjektet og relevante data",
                height=200,
                placeholder=(
                    "F.eks.:\n"
                    "Prosjekt: Byggegruppe E6 Kvithammar\n"
                    "Jordart: Leire, cu = 25 kPa\n"
                    "Gravdybde: 8 m\n"
                    "Spuntvegg: AZ 26, lengde 15 m\n"
                    "Grunnvannstand: -2 m under terreng"
                ),
                key="check_manual_input",
            )

        # Extra context (always available)
        extra = st.text_area(
            "Legg til ekstra kontekst (valgfritt)",
            placeholder="F.eks. spesifikke krav, jordart, murhøyde, grunnvannstand …",
            key="check_extra_ctx",
        )
        if extra.strip():
            summary += f"\n\nEkstra kontekst fra bruker:\n{extra.strip()}"

        # Run button
        if not summary.strip():
            st.info("Velg datakilde og last inn data for å kjøre samsvarskontroll.")
        else:
            if st.button(
                "🚀 Kjør samsvarskontroll", type="primary", use_container_width=True
            ):
                with st.spinner("GeoGPT analyserer prosjektet mot standarden …"):
                    result = api.check_standard_compliance(
                        doc_id, summary, chosen_ids
                    )

                if result.get("error"):
                    st.error(result["error"])
                else:
                    st.success(
                        f"Analyse fullført — {result.get('sections_checked', '?')} "
                        "seksjoner sjekket"
                    )
                    st.markdown("---")
                    st.markdown(result.get("result", "Ingen resultat."))


# ══════════════════════════════════════════════════════════════════════════
# TAB 3: Administrer
# ══════════════════════════════════════════════════════════════════════════

with tab_manage:
    st.subheader("⚙️ Administrer standarder")
    st.caption(
        "Last opp PDF-er av tekniske standarder (Eurokode 7, V220 osv.). "
        "Teksten trekkes ut og deles inn i paragrafer automatisk."
    )

    # Upload form
    with st.form("upload_standard", clear_on_submit=True):
        uploaded = st.file_uploader("Velg PDF-fil", type=["pdf"])
        std_name_input = st.text_input(
            "Navn på standarden",
            placeholder="F.eks. NS-EN 1997-1:2004 (Eurocode 7)",
        )
        submit = st.form_submit_button("📤 Last opp", type="primary")

    if submit and uploaded:
        with st.spinner(f"Laster opp og analyserer {uploaded.name} …"):
            result = api.upload_standard(
                uploaded.getvalue(), uploaded.name, std_name_input
            )
        if result.get("success"):
            doc = result["document"]
            st.success(
                f"✅ {uploaded.name} lastet opp — "
                f"{doc['section_count']} seksjoner funnet"
            )
            _cached_standards.clear()
            st.rerun()
        else:
            st.error(f"❌ {result.get('error', 'Ukjent feil')}")

    # List existing
    st.divider()
    st.markdown("#### Opplastede standarder")
    standards = _cached_standards()

    if not standards:
        st.info("Ingen standarder lastet opp ennå.")
    else:
        for std in standards:
            c1, c2, c3, c4 = st.columns([5, 1, 1, 1])
            size_kb = round(std.get("size_bytes", 0) / 1024, 1)
            pages = std.get("page_count", "?")
            scanned_tag = " ⚠️ skannet" if std.get("is_scanned") else ""
            c1.markdown(
                f"📄 **{std['name']}** &nbsp; `{size_kb} KB` &nbsp; "
                f"({std['section_count']} seksjoner, {pages} sider{scanned_tag})"
            )
            c2.markdown(f"_{std.get('uploaded_at', '')[:10]}_")
            if c3.button("🔄", key=f"reparse_std_{std['id']}",
                         help="Parse PDF-en på nytt med forbedret parser"):
                with st.spinner("Parser på nytt …"):
                    res = api.reparse_standard(std["id"])
                if res.get("success"):
                    scanned = " (skannet PDF)" if res.get("is_scanned") else ""
                    st.success(
                        f"✅ Ny parsing: {res['section_count']} seksjoner, "
                        f"{res.get('page_count', '?')} sider{scanned}"
                    )
                    _cached_standards.clear()
                    _cached_sections.clear()
                    st.rerun()
                else:
                    st.error(res.get("error", "Feil"))
            if c4.button("🗑️", key=f"del_std_{std['id']}"):
                res = api.delete_standard(std["id"])
                if res.get("success"):
                    st.success("✅ Slettet")
                    _cached_standards.clear()
                    st.rerun()
                else:
                    st.error(res.get("error", "Feil"))

    st.divider()
    st.markdown("#### Foreslåtte standarder å laste opp")
    st.markdown("""
- **NS-EN 1997-1** (Eurocode 7) — Geoteknisk prosjektering, del 1: Generelle regler
- **NS-EN 1997-2** — Geoteknisk prosjektering, del 2: Grunnundersøkelser og prøving
- **Håndbok V220** — Geoteknikk i vegbygging (SVV)
- **NS-EN 12699** — Utførelse av spesielle geotekniske arbeider – Peler
- **NS-EN 14199** — Mikropeler
- **NGF Veiledninger** — Diverse veiledninger fra Norsk Geoteknisk Forening
    """)
