"""
Feedback Component
==================
Provides show_feedback_dialog() — a sidebar button that lets users sende
en bugrapport eller et forbedringsforslag direkte som GitHub Issue.

Required environment variable (set in .env):
    GITHUB_TOKEN=github_pat_...

The token only needs Issues: Read & Write on toblemram/RamGAP.
"""

import os
import sys
import platform
import importlib.metadata
import datetime
import uuid
import requests
import streamlit as st
from dotenv import load_dotenv

# Load .env from the project root (two levels up from this file)
_ENV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '.env')
load_dotenv(_ENV_PATH, override=False)

_REPO = "toblemram/RamGAP"
_GITHUB_API = f"https://api.github.com/repos/{_REPO}/issues"


def _upload_screenshot_to_azure(file_bytes: bytes, filename: str) -> str | None:
    """
    Upload screenshot to Azure Blob Storage (temp container) and return a SAS URL
    valid for 1 year — long enough for the GitHub issue to remain useful.
    Returns None if upload fails or connection string is missing.
    """
    conn_str = os.getenv("AZURE_STORAGE_CONNECTION_STRING", "")
    container = os.getenv("AZURE_STORAGE_TEMP_CONTAINER", "temp-uploads")
    if not conn_str or "AccountName=..." in conn_str:
        return None
    try:
        from azure.storage.blob import (
            BlobServiceClient,
            ContentSettings,
            generate_blob_sas,
            BlobSasPermissions,
        )
        blob_name = f"bug-reports/{datetime.datetime.utcnow().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:6]}-{filename}"
        ext = filename.rsplit(".", 1)[-1].lower()
        content_type = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "gif": "image/gif"}.get(ext, "image/png")

        service_client = BlobServiceClient.from_connection_string(conn_str)
        blob_client = service_client.get_blob_client(container=container, blob=blob_name)
        blob_client.upload_blob(
            file_bytes,
            overwrite=True,
            content_settings=ContentSettings(content_type=content_type),
        )

        # Extract account name and key from connection string
        parts = dict(p.split("=", 1) for p in conn_str.split(";") if "=" in p)
        account_name = parts.get("AccountName", "")
        account_key = parts.get("AccountKey", "")

        sas_token = generate_blob_sas(
            account_name=account_name,
            container_name=container,
            blob_name=blob_name,
            account_key=account_key,
            permission=BlobSasPermissions(read=True),
            expiry=datetime.datetime.utcnow() + datetime.timedelta(days=365),
        )
        return f"{blob_client.url}?{sas_token}"
    except Exception:
        return None


def _collect_context(username: str) -> dict:
    """Build a dict of automatic diagnostics."""
    python_ver = platform.python_version()
    os_info = f"{platform.system()} {platform.release()} ({platform.machine()})"

    # Streamlit version
    try:
        st_ver = importlib.metadata.version("streamlit")
    except Exception:
        st_ver = "ukjent"

    # Current page / session state keys (safe subset)
    page = st.session_state.get("current_page", "ukjent")
    project = st.session_state.get("selected_project")
    project_name = project.get("name") if isinstance(project, dict) else None

    return {
        "bruker": username,
        "side": page,
        "prosjekt": project_name or "–",
        "os": os_info,
        "python": python_ver,
        "streamlit": st_ver,
        "tidspunkt": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


def _format_issue_body(description: str, steps: str, ctx: dict, screenshot_note: str) -> str:
    lines = [
        "## Beskrivelse",
        description,
        "",
        "## Steg for å gjenskape",
        steps if steps.strip() else "_Ikke oppgitt_",
        "",
        "## Automatisk diagnostikk",
        "| Felt | Verdi |",
        "|------|-------|",
    ]
    for k, v in ctx.items():
        lines.append(f"| {k} | {v} |")

    if screenshot_note:
        lines += ["", "## Skjermbilde", screenshot_note]

    lines += ["", "---", "_Sendt automatisk fra RamGAP bug-rapportknapp_"]
    return "\n".join(lines)


def _create_github_issue(title: str, body: str, token: str) -> tuple[bool, str]:
    """POST to GitHub Issues API. Returns (success, message)."""
    if not token:
        return False, "GITHUB_TOKEN er ikke satt (se .env)"
    try:
        r = requests.post(
            _GITHUB_API,
            json={"title": title, "body": body, "labels": ["bug"]},
            headers={
                "Authorization": f"token {token}",
                "Accept": "application/vnd.github+json",
            },
            timeout=10,
        )
        if r.status_code == 201:
            url = r.json().get("html_url", "")
            return True, url
        else:
            return False, f"GitHub svarte {r.status_code}: {r.text[:200]}"
    except requests.RequestException as exc:
        return False, str(exc)



# --- Ny tilbakemeldingsdialog ---
_TYPE_CONFIG = {
    "bug": {
        "label":       "🐛 Feil (bug)",
        "gh_label":    "bug",
        "title_hint":  "f.eks. «Plaxis level 3 krasjer ved oppstart»",
        "desc_hint":   "Beskriv feilen så godt du kan — hva skjedde, og hva forventet du?",
        "extra_label": "Steg for å gjenskape (valgfritt)",
        "extra_hint":  "1. Gå til …\n2. Klikk …\n3. …",
        "section":     "## Steg for å gjenskape",
    },
    "forslag": {
        "label":       "💡 Forslag til forbedring",
        "gh_label":    "enhancement",
        "title_hint":  "f.eks. «Kan vi eksportere resultater til PDF?»",
        "desc_hint":   "Beskriv forslaget ditt — hva ønsker du, og hvorfor vil det være nyttig?",
        "extra_label": "Hvordan bør det fungere? (valgfritt)",
        "extra_hint":  "Beskriv gjerne trinn for trinn eller med eksempler.",
        "section":     "## Ønsket funksjonalitet",
    },
}

def _format_issue_body(report_type: str, description: str, extra: str, ctx: dict, screenshot_note: str) -> str:
    cfg = _TYPE_CONFIG[report_type]
    lines = [
        "## Beskrivelse",
        description,
        "",
        cfg["section"],
        extra if extra.strip() else "_Ikke oppgitt_",
        "",
        "## Automatisk diagnostikk",
        "| Felt | Verdi |",
        "|------|-------|",
    ]
    for k, v in ctx.items():
        lines.append(f"| {k} | {v} |")
    if screenshot_note:
        lines += ["", "## Vedlegg", screenshot_note]
    lines += ["", "---", f"_Sendt automatisk fra RamGAP tilbakemeldingsknapp_"]
    return "\n".join(lines)

def _create_github_issue(title: str, body: str, labels: list[str], token: str) -> tuple[bool, str]:
    """POST to GitHub Issues API. Returns (success, url_or_error)."""
    if not token:
        return False, "GITHUB_TOKEN er ikke satt (se .env)"
    try:
        r = requests.post(
            _GITHUB_API,
            json={"title": title, "body": body, "labels": labels},
            headers={
                "Authorization": f"token {token}",
                "Accept": "application/vnd.github+json",
            },
            timeout=10,
        )
        if r.status_code == 201:
            return True, r.json().get("html_url", "")
        else:
            return False, f"GitHub svarte {r.status_code}: {r.text[:200]}"
    except requests.RequestException as exc:
        return False, str(exc)

def show_feedback_dialog(username: str):
    """
    Renders the feedback button + inline form in the sidebar.
    Call this from the sidebar block in app.py.
    """
    if st.button("💬 Tilbakemelding / Forslag", use_container_width=True, key="open_feedback"):
        st.session_state["_feedback_open"] = not st.session_state.get("_feedback_open", False)

    if not st.session_state.get("_feedback_open"):
        return

    st.markdown("---")
    st.markdown("#### 💬 Send tilbakemelding")

    report_type = st.radio(
        "Type",
        options=["bug", "forslag"],
        format_func=lambda x: _TYPE_CONFIG[x]["label"],
        horizontal=True,
        key="_feedback_type",
    )
    cfg = _TYPE_CONFIG[report_type]

    with st.form("feedback_form", clear_on_submit=True):
        title = st.text_input(
            "Kort beskrivelse *",
            placeholder=cfg["title_hint"],
        )
        description = st.text_area(
            "Beskrivelse",
            placeholder=cfg["desc_hint"],
            height=110,
        )
        extra = st.text_area(
            cfg["extra_label"],
            placeholder=cfg["extra_hint"],
            height=70,
        )
        screenshot = st.file_uploader(
            "Legg ved bilde (valgfritt)",
            type=["png", "jpg", "jpeg", "gif"],
            help="Bildet lastes opp til Azure og vises direkte i GitHub-issue-en.",
        )

        col_send, col_cancel = st.columns(2)
        submitted = col_send.form_submit_button("📤 Send", type="primary", use_container_width=True)
        cancelled = col_cancel.form_submit_button("Avbryt", use_container_width=True)

    if cancelled:
        st.session_state["_feedback_open"] = False
        st.rerun()

    if submitted:
        if not title.strip():
            st.error("Du må fylle inn en kort beskrivelse.")
            return

        token = os.getenv("GITHUB_TOKEN", "")
        ctx = _collect_context(username)

        screenshot_note = ""
        if screenshot:
            file_bytes = screenshot.read()
            with st.spinner("Laster opp bilde…"):
                img_url = _upload_screenshot_to_azure(file_bytes, screenshot.name)
            if img_url:
                screenshot_note = f"![{screenshot.name}]({img_url})"
            else:
                screenshot_note = (
                    f"Bruker lastet opp `{screenshot.name}` ({screenshot.size} bytes). "
                    "Bildet ble ikke lastet opp automatisk – be brukeren sende det direkte."
                )

        # Prefix title with type for clarity in GitHub
        prefix = "[Bug]" if report_type == "bug" else "[Forslag]"
        full_title = f"{prefix} {title.strip()}"

        body = _format_issue_body(report_type, description, extra, ctx, screenshot_note)
        ok, result = _create_github_issue(full_title, body, [cfg["gh_label"]], token)

        if ok:
            verb = "Bugrapport" if report_type == "bug" else "Forslag"
            st.success(f"✅ {verb} sendt! [Se på GitHub]({result})")
            st.session_state["_feedback_open"] = False
        else:
            st.error(f"Feil ved sending: {result}")
