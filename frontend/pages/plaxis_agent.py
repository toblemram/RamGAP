# -*- coding: utf-8 -*-
"""
Plaxis Agent — AI-drevet kodeassistent for PLAXIS
===================================================
Todelt layout:
  VENSTRE: Chat med agenten
  HØYRE:   Funn-panel — viser strukturerte resultater fra agenten.
           Brukeren kan velge (klikke) på elementer, og valgte elementer
           blir inkludert som kontekst i neste prompt.
"""

import re
import streamlit as st
from components.api_client import APIClient

# ---------------------------------------------------------------------------
# Initialisering
# ---------------------------------------------------------------------------

st.title("🤖 Plaxis Agent")
api = APIClient()

# Session state defaults
_defaults = {
    "pa_messages": [],
    "pa_connected": False,
    "pa_session_id": "agent_default",
    "pa_pdf_text": None,
    "pa_pdf_name": None,
    "pa_auto_execute": True,
    "pa_findings": [],          # list of {"section": str, "items": list[str]}
    "pa_selected": [],           # list of selected item keys ("section::item")
}
for k, v in _defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ---------------------------------------------------------------------------
# Tilkoblingspanel — vises øverst FØR chatten
# ---------------------------------------------------------------------------

if not st.session_state.pa_connected:
    st.info("Koble til PLAXIS for å starte agenten.")

    with st.container(border=True):
        st.subheader("🔌 Koble til PLAXIS")
        col_port, col_pwd = st.columns(2)
        with col_port:
            port = st.number_input("Port (Input)", value=10000, min_value=1, max_value=65535,
                                   key="pa_port",
                                   help="Input-porten til PLAXIS (vanligvis 10000)")
        with col_pwd:
            password = st.text_input("Passord (Code)", type="password", key="pa_pwd",
                                     help="Passordet som ble satt i PLAXIS Expert > Configure remote scripting")

        output_port = st.number_input(
            "Port (Output)", value=10001, min_value=1, max_value=65535,
            key="pa_output_port",
            help="Output-porten til PLAXIS (vanligvis 10001). Brukes for å hente resultater (krefter, momenter etc.)",
        )

        col_btn, col_status = st.columns([1, 2])
        with col_btn:
            connect_clicked = st.button("🔌 Koble til", use_container_width=True, type="primary")
        with col_status:
            if connect_clicked:
                with st.spinner("Kobler til PLAXIS…"):
                    res = api.plaxis_agent_connect(
                        port=port,
                        password=password,
                        session_id=st.session_state.pa_session_id,
                        output_port=output_port,
                        output_password=password,
                    )
                if res.get("success"):
                    st.session_state.pa_connected = True
                    st.rerun()
                else:
                    st.error(res.get("error", "Tilkobling feilet"))

    st.stop()  # Ikke vis chatten før tilkoblet

# ---------------------------------------------------------------------------
# Sidebar — innstillinger
# ---------------------------------------------------------------------------

with st.sidebar:
    st.success("✅ PLAXIS tilkoblet")

    if st.button("🔌 Koble fra", use_container_width=True):
        st.session_state.pa_connected = False
        st.session_state.pa_messages = []
        st.session_state.pa_findings = []
        st.session_state.pa_selected = []
        st.rerun()

    st.divider()

    st.session_state.pa_auto_execute = st.toggle(
        "Auto-kjør kode i PLAXIS",
        value=st.session_state.pa_auto_execute,
        help="Når aktiv, kjøres generert kode automatisk mot Plaxis. Ved feil prøver agenten igjen.",
    )

    st.divider()

    # PDF-opplasting
    st.markdown("### 📄 Last opp dokument")
    uploaded = st.file_uploader("PDF for ekstra kontekst", type=["pdf"], key="pa_pdf_upload")
    if uploaded is not None and uploaded.name != st.session_state.pa_pdf_name:
        with st.spinner("Leser PDF…"):
            res = api.plaxis_agent_upload_pdf(uploaded.getvalue(), uploaded.name)
        if "error" in res:
            st.error(res["error"])
        else:
            st.session_state.pa_pdf_text = res.get("text", "")
            st.session_state.pa_pdf_name = uploaded.name
            st.success(f"📄 {uploaded.name} lastet inn ({len(st.session_state.pa_pdf_text)} tegn)")

    if st.session_state.pa_pdf_text:
        st.caption(f"Aktiv PDF: **{st.session_state.pa_pdf_name}**")
        if st.button("🗑️ Fjern PDF"):
            st.session_state.pa_pdf_text = None
            st.session_state.pa_pdf_name = None
            st.rerun()

    st.divider()

    if st.button("🗑️ Tøm samtale", use_container_width=True):
        st.session_state.pa_messages = []
        st.session_state.pa_findings = []
        st.session_state.pa_selected = []
        st.rerun()


# ---------------------------------------------------------------------------
# Hjelpefunksjoner
# ---------------------------------------------------------------------------

def _build_history() -> list:
    """Konverter st.session_state.pa_messages til LLM-format."""
    history = []
    for msg in st.session_state.pa_messages:
        if msg["role"] == "user":
            history.append({"role": "user", "content": msg["content"]})
        elif msg["role"] == "assistant":
            content = msg.get("code") or msg.get("content", "")
            history.append({"role": "assistant", "content": content})
    return history


_SECTION_RE = re.compile(r'^===\s*(.+?)\s*===$')
_ITEM_RE = re.compile(r'^ITEM:\s*(.+)$')


def _parse_findings(output: str) -> list:
    """
    Parser output til strukturerte funn.
    Hvert funn: {"section": str, "items": list[str]}
    Items er linjer som starter med 'ITEM:' eller alle ikke-tomme linjer i seksjonen.
    """
    sections = []
    current_section = None
    current_items = []

    for line in output.splitlines():
        sec_match = _SECTION_RE.match(line)
        if sec_match:
            if current_section is not None:
                sections.append({"section": current_section, "items": current_items})
            current_section = sec_match.group(1)
            current_items = []
        elif current_section is not None:
            stripped = line.strip()
            if not stripped or stripped.startswith("(ingen"):
                continue
            # Prefer ITEM: prefix but accept any non-empty line
            item_match = _ITEM_RE.match(stripped)
            if item_match:
                current_items.append(item_match.group(1).strip())
            elif stripped:
                current_items.append(stripped)

    if current_section is not None:
        sections.append({"section": current_section, "items": current_items})

    return sections


# Ikon-mapping for funn
_SECTION_ICONS = {
    "prosjektinfo": "📋", "materialer": "🧱", "jordlag": "🌍",
    "borehull": "🕳️", "plater": "🔩", "geogrids": "🔲",
    "embedded beams": "📐", "fixed end anchors": "⚓",
    "faser": "📊", "punkter": "📍", "linjer": "📏",
    "geometri": "📐", "ankere": "🔗",
    "node-to-node anchors": "🔗", "node to node anchors": "🔗",
}


# ---------------------------------------------------------------------------
# LAYOUT: Venstre = Chat   |   Høyre = Funn-panel
# ---------------------------------------------------------------------------

col_chat, col_findings = st.columns([3, 2])


# ===================== HØYRE PANEL — FUNN =====================

with col_findings:
    st.markdown("### 📋 Funn fra agenten")

    findings = st.session_state.pa_findings
    selected = list(st.session_state.pa_selected)  # work with a copy

    if not findings:
        st.caption("Spør agenten om å hente data — resultatene vises her.")
    else:
        # Tøm valg-knapp
        top_c1, top_c2 = st.columns([1, 1])
        with top_c1:
            sel_count = len(selected)
            st.caption(f"**{sel_count}** valgt")
        with top_c2:
            if selected and st.button("🗑️ Fjern valg", key="clear_sel", use_container_width=True):
                st.session_state.pa_selected = []
                st.rerun()

        # Rebuild selected list from checkbox states
        new_selected = []

        for sec_idx, sec in enumerate(findings):
            section_name = sec["section"]
            items = sec["items"]
            icon = _SECTION_ICONS.get(section_name.lower(), "📦")
            count = len(items)

            with st.expander(f"{icon} {section_name} ({count})", expanded=(count > 0 and count <= 20)):
                if not items:
                    st.caption("Ingen elementer.")
                else:
                    for item_idx, item in enumerate(items):
                        item_key = f"{section_name}::{item}"
                        cb_key = f"cb_{sec_idx}_{item_idx}"
                        is_checked = item_key in selected

                        if st.checkbox(
                            item,
                            value=is_checked,
                            key=cb_key,
                            help="Velg for å inkludere i neste prompt",
                        ):
                            new_selected.append(item_key)

        # Oppdater session state
        st.session_state.pa_selected = new_selected

        # Vis valgte elementer kompakt
        if new_selected:
            st.divider()
            st.markdown("#### ✅ Valgt kontekst")
            for sel in sorted(new_selected):
                sec_name, item_text = sel.split("::", 1) if "::" in sel else ("", sel)
                icon = _SECTION_ICONS.get(sec_name.lower(), "📦")
                st.caption(f"{icon} **{sec_name}**: {item_text}")


# ===================== VENSTRE PANEL — CHAT =====================

with col_chat:
    st.markdown("### 💬 Chat")

    # Vis eksisterende meldinger
    chat_container = st.container(height=500)
    with chat_container:
        for idx, msg in enumerate(st.session_state.pa_messages):
            if msg["role"] == "user":
                with st.chat_message("user"):
                    st.markdown(msg["content"])
            elif msg["role"] == "assistant":
                with st.chat_message("assistant", avatar="🤖"):
                    if msg.get("content"):
                        st.markdown(msg["content"])
                    if msg.get("code"):
                        with st.expander("🐍 Vis kode", expanded=False):
                            st.code(msg["code"], language="python")
                    if msg.get("output"):
                        # Kort oppsummering i chatten — detaljer i høyre panel
                        output = msg["output"]
                        sections = _parse_findings(output)
                        if sections:
                            summary_parts = []
                            for s in sections:
                                icon = _SECTION_ICONS.get(s["section"].lower(), "📦")
                                summary_parts.append(f"{icon} **{s['section']}** ({len(s['items'])})")
                            st.markdown("Hentet: " + " · ".join(summary_parts))
                            st.caption("Se detaljer i panelet til høyre →")
                        else:
                            st.code(output, language="text")
                    if msg.get("error"):
                        st.error(f"Feil: {msg['error']}")
                    if msg.get("question"):
                        st.info(f"🤔 {msg['question']}")
                    step_info = []
                    if msg.get("attempts") and msg["attempts"] > 1:
                        step_info.append(f"🔄 {msg['attempts']} forsøk")
                    if msg.get("steps") and msg["steps"] > 1:
                        step_info.append(f"📊 {msg['steps']} steg")
                    if step_info:
                        st.caption(" · ".join(step_info))
                    if msg.get("docs_used"):
                        with st.expander("📚 Dokumenter brukt"):
                            for d in msg["docs_used"]:
                                st.caption(f"• {d}")
                    if msg.get("thinking"):
                        with st.expander("🧠 Agentens tenkeprosess", expanded=False):
                            for t in msg["thinking"]:
                                step_n = t.get("step", "")
                                action = t.get("action", "")
                                detail = t.get("detail", "")
                                st.markdown(
                                    f"**Steg {step_n}** — {action}\n\n"
                                    f"<small style='color: #888'>{detail}</small>",
                                    unsafe_allow_html=True,
                                )

    # ---------------------------------------------------------------------------
    # Chat-input
    # ---------------------------------------------------------------------------

    # Sjekk om en detalj-forespørsel er trigget
    detail_query = st.session_state.pop("pa_detail_query", None)
    user_input = detail_query or st.chat_input("Beskriv hva du vil gjøre i PLAXIS…")

    if user_input:
        st.session_state.pa_messages.append({"role": "user", "content": user_input})

        # Forbered valgt kontekst
        selected_context_list = None
        if st.session_state.pa_selected:
            selected_context_list = []
            for sel in sorted(st.session_state.pa_selected):
                sec_name, item_text = sel.split("::", 1) if "::" in sel else ("", sel)
                selected_context_list.append(f"[{sec_name}] {item_text}")

        with st.spinner("Agenten tenker grundig… (kan ta flere steg)"):
            auto_exec = st.session_state.pa_auto_execute and st.session_state.pa_connected
            res = api.plaxis_agent_chat(
                message=user_input,
                session_id=st.session_state.pa_session_id,
                history=_build_history()[:-1],
                pdf_text=st.session_state.pa_pdf_text,
                auto_execute=auto_exec,
                selected_context=selected_context_list,
            )

        if "error" in res and not res.get("code"):
            st.session_state.pa_messages.append({
                "role": "assistant",
                "content": f"❌ {res['error']}",
            })
        else:
            code = res.get("code", "")
            output = res.get("output", "")
            error = res.get("error")
            attempts = res.get("attempts", 0)
            steps = res.get("steps", 1)
            docs_used = res.get("docs_used", [])
            question = res.get("question")
            thinking = res.get("thinking", [])

            # Oppdater funn-panelet med nye resultater
            if output:
                new_findings = _parse_findings(output)
                if new_findings:
                    st.session_state.pa_findings = new_findings

            st.session_state.pa_messages.append({
                "role": "assistant",
                "code": code,
                "output": output,
                "error": error,
                "attempts": attempts,
                "steps": steps,
                "docs_used": docs_used,
                "question": question,
                "thinking": thinking,
            })

        st.rerun()
