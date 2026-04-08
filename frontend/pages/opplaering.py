# -*- coding: utf-8 -*-
"""Opplæring — kurs, quiz og opplæringsmateriell."""

import time
from datetime import timedelta

import pandas as pd
import streamlit as st

from components.api_client import APIClient
from components.auth import get_username

api = APIClient()
_USERNAME = get_username() or "Anonym"

st.title("🎓 Opplæring")

tab_overview, tab_quiz, tab_scoreboard = st.tabs(
    ["📚 Oversikt", "🧠 NS-EN 1997-1 Quiz", "🏆 Scoreboard"]
)

# ===================================================================
# Tab 1 — Oversikt
# ===================================================================
with tab_overview:
    st.markdown("---")
    st.info(
        "Kurs og opplæringsmateriell for bruk av RamGAP.\n\n"
        "_Innhold er under utvikling._"
    )
    st.markdown("#### Planlagte moduler")
    st.markdown("""
    - 🟢 Kom i gang med RamGAP  
    - 🔧 Plaxis-automatisering trinn for trinn  
    - 🗺️ GeoTolk — tolking av sonderinger  
    - 🤖 Bruk av GeoGPT  
    """)

# ===================================================================
# Quiz — NS-EN 1997-1:2004+A1:2013+NA:2025
# ===================================================================

QUESTIONS = [
    # --- Nivå 1: Lett (1-10) ---
    {
        "q": "Hva er det vanlige norske navnet på NS-EN 1997-1?",
        "a": "Eurokode 5 – Trekonstruksjoner",
        "b": "Eurokode 7 – Geoteknisk prosjektering",
        "c": "Eurokode 2 – Betongkonstruksjoner",
        "correct": "b",
    },
    {
        "q": "Hvor mange geotekniske kategorier (GK) defineres i NS-EN 1997-1?",
        "a": "2",
        "b": "4",
        "c": "3",
        "correct": "c",
    },
    {
        "q": "Hvilken geoteknisk kategori gjelder for enkle konstruksjoner med kjente grunnforhold?",
        "a": "Geoteknisk kategori 1",
        "b": "Geoteknisk kategori 2",
        "c": "Geoteknisk kategori 3",
        "correct": "a",
    },
    {
        "q": "Hva er hovedformålet med NS-EN 1997-1?",
        "a": "Dimensjonering av stålkonstruksjoner",
        "b": "Geoteknisk prosjektering av bygninger og anlegg",
        "c": "Beregning av vindlaster",
        "correct": "b",
    },
    {
        "q": "Hva står forkortelsen ULS for i Eurokode-sammenheng?",
        "a": "Ultimate Limit State (bruddgrensetilstand)",
        "b": "Uniform Load System",
        "c": "Upper Level Structure",
        "correct": "a",
    },
    {
        "q": "Hva står SLS for?",
        "a": "Structural Load System",
        "b": "Serviceability Limit State (bruksgrensetilstand)",
        "c": "Standard Loading Specification",
        "correct": "b",
    },
    {
        "q": "Hvilken norsk standard brukes sammen med NS-EN 1997-1 for geotekniske feltundersøkelser?",
        "a": "NS-EN 1997-2",
        "b": "NS-EN 1993-1",
        "c": "NS-EN 1992-1",
        "correct": "a",
    },
    {
        "q": "Hva er den norske nasjonale tilleggsbetegnelsen (NA) for NS-EN 1997-1?",
        "a": "NA:2020",
        "b": "NA:2025",
        "c": "NA:2015",
        "correct": "b",
    },
    {
        "q": "Hvilken grensetilstand omhandler tap av likevekt (f.eks. velting)?",
        "a": "STR",
        "b": "GEO",
        "c": "EQU",
        "correct": "c",
    },
    {
        "q": "Hva betyr grensetilstanden GEO?",
        "a": "Brudd i konstruksjonselementer",
        "b": "Brudd eller store deformasjoner i grunnen",
        "c": "Oppdrift og vanntrykk",
        "correct": "b",
    },
    # --- Nivå 2: Middels (11-20) ---
    {
        "q": "Hvilken dimensjoneringsmetode (DA) skal brukes i Norge iht. NA:2025?",
        "a": "Dimensjoneringsmetode 1 (DA1)",
        "b": "Dimensjoneringsmetode 2 (DA2)",
        "c": "Dimensjoneringsmetode 3 (DA3)",
        "correct": "c",
    },
    {
        "q": "I DA3: Hvor påføres partialfaktorene for laster?",
        "a": "På jordparametrene",
        "b": "På konstruksjonslaster (fra konstruksjonen) og på jordparametrene",
        "c": "Kun på materialmotstand",
        "correct": "b",
    },
    {
        "q": "Hva er partialfaktoren γφ' (friksjonsvinkel) for vedvarende og forbigående situasjoner i DA3 (NA:2025)?",
        "a": "1.0",
        "b": "1.25",
        "c": "1.40",
        "correct": "b",
    },
    {
        "q": "Hva er materialfaktoren γc' (effektiv kohesjon) i DA3 for vedvarende situasjoner?",
        "a": "1.25",
        "b": "1.40",
        "c": "1.0",
        "correct": "a",
    },
    {
        "q": "Hva er partialfaktoren γcu (udrenert skjærstyrke) i DA3?",
        "a": "1.0",
        "b": "1.25",
        "c": "1.40",
        "correct": "c",
    },
    {
        "q": "Hvilken grensetilstand gjelder for kontroll av hydraulisk grunnbrudd?",
        "a": "GEO",
        "b": "HYD",
        "c": "STR",
        "correct": "b",
    },
    {
        "q": "Hva er grensetilstanden UPL?",
        "a": "Tap av likevekt pga. vanntrykk (oppdrift)",
        "b": "Utmatting av fundamenter",
        "c": "Brudd i peler",
        "correct": "a",
    },
    {
        "q": "I NS-EN 1997-1, hva er «karakteristisk verdi» av en jordparameter?",
        "a": "Middelverdi fra laboratorieprøver",
        "b": "En forsiktig vurdering av verdien som påvirker grensetilstand",
        "c": "Den laveste målte verdien",
        "correct": "b",
    },
    {
        "q": "Hva krever NS-EN 1997-1 for geoteknisk kategori 3?",
        "a": "Forenklet beregning er tilstrekkelig",
        "b": "Supplerende undersøkelser og/eller beregninger utover GK2-krav",
        "c": "Ingen spesielle krav",
        "correct": "b",
    },
    {
        "q": "Hvilken faktor brukes for å redusere den karakteristiske friksjonsvinkel til dimensjonerende verdi i DA3?",
        "a": "tan(φ'd) = tan(φ'k) / γφ'",
        "b": "φ'd = φ'k × γφ'",
        "c": "φ'd = φ'k - γφ'",
        "correct": "a",
    },
    # --- Nivå 3: Vanskelig (21-30) ---
    {
        "q": "Hva er partialfaktoren γG for vedvarende belastende (unfavourable) permanente laster i STR/GEO (sett B i tabell NA.A1.2(B))?",
        "a": "1.0",
        "b": "1.35",
        "c": "1.20",
        "correct": "b",
    },
    {
        "q": "Hva er korreksjonsfaktoren ξ3 for karakteristisk pelekapasitet basert på statisk pelebelastningsprøve (n=1) iht. NA?",
        "a": "ξ3 = 1.0",
        "b": "ξ3 = 1.40",
        "c": "ξ3 = 1.55",
        "correct": "b",
    },
    {
        "q": "I DA3 for pelefundamenter: Skal partialfaktorer påføres på jordparametrene ELLER på pelekapasiteten?",
        "a": "På jordparametrene (som for grunne fundamenter)",
        "b": "På pelekapasiteten (modellpelemetoden med γt eller γs)",
        "c": "Begge deler samtidig",
        "correct": "b",
    },
    {
        "q": "Hva er den norske partialfaktoren γs for peleskaft-motstand (trykkpeler) i DA3?",
        "a": "1.0",
        "b": "1.15",
        "c": "1.30",
        "correct": "c",
    },
    {
        "q": "Hva er den norske partialfaktoren γb for pelespiss-motstand (trykkpeler) i DA3?",
        "a": "1.30",
        "b": "1.45",
        "c": "1.60",
        "correct": "a",
    },
    {
        "q": "Hva er kravet til minste innbyrdes avstand mellom friksjons­peler iht. NS-EN 1997-1 (generell anbefaling)?",
        "a": "Minimum pelediameter",
        "b": "Minimum 3 × pelediameter (senter-senter)",
        "c": "Minimum 5 × pelediameter",
        "correct": "b",
    },
    {
        "q": "Hva betyr «observasjonsmetoden» (Observational Method) i NS-EN 1997-1 seksjon 2.7?",
        "a": "Kontinuerlig overvåking som erstatter alle beregninger",
        "b": "En metode der prosjekteringen justeres under utførelsen basert på kontrollmålinger og forhåndsdefinerte kriterier",
        "c": "Bruk av erfaring fra tidligere prosjekter uten beregninger",
        "correct": "b",
    },
    {
        "q": "Ved beregning av jordtrykk mot støttemurer: Hva er Rankine-koeffisienten Ka for aktiv jordtrykk med friksjonsvinkel φ'?",
        "a": "Ka = (1 - sin φ') / (1 + sin φ')",
        "b": "Ka = tan²(45° + φ'/2)",
        "c": "Ka = 1 / (1 + sin φ')",
        "correct": "a",
    },
    {
        "q": "I NS-EN 1997-1 Annex D: Hvilken bæreevneformel brukes for grunne fundamenter?",
        "a": "Terzaghis formel",
        "b": "Analytisk metode med bæreevnefaktorene Nq, Nc og Nγ (basert på Hansen/Meyerhof)",
        "c": "Pressiometermetoden",
        "correct": "b",
    },
    {
        "q": "Hva er forholdet mellom Nq og friksjonsvinkel φ' i bæreevneberegning (Annex D)? Nq = ...",
        "a": "Nq = e^(π·tan φ') · tan²(45° + φ'/2)",
        "b": "Nq = (1 + sin φ') / (1 - sin φ')",
        "c": "Nq = tan²(45° + φ'/2) / cos²(φ')",
        "correct": "a",
    },
]

TIME_LIMIT = 30  # sekunder per spørsmål
_FB_DELAY_CORRECT = 1.5  # sekunder feedback ved riktig svar
_FB_DELAY_WRONG = 2.5  # sekunder feedback ved feil/timeout

# Compat: st.fragment (>=1.37) eller st.experimental_fragment (1.33–1.36)
_fragment = getattr(st, "fragment", None) or getattr(st, "experimental_fragment", None)


def _init_quiz():
    """Initialize or reset quiz session state."""
    st.session_state.quiz_phase = "active"
    st.session_state.quiz_index = 0
    st.session_state.quiz_score = 0
    st.session_state.quiz_answers = []
    st.session_state.quiz_q_start = time.time()
    st.session_state.quiz_streak = 0
    st.session_state.quiz_max_streak = 0
    # Rydd opp gammel state
    for _k in ("quiz_active", "quiz_finished"):
        st.session_state.pop(_k, None)


@st.cache_data(ttl=30)
def _fetch_scoreboard():
    """Hent scoreboard fra backend (cachet 30s)."""
    result = api.get_quiz_scores()
    if "error" in result:
        return [], []
    return result.get("top_scores", []), result.get("user_bests", [])


def _save_score_to_db(username: str, score: int, total: int, max_streak: int = 0):
    """Lagre score til backend-databasen."""
    result = api.save_quiz_score(
        username=username, score=score, total=total, max_streak=max_streak
    )
    if "error" not in result:
        _fetch_scoreboard.clear()
    return result


def _record_answer(idx: int, q: dict, choice: str):
    """Record the user's answer and move to feedback phase."""
    elapsed = time.time() - st.session_state.quiz_q_start
    if elapsed > TIME_LIMIT:
        st.session_state.quiz_answers.append({"answer": "—", "correct": False, "timeout": True})
        st.session_state.quiz_streak = 0
    else:
        is_correct = choice == q["correct"]
        st.session_state.quiz_answers.append({
            "answer": f"{choice.upper()}) {q[choice]}",
            "correct": is_correct,
            "timeout": False,
        })
        if is_correct:
            st.session_state.quiz_score += 1
            st.session_state.quiz_streak += 1
            st.session_state.quiz_max_streak = max(
                st.session_state.quiz_max_streak, st.session_state.quiz_streak
            )
        else:
            st.session_state.quiz_streak = 0
    st.session_state.quiz_phase = "feedback"
    st.session_state.quiz_feedback_start = time.time()


def _record_timeout(idx: int):
    """Record a timeout (only once per question)."""
    if len(st.session_state.quiz_answers) <= idx:
        st.session_state.quiz_answers.append({"answer": "—", "correct": False, "timeout": True})
        st.session_state.quiz_streak = 0
        st.session_state.quiz_phase = "feedback"
        st.session_state.quiz_feedback_start = time.time()


def _advance_question():
    """Move to the next question, or finish the quiz."""
    st.session_state.quiz_index += 1
    if st.session_state.quiz_index >= len(QUESTIONS):
        st.session_state.quiz_phase = "finished"
    else:
        st.session_state.quiz_phase = "active"
        st.session_state.quiz_q_start = time.time()


@_fragment(run_every=timedelta(seconds=1))
def _quiz_play():
    """Live-oppdaterende quiz-fragment — teller ned hvert sekund."""
    phase = st.session_state.quiz_phase
    idx = st.session_state.quiz_index
    total = len(QUESTIONS)

    # Sikkerhet: sjekk at vi ikke er forbi siste spørsmål
    if idx >= total:
        st.session_state.quiz_phase = "finished"
        st.rerun(scope="app")
        return

    q = QUESTIONS[idx]

    # --- Vanskelighetsgrad ---
    if idx < 10:
        diff_label = "🟢 Lett"
    elif idx < 20:
        diff_label = "🟡 Middels"
    else:
        diff_label = "🔴 Vanskelig"

    st.markdown(f"**Spørsmål {idx + 1} / {total}** — {diff_label}")
    st.progress((idx + 1) / total)

    # --- Score-rad ---
    answered_count = len(st.session_state.quiz_answers)
    c1, c2, c3 = st.columns(3)
    c1.metric("Score", f"{st.session_state.quiz_score} / {answered_count}")
    c2.metric("Streak", f"{st.session_state.quiz_streak} 🔥")

    # ===================== AKTIV FASE =====================
    if phase == "active":
        elapsed = time.time() - st.session_state.quiz_q_start
        remaining = max(0, TIME_LIMIT - elapsed)
        timed_out = remaining <= 0

        # Tidtaker
        if timed_out:
            c3.metric("Tid", "⏰ 0s")
        elif remaining > 15:
            c3.metric("Tid", f"🟢 {remaining:.0f}s")
        elif remaining > 5:
            c3.metric("Tid", f"🟡 {remaining:.0f}s")
        else:
            c3.metric("Tid", f"🔴 {remaining:.0f}s")

        st.progress(max(0.0, remaining / TIME_LIMIT))
        st.markdown("---")
        st.subheader(q["q"])

        if timed_out:
            _record_timeout(idx)
            st.rerun()
        else:
            # Svar-skjema (form bevarer tilstand under auto-refresh)
            with st.form(key=f"qf_{idx}"):
                choice = st.radio(
                    "Velg svar:",
                    options=["a", "b", "c"],
                    format_func=lambda x: f"{x.upper()}) {q[x]}",
                    index=None,
                    horizontal=True,
                )
                submitted = st.form_submit_button(
                    "Svar ✅", type="primary", use_container_width=True
                )
            if submitted:
                if choice is None:
                    st.warning("⚠️ Velg et svar først!")
                else:
                    _record_answer(idx, q, choice)
                    st.rerun()

    # ===================== FEEDBACK FASE =====================
    elif phase == "feedback":
        c3.metric("Tid", "—")
        st.markdown("---")
        st.subheader(q["q"])

        last = st.session_state.quiz_answers[-1]

        if last["timeout"]:
            st.error("⏰ Tiden gikk ut!")
            st.info(f"Riktig svar: **{q['correct'].upper()}) {q[q['correct']]}**")
        elif last["correct"]:
            st.success("✅ Riktig!")
        else:
            st.error(f"❌ Feil!  Ditt svar: {last['answer']}")
            st.info(f"Riktig svar: **{q['correct'].upper()}) {q[q['correct']]}**")

        # Auto-avansering etter kort forsinkelse, eller manuell «Neste»
        fb_elapsed = time.time() - st.session_state.quiz_feedback_start
        delay = _FB_DELAY_CORRECT if last.get("correct") else _FB_DELAY_WRONG

        if fb_elapsed >= delay:
            _advance_question()
            if st.session_state.quiz_phase == "finished":
                st.rerun(scope="app")
            else:
                st.rerun()
        else:
            remaining_fb = max(0, delay - fb_elapsed)
            st.caption(f"Neste spørsmål om {remaining_fb:.0f}s …")
            if st.button("Neste ➡️", type="primary", use_container_width=True):
                _advance_question()
                if st.session_state.quiz_phase == "finished":
                    st.rerun(scope="app")
                else:
                    st.rerun()


# ===================================================================
# Tab 2 — Quiz
# ===================================================================
with tab_quiz:
    st.header("🧠 NS-EN 1997-1 Quiz")
    st.caption("Test din kunnskap om Eurokode 7 – Geoteknisk prosjektering (NS-EN 1997-1:2004+A1:2013+NA:2025)")

    phase = st.session_state.get("quiz_phase", "start")

    # --- Startskjerm ---
    if phase == "start":
        st.markdown("""
        **Regler:**
        - 30 spørsmål med 3 alternativer (A, B, C)
        - ⏱️ 30 sekunder per spørsmål
        - Spørsmålene blir vanskeligere etter hvert
        - 🟢 1–10: Lett  |  🟡 11–20: Middels  |  🔴 21–30: Vanskelig
        """)
        st.info(f"Du er logget inn som **{_USERNAME}**. Scoren din lagres automatisk på scoreboardet.")
        if st.button("🚀 Start quiz!", type="primary", use_container_width=True):
            _init_quiz()
            st.rerun()

    # --- Aktiv quiz (live fragment) ---
    elif phase in ("active", "feedback"):
        _quiz_play()

    # --- Resultatskjerm ---
    elif phase == "finished":
        score = st.session_state.quiz_score
        total = len(QUESTIONS)
        pct = score / total * 100
        streak = st.session_state.quiz_max_streak

        st.markdown("## 🏁 Quiz ferdig!")

        c1, c2, c3 = st.columns(3)
        c1.metric("Score", f"{score}/{total}")
        c2.metric("Prosent", f"{pct:.0f}%")
        c3.metric("Lengste streak", f"{streak} 🔥")

        if pct >= 90:
            st.success("🌟 Fantastisk! Du er en Eurokode 7-ekspert!")
        elif pct >= 70:
            st.success("👏 Veldig bra! Solid forståelse av NS-EN 1997-1.")
        elif pct >= 50:
            st.info("📖 Bra forsøk — les opp litt mer og prøv igjen!")
        else:
            st.warning("💪 Tid for å studere NS-EN 1997-1 litt grundigere!")

        with st.expander("📋 Se alle svar", expanded=False):
            for i, ans in enumerate(st.session_state.quiz_answers):
                q = QUESTIONS[i]
                diff = "🟢" if i < 10 else ("🟡" if i < 20 else "🔴")
                icon = "✅" if ans["correct"] else ("⏰" if ans.get("timeout") else "❌")
                st.markdown(f"{diff} **{i+1}.** {q['q']}")
                st.markdown(
                    f"&nbsp;&nbsp;&nbsp;&nbsp;{icon} Ditt svar: **{ans['answer']}** — "
                    f"Riktig: **{q['correct'].upper()}) {q[q['correct']]}**"
                )
                if ans.get("timeout"):
                    st.markdown("&nbsp;&nbsp;&nbsp;&nbsp;_⏰ Tiden gikk ut_")

        # Auto-lagre score til DB (kun én gang per forsøk)
        if not st.session_state.get("quiz_score_saved"):
            result = _save_score_to_db(_USERNAME, score, total, streak)
            if "error" not in result:
                st.session_state.quiz_score_saved = True
                st.success(f"💾 Score lagret for **{_USERNAME}**!")
            else:
                st.warning(f"Kunne ikke lagre score: {result.get('error', 'ukjent feil')}")
        else:
            st.success(f"💾 Score lagret for **{_USERNAME}**!")

        st.markdown("---")
        if st.button("🔄 Prøv igjen", type="primary", use_container_width=True):
            st.session_state.quiz_phase = "start"
            st.session_state.pop("quiz_score_saved", None)
            st.rerun()

# ===================================================================
# Tab 3 — Scoreboard
# ===================================================================
with tab_scoreboard:
    st.header("🏆 Scoreboard")

    top_scores, user_bests = _fetch_scoreboard()

    if st.button("🔄 Oppdater", key="refresh_sb"):
        _fetch_scoreboard.clear()
        st.rerun()

    if not top_scores and not user_bests:
        st.info("Ingen scores registrert ennå. Fullfør quizen for å komme på scoreboardet!")
    else:
        # --- Per-bruker beste score ---
        st.subheader("👤 Beste score per bruker")
        if user_bests:
            for i, entry in enumerate(user_bests):
                medal = ["🥇", "🥈", "🥉"][i] if i < 3 else f"**{i+1}.**"
                streak_txt = f" | 🔥 {entry['max_streak']}" if entry.get("max_streak") else ""
                ts = entry.get("created_at", "")[:10]
                st.markdown(
                    f"{medal} **{entry['username']}** — "
                    f"**{entry['score']}/{entry['total']}** ({entry['pct']:.0f}%)"
                    f"{streak_txt} — {ts}"
                )
        else:
            st.caption("Ingen data ennå.")

        st.markdown("---")

        # --- Alle forsøk (tabell) ---
        st.subheader("📊 Alle forsøk")
        if top_scores:
            df = pd.DataFrame(top_scores)
            df = df.rename(columns={
                "username": "Bruker",
                "score": "Riktige",
                "total": "Totalt",
                "pct": "Prosent (%)",
                "max_streak": "Streak 🔥",
                "created_at": "Tidspunkt",
            })
            df = df[["Bruker", "Riktige", "Totalt", "Prosent (%)", "Streak 🔥", "Tidspunkt"]]
            df["Tidspunkt"] = df["Tidspunkt"].str[:16].str.replace("T", " ")
            st.dataframe(df, use_container_width=True, hide_index=True)
