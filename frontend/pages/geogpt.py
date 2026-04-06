# -*- coding: utf-8 -*-
"""GeoGPT — AI-assistent for geoteknikk, basert på opplastede fagdokumenter."""

import requests
import streamlit as st
from components.api_client import APIClient
from components.auth import get_username

api = APIClient()
USERNAME = get_username()

# ------------------------------------------------------------------
# Custom styling
# ------------------------------------------------------------------
st.markdown("""
<style>
/* ---- Header banner ---- */
.geogpt-banner {
    background: linear-gradient(135deg, #1b3a5c 0%, #1565c0 100%);
    border-radius: 14px;
    padding: 26px 32px;
    color: white;
    margin-bottom: 20px;
}
.geogpt-banner h2 {
    margin: 0 0 6px 0;
    font-size: 1.65rem;
    font-weight: 700;
    letter-spacing: -0.3px;
}
.geogpt-banner p {
    margin: 0;
    opacity: 0.82;
    font-size: 0.93rem;
}

/* ---- Welcome / empty state ---- */
.geogpt-welcome {
    text-align: center;
    padding: 48px 20px 28px;
    color: #6b7280;
}
.geogpt-welcome .icon { font-size: 3.2rem; margin-bottom: 14px; }
.geogpt-welcome h4 { color: #1f2937; font-size: 1.15rem; margin-bottom: 8px; }
.geogpt-welcome p  { font-size: 0.88rem; max-width: 420px; margin: 0 auto; }

/* ---- Source expander ---- */
[data-testid="stExpander"] {
    border: 1px solid #e5eaf0 !important;
    border-radius: 10px !important;
    background: #f9fafb !important;
    margin-top: 8px !important;
}

/* ---- Chat input ---- */
[data-testid="stChatInput"] textarea {
    border-radius: 12px !important;
    font-size: 0.94rem !important;
}

/* ---- Suggestion buttons ---- */
div[data-testid="column"] .stButton > button {
    border-radius: 20px;
    font-size: 0.82rem;
    background: #eef2ff;
    border: 1px solid #c7d2fe;
    color: #3730a3;
    padding: 6px 12px;
}
div[data-testid="column"] .stButton > button:hover {
    background: #e0e7ff;
    border-color: #818cf8;
}
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------
# Header
# ------------------------------------------------------------------
st.markdown("""
<div class="geogpt-banner">
    <h2>🤖 GeoGPT</h2>
    <p>AI-assistent for geoteknikk &mdash; svarene hentes direkte fra opplastede fagdokumenter.</p>
</div>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------
# Admin check
# ------------------------------------------------------------------
@st.cache_data(ttl=60)
def _check_admin(username: str) -> bool:
    result = api._get('/api/geogpt/admin-check', params={'username': username})
    return result.get('is_admin', False)

is_admin = _check_admin(USERNAME)

tab_labels = ["💬 Chat"]
if is_admin:
    tab_labels.append("⚙️ Administrer")

tabs = st.tabs(tab_labels)

# ------------------------------------------------------------------
# TAB 1: Chat
# ------------------------------------------------------------------
with tabs[0]:
    if "geogpt_messages" not in st.session_state:
        st.session_state.geogpt_messages = []

    # Empty state — welcome screen with clickable suggestions
    if not st.session_state.geogpt_messages:
        st.markdown("""
        <div class="geogpt-welcome">
            <div class="icon">💬</div>
            <h4>Hva kan jeg hjelpe deg med?</h4>
            <p>Still et faglig spørsmål og jeg søker i kunnskapsbasen din for å gi deg et presist svar.</p>
        </div>
        """, unsafe_allow_html=True)

        suggestions = [
            "Krav til grunnundersøkelser etter Eurocode 7",
            "Hvordan beregnes pælenes bæreevne?",
            "Krav for kvikkleire-soner?",
        ]
        cols = st.columns(len(suggestions))
        for i, (col, sug) in enumerate(zip(cols, suggestions)):
            if col.button(sug, key=f"sug_{i}", use_container_width=True):
                st.session_state.geogpt_messages.append({"role": "user", "content": sug})
                st.rerun()

        st.markdown("<div style='margin-bottom:24px'></div>", unsafe_allow_html=True)

    # Chat history
    for msg in st.session_state.geogpt_messages:
        avatar = "🧑‍💻" if msg["role"] == "user" else "🤖"
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])
            if msg.get("documents"):
                with st.expander(f"📎 {len(msg['documents'])} kilde(r) brukt", expanded=False):
                    for doc in msg["documents"]:
                        c1, c2 = st.columns([6, 1])
                        c1.markdown(f"📄 **{doc['title']}**")
                        if doc.get("download_url"):
                            c2.link_button("⬇️", f"{api.base_url}{doc['download_url']}", use_container_width=True)

    # Input
    if prompt := st.chat_input("Still et faglig spørsmål om geoteknikk..."):
        st.session_state.geogpt_messages.append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar="🧑‍💻"):
            st.markdown(prompt)

        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("Søker i kunnskapsbasen..."):
                result = api._post('/api/geogpt/chat', payload={'question': prompt})

            if 'error' in result:
                err_detail = result.get('error', 'Ukjent feil')
                answer_text = "Beklager, noe gikk galt med GeoGPT."
                st.error(answer_text)
                st.warning(f"**Feildetaljer:** {err_detail}")
                st.caption(f"Backend-URL: `{api.base_url}`")
                st.session_state.geogpt_messages.append({"role": "assistant", "content": f"{answer_text}\n\n_Feil: {err_detail}_"})
            else:
                answer_text = result.get('answer', 'Ingen svar funnet.')
                st.markdown(answer_text)

                documents = result.get('documents', [])
                search_err = result.get('search_error')
                if documents:
                    with st.expander(f"📎 {len(documents)} kilde(r) brukt", expanded=False):
                        for doc in documents:
                            c1, c2 = st.columns([6, 1])
                            c1.markdown(f"📄 **{doc['title']}**")
                            if doc.get("download_url"):
                                c2.link_button("⬇️", f"{api.base_url}{doc['download_url']}", use_container_width=True)
                elif search_err:
                    st.warning(f"⚠️ Søk feilet: {search_err}")
                elif not result.get('ai_powered'):
                    st.caption("💡 Ingen dokumenter indeksert ennå. Last opp dokumenter i Administrer-fanen.")

                st.session_state.geogpt_messages.append({
                    "role": "assistant",
                    "content": answer_text,
                    "documents": documents,
                })

    # Clear chat button
    if st.session_state.geogpt_messages:
        st.divider()
        _, col_btn, _ = st.columns([4, 2, 4])
        if col_btn.button("🗑️ Tøm chat", key="clear_chat", use_container_width=True):
            st.session_state.geogpt_messages = []
            st.rerun()

# ------------------------------------------------------------------
# TAB 2: Admin (only shown for admins)
# ------------------------------------------------------------------
if is_admin:
    with tabs[1]:
        st.subheader("⚙️ Administrer GeoGPT")
        admin_tabs = st.tabs(["📄 Dokumenter", "🔍 Søkeindeks"])

        # ---- Dokumenter ----
        with admin_tabs[0]:
            st.markdown("#### Last opp fagdokumenter")
            st.caption("PDF, Word og tekstfiler lastes opp til Azure Blob Storage og gjøres søkbare via AI Search.")

            with st.form("upload_docs", clear_on_submit=True):
                uploaded_files = st.file_uploader(
                    "Velg filer",
                    accept_multiple_files=True,
                    type=["pdf", "docx", "txt", "md"],
                )
                upload_btn = st.form_submit_button("📤 Last opp", type="primary")

            if upload_btn and uploaded_files:
                for uf in uploaded_files:
                    with st.spinner(f"Laster opp {uf.name}..."):
                        try:
                            resp = requests.post(
                                f"{api.base_url}/api/geogpt/documents",
                                files={"file": (uf.name, uf.getvalue(), uf.type or "application/octet-stream")},
                                data={"username": USERNAME},
                                timeout=120,
                            )
                            r = resp.json()
                            if r.get("success"):
                                idx = " (indeksering startet ⏳)" if r.get("indexer_triggered") else ""
                                st.success(f"✅ {uf.name} lastet opp{idx}")
                            else:
                                st.error(f"❌ {uf.name}: {r.get('error', 'Ukjent feil')}")
                        except Exception as e:
                            st.error(f"❌ {uf.name}: {e}")

            st.divider()
            st.markdown("#### Dokumenter i kunnskapsbasen")
            docs_result = api._get('/api/geogpt/documents')
            docs_list = docs_result.get('documents', [])
            docs_err = docs_result.get('error', '')

            if docs_err and not docs_list:
                st.warning(f"⚠️ {docs_err}")
            elif not docs_list:
                st.info("Ingen dokumenter lastet opp ennå.")
            else:
                st.caption(f"{len(docs_list)} dokument(er)")
                for doc in docs_list:
                    dc1, dc2, dc3 = st.columns([5, 1, 1])
                    size_kb = round(doc.get('size', 0) / 1024, 1)
                    dc1.markdown(f"📄 **{doc['name']}** &nbsp; `{size_kb} KB`")
                    if doc.get('download_url'):
                        dc2.link_button("⬇️", f"{api.base_url}{doc['download_url']}", use_container_width=True)
                    if dc3.button("🗑️", key=f"del_doc_{doc['name']}", use_container_width=True):
                        res = api._delete(f"/api/geogpt/documents/{doc['name']}",
                                          params={'username': USERNAME})
                        if res.get('success'):
                            st.success(f"✅ {doc['name']} slettet")
                            st.rerun()
                        else:
                            st.error(f"Feil: {res.get('error')}")

        # ---- Søkeindeks ----
        with admin_tabs[1]:
            st.markdown("#### Azure AI Search — status")

            status_r = api._get('/api/geogpt/index/status', params={'username': USERNAME})
            if not status_r.get('configured'):
                st.warning(
                    "⚠️ Azure AI Search er ikke konfigurert.\n\n"
                    "Fyll inn `AZURE_SEARCH_ENDPOINT` og `AZURE_SEARCH_KEY` i `.env` "
                    "og start backend på nytt."
                )
            else:
                run_status = status_r.get('status', '?')
                last_run   = status_r.get('last_run_status', '—')
                docs_ok    = status_r.get('documents_succeeded', 0)
                errs       = status_r.get('errors', 0)

                if 'ikke satt opp' in run_status:
                    st.info("ℹ️ Søkeindeks er ikke satt opp ennå. Klikk 'Sett opp indeks' nedenfor.")
                else:
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Indexer-status", run_status)
                    c2.metric("Siste kjøring", last_run or '—')
                    c3.metric("Indekserte dok.", docs_ok)
                    if status_r.get('last_run_time'):
                        st.caption(f"Sist kjørt: {status_r['last_run_time'][:19].replace('T', ' ')}")
                    if errs:
                        st.warning(f"⚠️ {errs} feil i siste kjøring")

            st.divider()
            st.caption(
                "🔧 **Første gang**: Klikk 'Sett opp indeks' for å opprette indeks, datakilde og indexer i Azure AI Search.\n"
                "Deretter indekseres nye dokumenter automatisk hver 2. time."
            )
            btn1, btn2 = st.columns(2)
            if btn1.button("⚙️ Sett opp indeks (første gang)", use_container_width=True, type="primary"):
                with st.spinner("Setter opp Azure AI Search..."):
                    res = api._post('/api/geogpt/index/setup', payload={'username': USERNAME})
                if res.get('success'):
                    st.success("✅ Indeks, datakilde og indexer er klare!")
                    st.json(res.get('results', {}))
                else:
                    st.error(f"❌ {res.get('error', 'Ukjent feil')}")

            if btn2.button("▶️ Kjør indeksering nå", use_container_width=True):
                with st.spinner("Starter indeksering..."):
                    res = api._post('/api/geogpt/index/run', payload={'username': USERNAME})
                if res.get('success'):
                    st.success("✅ Indeksering startet! Nye dokumenter er søkbare om noen minutter.")
                else:
                    st.error(f"❌ {res.get('error', 'Ukjent feil')}")

            st.divider()
            st.markdown("#### Test søk")
            test_q = st.text_input("Søkeord", placeholder="f.eks. kvikkleire", key="debug_q")
            if st.button("🔍 Test søk mot Azure AI Search", key="debug_search"):
                res = api._get('/api/geogpt/search-debug', params={'username': USERNAME, 'q': test_q or 'test'})
                if res.get('error') and not res.get('endpoint'):
                    st.error(res['error'])
                else:
                    st.caption(f"Endepunkt: `{res.get('endpoint')}` | Indeks: `{res.get('index')}`")
                    if res.get('search_error'):
                        st.error(f"❌ Søkfeil: {res['search_error']}")
                    else:
                        st.success(f"✅ {res.get('results_count', 0)} treff")
                        for r in res.get('results', []):
                            st.markdown(f"- **{r.get('title') or r.get('source', '?')}** (score: {round(r.get('score', 0), 3)})")
