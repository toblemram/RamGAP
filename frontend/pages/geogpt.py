# -*- coding: utf-8 -*-
"""GeoGPT — AI-assistent for geoteknikk, basert på opplastede fagdokumenter."""

import requests
import streamlit as st
from components.api_client import APIClient
from components.auth import get_username

api = APIClient()
USERNAME = get_username()

# ------------------------------------------------------------------
# Scoped styling — all selectors prefixed to avoid leaking
# ------------------------------------------------------------------
st.markdown("""
<style>
/* ===== GeoGPT Page Styles ===== */

/* Header */
.geogpt-header {
    background: linear-gradient(135deg, #0f2b46 0%, #1565c0 60%, #1e88e5 100%);
    border-radius: 16px;
    padding: 28px 34px;
    color: #fff;
    margin-bottom: 24px;
    box-shadow: 0 4px 20px rgba(21,101,192,.18);
}
.geogpt-header h2 {
    margin: 0 0 4px 0;
    font-size: 1.6rem;
    font-weight: 700;
    letter-spacing: -.3px;
}
.geogpt-header p {
    margin: 0;
    opacity: .78;
    font-size: .9rem;
    font-weight: 400;
}

/* Welcome / empty state */
.geogpt-empty {
    text-align: center;
    padding: 56px 24px 32px;
}
.geogpt-empty-icon {
    width: 72px; height: 72px;
    margin: 0 auto 18px;
    background: linear-gradient(135deg, #e0edff 0%, #c7d9f7 100%);
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 2rem;
}
.geogpt-empty h4 {
    color: #1f2937;
    font-size: 1.2rem;
    font-weight: 600;
    margin: 0 0 8px;
}
.geogpt-empty p {
    color: #6b7280;
    font-size: .88rem;
    max-width: 440px;
    margin: 0 auto;
    line-height: 1.5;
}

/* Suggestion chips */
.geogpt-suggestions {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    justify-content: center;
    margin-top: 22px;
}
.geogpt-sug-btn {
    background: #f0f4ff;
    border: 1px solid #c7d2fe;
    border-radius: 22px;
    padding: 8px 18px;
    font-size: .83rem;
    color: #3730a3;
    cursor: pointer;
    transition: all .15s ease;
    text-decoration: none;
    font-weight: 500;
}
.geogpt-sug-btn:hover {
    background: #e0e7ff;
    border-color: #818cf8;
    transform: translateY(-1px);
    box-shadow: 0 2px 8px rgba(99,102,241,.12);
}

/* Source cards inside chat */
.geogpt-source-card {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 10px 14px;
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    margin-bottom: 6px;
    transition: border-color .15s;
}
.geogpt-source-card:hover {
    border-color: #93c5fd;
}
.geogpt-source-icon {
    flex-shrink: 0;
    width: 34px; height: 34px;
    background: #eff6ff;
    border-radius: 8px;
    display: flex; align-items: center; justify-content: center;
    font-size: .95rem;
}
.geogpt-source-title {
    font-size: .85rem;
    font-weight: 600;
    color: #1e293b;
    line-height: 1.3;
}

/* Admin cards */
.geogpt-admin-card {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 16px;
}
.geogpt-admin-card h5 {
    margin: 0 0 4px;
    font-size: .95rem;
    color: #1e293b;
}
.geogpt-admin-card p {
    margin: 0;
    font-size: .82rem;
    color: #64748b;
}

/* Status badge */
.geogpt-badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: .75rem;
    font-weight: 600;
    letter-spacing: .3px;
}
.geogpt-badge-ok   { background: #dcfce7; color: #166534; }
.geogpt-badge-warn { background: #fef3c7; color: #92400e; }
.geogpt-badge-err  { background: #fee2e2; color: #991b1b; }

/* Document list */
.geogpt-doc-row {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 10px 14px;
    border-bottom: 1px solid #f1f5f9;
    transition: background .1s;
}
.geogpt-doc-row:hover { background: #f8fafc; }
.geogpt-doc-row:last-child { border-bottom: none; }
.geogpt-doc-name {
    flex: 1;
    font-size: .88rem;
    font-weight: 500;
    color: #1e293b;
}
.geogpt-doc-size {
    font-size: .78rem;
    color: #94a3b8;
    font-weight: 400;
}

/* Clear chat */
.geogpt-clear-row {
    display: flex;
    justify-content: center;
    padding: 8px 0 0;
}
</style>
""", unsafe_allow_html=True)


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------
def _render_sources(documents: list):
    """Render source citation cards for a set of documents."""
    if not documents:
        return
    with st.expander(f"📎 {len(documents)} kilde(r) brukt", expanded=False):
        for doc in documents:
            title = doc.get("title", "Ukjent dokument")
            dl_url = doc.get("download_url", "")
            c1, c2 = st.columns([8, 1])
            c1.markdown(
                f'<div class="geogpt-source-card">'
                f'<div class="geogpt-source-icon">📄</div>'
                f'<span class="geogpt-source-title">{title}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
            if dl_url:
                c2.link_button("⬇️", f"{api.base_url}{dl_url}", use_container_width=True)


def _send_message(question: str) -> dict:
    """Send a message to the GeoGPT backend with conversation history."""
    history = [
        {"role": m["role"], "content": m["content"]}
        for m in st.session_state.geogpt_messages
        if m["role"] in ("user", "assistant")
    ]
    return api._post(
        "/api/geogpt/chat",
        payload={"question": question, "history": history},
        timeout=120,
    )


# ------------------------------------------------------------------
# Header
# ------------------------------------------------------------------
st.markdown(
    '<div class="geogpt-header">'
    "<h2>🤖 GeoGPT</h2>"
    "<p>AI-assistent for geoteknikk — svarene hentes fra opplastede fagdokumenter</p>"
    "</div>",
    unsafe_allow_html=True,
)

# ------------------------------------------------------------------
# Admin check
# ------------------------------------------------------------------
@st.cache_data(ttl=60)
def _check_admin(username: str) -> bool:
    result = api._get("/api/geogpt/admin-check", params={"username": username})
    return result.get("is_admin", False)

is_admin = _check_admin(USERNAME)

tab_labels = ["💬 Chat"]
if is_admin:
    tab_labels.append("⚙️ Administrer")

tabs = st.tabs(tab_labels)

# ------------------------------------------------------------------
# TAB 1 — Chat
# ------------------------------------------------------------------
with tabs[0]:
    if "geogpt_messages" not in st.session_state:
        st.session_state.geogpt_messages = []

    msgs = st.session_state.geogpt_messages

    # Accept new input from the chat box (renders pinned to bottom of tab)
    new_input = st.chat_input("Still et spørsmål om geoteknikk …")
    if new_input:
        msgs.append({"role": "user", "content": new_input})
        st.rerun()

    # Detect if last message is an unanswered user question
    needs_response = bool(msgs) and msgs[-1]["role"] == "user"

    # ---- Scrollable chat window ----
    chat_box = st.container(height=500)

    with chat_box:
        if not msgs:
            # ---- Welcome / empty state ----
            st.markdown(
                '<div class="geogpt-empty">'
                '<div class="geogpt-empty-icon">🧠</div>'
                "<h4>Hva kan jeg hjelpe deg med?</h4>"
                "<p>Still et faglig spørsmål, så søker jeg gjennom dokumentene "
                "og gir deg et presist svar med kildehenvisninger.</p>"
                "</div>",
                unsafe_allow_html=True,
            )

            suggestions = [
                "Krav til grunnundersøkelser etter Eurocode 7",
                "Hvordan beregnes pælenes bæreevne?",
                "Hva er kravene for kvikkleire-soner?",
            ]
            cols = st.columns(len(suggestions))
            for i, (col, sug) in enumerate(zip(cols, suggestions)):
                if col.button(sug, key=f"geogpt_sug_{i}", use_container_width=True):
                    msgs.append({"role": "user", "content": sug})
                    st.rerun()
        else:
            # ---- Render message history ----
            for msg in msgs:
                is_user = msg["role"] == "user"
                with st.chat_message(msg["role"], avatar="🧑‍💻" if is_user else "🤖"):
                    st.markdown(msg["content"])
                    if not is_user and msg.get("documents"):
                        _render_sources(msg["documents"])

            # ---- Generate response for pending question ----
            if needs_response:
                question = msgs[-1]["content"]
                with st.chat_message("assistant", avatar="🤖"):
                    with st.spinner("Søker i dokumentene …"):
                        result = _send_message(question)

                    if "error" in result:
                        answer = "Beklager, noe gikk galt. Prøv igjen om litt."
                        st.error(answer)
                        if is_admin:
                            st.caption(f"Feildetaljer: {result['error']}")
                        msgs.append({"role": "assistant", "content": answer})
                    else:
                        answer = result.get("answer", "Ingen svar funnet.")
                        st.markdown(answer)

                        documents = result.get("documents", [])
                        search_err = result.get("search_error")

                        if documents:
                            _render_sources(documents)
                        elif search_err and is_admin:
                            st.caption(f"⚠️ Søkproblem: {search_err}")
                        elif not result.get("ai_powered"):
                            st.info(
                                "Ingen dokumenter er indeksert ennå. "
                                "Last opp dokumenter i **Administrer**-fanen."
                            )

                        msgs.append({
                            "role": "assistant",
                            "content": answer,
                            "documents": documents,
                        })

    # ---- Clear chat (below the chat window) ----
    if msgs:
        if st.button("🗑️ Tøm samtale", key="geogpt_clear"):
            st.session_state.geogpt_messages = []
            st.rerun()


# ------------------------------------------------------------------
# TAB 2 — Admin (only shown for admins)
# ------------------------------------------------------------------
if is_admin:
    with tabs[1]:
        admin_tabs = st.tabs(["📄 Dokumenter", "🔍 Søkeindeks"])

        # === Dokumenter ===
        with admin_tabs[0]:
            st.markdown(
                '<div class="geogpt-admin-card">'
                "<h5>📤 Last opp fagdokumenter</h5>"
                "<p>PDF, Word og tekstfiler lastes opp til Azure Blob Storage "
                "og gjøres søkbare via AI Search.</p>"
                "</div>",
                unsafe_allow_html=True,
            )

            with st.form("geogpt_upload", clear_on_submit=True):
                uploaded_files = st.file_uploader(
                    "Velg filer",
                    accept_multiple_files=True,
                    type=["pdf", "docx", "txt", "md"],
                    label_visibility="collapsed",
                )
                upload_btn = st.form_submit_button("📤 Last opp", type="primary", use_container_width=True)

            if upload_btn and uploaded_files:
                progress = st.progress(0, text="Laster opp …")
                for idx, uf in enumerate(uploaded_files):
                    progress.progress(
                        (idx + 1) / len(uploaded_files),
                        text=f"Laster opp {uf.name} ({idx+1}/{len(uploaded_files)})",
                    )
                    try:
                        resp = requests.post(
                            f"{api.base_url}/api/geogpt/documents",
                            files={"file": (uf.name, uf.getvalue(), uf.type or "application/octet-stream")},
                            data={"username": USERNAME},
                            timeout=120,
                        )
                        r = resp.json()
                        if r.get("success"):
                            idx_msg = " — indeksering startet" if r.get("indexer_triggered") else ""
                            st.success(f"✅ {uf.name} lastet opp{idx_msg}")
                        else:
                            st.error(f"❌ {uf.name}: {r.get('error', 'Ukjent feil')}")
                    except Exception as e:
                        st.error(f"❌ {uf.name}: {e}")
                progress.empty()

            st.markdown("---")
            st.markdown("#### Dokumenter i kunnskapsbasen")

            docs_result = api._get("/api/geogpt/documents")
            docs_list = docs_result.get("documents", [])
            docs_err = docs_result.get("error", "")

            if docs_err and not docs_list:
                st.warning(f"⚠️ {docs_err}")
            elif not docs_list:
                st.info("Ingen dokumenter lastet opp ennå.")
            else:
                st.caption(f"{len(docs_list)} dokument(er) i kunnskapsbasen")
                for doc in docs_list:
                    dc1, dc2, dc3 = st.columns([6, 1, 1])
                    size_kb = round(doc.get("size", 0) / 1024, 1)
                    dc1.markdown(
                        f'<div class="geogpt-doc-row">'
                        f'<span>📄</span>'
                        f'<span class="geogpt-doc-name">{doc["name"]}</span>'
                        f'<span class="geogpt-doc-size">{size_kb} KB</span>'
                        f"</div>",
                        unsafe_allow_html=True,
                    )
                    if doc.get("download_url"):
                        dc2.link_button("⬇️", f"{api.base_url}{doc['download_url']}", use_container_width=True)
                    if dc3.button("🗑️", key=f"geogpt_del_{doc['name']}", use_container_width=True):
                        res = api._delete(
                            f"/api/geogpt/documents/{doc['name']}",
                            params={"username": USERNAME},
                        )
                        if res.get("success"):
                            st.success(f"✅ {doc['name']} slettet")
                            st.rerun()
                        else:
                            st.error(f"Feil: {res.get('error')}")

        # === Søkeindeks ===
        with admin_tabs[1]:
            st.markdown("#### Søkeindeks — status")

            status_r = api._get("/api/geogpt/index/status", params={"username": USERNAME})
            if not status_r.get("configured"):
                st.warning(
                    "Azure AI Search er ikke konfigurert.  \n"
                    "Fyll inn `AZURE_SEARCH_ENDPOINT` og `AZURE_SEARCH_KEY` i **.env** "
                    "og start backend på nytt."
                )
            else:
                run_status = status_r.get("status", "ukjent")
                last_run = status_r.get("last_run_status", "—")
                docs_ok = status_r.get("documents_succeeded", 0)
                errs = status_r.get("errors", 0)

                if "ikke satt opp" in run_status:
                    st.info("Søkeindeks er ikke satt opp ennå. Klikk **Sett opp indeks** nedenfor.")
                else:
                    m1, m2, m3 = st.columns(3)
                    badge = "geogpt-badge-ok" if run_status == "running" else "geogpt-badge-warn"
                    m1.metric("Status", run_status)
                    m2.metric("Siste kjøring", last_run or "—")
                    m3.metric("Indekserte dok.", docs_ok)
                    if status_r.get("last_run_time"):
                        st.caption(f"Sist kjørt: {status_r['last_run_time'][:19].replace('T', ' ')}")
                    if errs:
                        st.warning(f"⚠️ {errs} feil i siste kjøring")

            st.markdown("---")
            st.markdown(
                '<div class="geogpt-admin-card">'
                "<h5>🔧 Oppsett</h5>"
                "<p>Første gang: opprett indeks, datakilde og indexer i Azure AI Search. "
                "Deretter indekseres nye dokumenter automatisk hver 2. time.</p>"
                "</div>",
                unsafe_allow_html=True,
            )

            b1, b2 = st.columns(2)
            if b1.button("⚙️ Sett opp indeks", use_container_width=True, type="primary"):
                with st.spinner("Setter opp Azure AI Search …"):
                    res = api._post("/api/geogpt/index/setup", payload={"username": USERNAME})
                if res.get("success"):
                    st.success("✅ Indeks, datakilde og indexer er klare!")
                else:
                    st.error(f"❌ {res.get('error', 'Ukjent feil')}")

            if b2.button("▶️ Kjør indeksering nå", use_container_width=True):
                with st.spinner("Starter indeksering …"):
                    res = api._post("/api/geogpt/index/run", payload={"username": USERNAME})
                if res.get("success"):
                    st.success("✅ Indeksering startet! Dokumenter er søkbare om noen minutter.")
                else:
                    st.error(f"❌ {res.get('error', 'Ukjent feil')}")

            st.markdown("---")
            st.markdown("#### 🔍 Test søk")
            test_q = st.text_input("Søkeord", placeholder="f.eks. kvikkleire", key="geogpt_debug_q")
            if st.button("Søk", key="geogpt_debug_search", type="secondary"):
                if not test_q.strip():
                    st.warning("Skriv inn et søkeord først.")
                else:
                    with st.spinner("Søker …"):
                        res = api._get(
                            "/api/geogpt/search-debug",
                            params={"username": USERNAME, "q": test_q},
                        )
                    if res.get("error") and not res.get("endpoint"):
                        st.error(res["error"])
                    else:
                        st.caption(f"Indeks: `{res.get('index')}`")
                        if res.get("search_error"):
                            st.error(f"Søkfeil: {res['search_error']}")
                        elif res.get("results_count", 0) == 0:
                            st.info("Ingen treff.")
                        else:
                            st.success(f"{res['results_count']} treff")
                            for r in res.get("results", []):
                                title = r.get("title") or r.get("source", "?")
                                score = round(r.get("score", 0), 3)
                                st.markdown(f"- **{title}** — score {score}")
