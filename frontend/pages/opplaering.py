# -*- coding: utf-8 -*-
"""Opplæring — kurs, quiz og opplæringsmateriell."""

import time
import streamlit as st

st.title("🎓 Opplæring")

tab_overview, tab_quiz = st.tabs(["📚 Oversikt", "🧠 NS-EN 1997-1 Quiz"])

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


def _init_quiz_state():
    """Initialize or reset quiz session state."""
    st.session_state.quiz_active = True
    st.session_state.quiz_index = 0
    st.session_state.quiz_score = 0
    st.session_state.quiz_answers = []
    st.session_state.quiz_q_start = time.time()
    st.session_state.quiz_finished = False
    st.session_state.quiz_streak = 0
    st.session_state.quiz_max_streak = 0


def _get_highscores() -> list[dict]:
    return st.session_state.get("quiz_highscores", [])


def _save_highscore(name: str, score: int, total: int, pct: float):
    hs = _get_highscores()
    hs.append({"name": name, "score": score, "total": total, "pct": pct, "time": time.strftime("%Y-%m-%d %H:%M")})
    hs.sort(key=lambda x: (-x["pct"], -x["score"]))
    st.session_state.quiz_highscores = hs[:20]  # keep top 20


with tab_quiz:
    st.header("🧠 NS-EN 1997-1 Quiz")
    st.caption("Test din kunnskap om Eurokode 7 – Geoteknisk prosjektering (NS-EN 1997-1:2004+A1:2013+NA:2025)")

    # --- Start / Reset ---
    if not st.session_state.get("quiz_active") and not st.session_state.get("quiz_finished"):
        st.markdown("""
        **Regler:**
        - 30 spørsmål med 3 alternativer (A, B, C)
        - ⏱️ 30 sekunder per spørsmål
        - Spørsmålene blir vanskeligere etter hvert
        - 🟢 Spørsmål 1–10: Lett  |  🟡 11–20: Middels  |  🔴 21–30: Vanskelig
        """)
        col_start, col_hs = st.columns(2)
        with col_start:
            if st.button("🚀 Start quiz!", type="primary", use_container_width=True):
                _init_quiz_state()
                st.rerun()
        with col_hs:
            hs = _get_highscores()
            if hs:
                st.markdown("#### 🏆 Highscores")
                for i, entry in enumerate(hs[:10]):
                    medal = ["🥇", "🥈", "🥉"][i] if i < 3 else f"**{i+1}.**"
                    st.markdown(f"{medal} **{entry['name']}** — {entry['score']}/{entry['total']} ({entry['pct']:.0f}%) — {entry['time']}")

    # --- Quiz finished ---
    elif st.session_state.get("quiz_finished"):
        score = st.session_state.quiz_score
        total = len(QUESTIONS)
        pct = score / total * 100
        streak = st.session_state.quiz_max_streak

        st.markdown("---")
        st.markdown("## 🏁 Quiz ferdig!")

        # Score display
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Score", f"{score}/{total}")
        with c2:
            st.metric("Prosent", f"{pct:.0f}%")
        with c3:
            st.metric("Lengste streak", f"{streak} 🔥")

        # Rating
        if pct >= 90:
            st.success("🌟 Fantastisk! Du er en Eurokode 7-ekspert!")
        elif pct >= 70:
            st.success("👏 Veldig bra! Solid forståelse av NS-EN 1997-1.")
        elif pct >= 50:
            st.info("📖 Bra forsøk — les opp litt mer og prøv igjen!")
        else:
            st.warning("💪 Tid for å studere NS-EN 1997-1 litt grundigere!")

        # Review answers
        with st.expander("📋 Se alle svar", expanded=False):
            for i, ans in enumerate(st.session_state.quiz_answers):
                q = QUESTIONS[i]
                difficulty = "🟢" if i < 10 else ("🟡" if i < 20 else "🔴")
                icon = "✅" if ans["correct"] else ("⏰" if ans.get("timeout") else "❌")
                st.markdown(f"{difficulty} **{i+1}.** {q['q']}")
                st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;{icon} Ditt svar: **{ans['answer']}** — Riktig: **{q['correct'].upper()}) {q[q['correct']]}**")
                if ans.get("timeout"):
                    st.markdown("&nbsp;&nbsp;&nbsp;&nbsp;_⏰ Tiden gikk ut_")
                st.markdown("")

        # Save highscore
        st.markdown("---")
        hs_name = st.text_input("Ditt navn for highscore-listen:", key="hs_name_input",
                                placeholder="Skriv inn navnet ditt")
        c_save, c_retry = st.columns(2)
        with c_save:
            if st.button("💾 Lagre score", use_container_width=True):
                name = hs_name.strip() or "Anonym"
                _save_highscore(name, score, total, pct)
                st.success(f"Score lagret for {name}!")
        with c_retry:
            if st.button("🔄 Prøv igjen", type="primary", use_container_width=True):
                st.session_state.quiz_active = False
                st.session_state.quiz_finished = False
                st.rerun()

        # Show highscores
        hs = _get_highscores()
        if hs:
            st.markdown("---")
            st.markdown("#### 🏆 Highscores")
            for i, entry in enumerate(hs[:10]):
                medal = ["🥇", "🥈", "🥉"][i] if i < 3 else f"**{i+1}.**"
                st.markdown(f"{medal} **{entry['name']}** — {entry['score']}/{entry['total']} ({entry['pct']:.0f}%) — {entry['time']}")

    # --- Active quiz ---
    elif st.session_state.get("quiz_active"):
        idx = st.session_state.quiz_index
        total = len(QUESTIONS)

        if idx >= total:
            st.session_state.quiz_finished = True
            st.session_state.quiz_active = False
            st.rerun()

        q = QUESTIONS[idx]
        elapsed = time.time() - st.session_state.quiz_q_start
        remaining = max(0, TIME_LIMIT - elapsed)
        timed_out = remaining <= 0

        # Difficulty indicator
        if idx < 10:
            diff_label = "🟢 Lett"
        elif idx < 20:
            diff_label = "🟡 Middels"
        else:
            diff_label = "🔴 Vanskelig"

        # Header
        st.markdown(f"**Spørsmål {idx + 1}/{total}** — {diff_label}")
        st.progress(min((idx + 1) / total, 1.0))

        # Score so far
        sc1, sc2, sc3 = st.columns(3)
        with sc1:
            st.metric("Score", f"{st.session_state.quiz_score}/{idx}")
        with sc2:
            st.metric("Streak", f"{st.session_state.quiz_streak} 🔥")
        with sc3:
            if not timed_out:
                color = "🟢" if remaining > 15 else ("🟡" if remaining > 5 else "🔴")
                st.metric("Tid igjen", f"{color} {remaining:.0f}s")
            else:
                st.metric("Tid igjen", "🔴 0s")

        # Timer bar
        pct_remaining = remaining / TIME_LIMIT * 100
        bar_color = "#4caf50" if remaining > 15 else ("#ff9800" if remaining > 5 else "#f44336")
        st.markdown(
            f'<div style="background:#e0e0e0;border-radius:4px;height:8px;margin-bottom:16px;">'
            f'<div style="background:{bar_color};width:{pct_remaining:.1f}%;height:8px;border-radius:4px;'
            f'transition:width 1s linear;"></div></div>',
            unsafe_allow_html=True,
        )

        # Auto-refresh script (updates every second)
        if not timed_out:
            st.markdown(
                f'<script>setTimeout(function(){{window.parent.postMessage({{isStreamlitMessage:true,type:"streamlit:setComponentValue",value:Date.now()}},"*")}},{min(int(remaining * 1000), 1000)})</script>',
                unsafe_allow_html=True,
            )

        # Question
        st.markdown(f"### {q['q']}")

        # Handle timeout
        if timed_out:
            st.error("⏰ Tiden gikk ut!")
            st.session_state.quiz_answers.append({
                "answer": "—", "correct": False, "timeout": True
            })
            st.session_state.quiz_streak = 0
            st.info(f"Riktig svar: **{q['correct'].upper()}) {q[q['correct']]}**")
            if st.button("Neste spørsmål ➡️", type="primary", use_container_width=True):
                st.session_state.quiz_index += 1
                st.session_state.quiz_q_start = time.time()
                st.rerun()
        else:
            # Answer buttons
            col_a, col_b, col_c = st.columns(3)
            answered = False
            chosen = None
            with col_a:
                if st.button(f"🅰️ {q['a']}", key=f"ans_a_{idx}", use_container_width=True):
                    chosen = "a"
                    answered = True
            with col_b:
                if st.button(f"🅱️ {q['b']}", key=f"ans_b_{idx}", use_container_width=True):
                    chosen = "b"
                    answered = True
            with col_c:
                if st.button(f"🅲 {q['c']}", key=f"ans_c_{idx}", use_container_width=True):
                    chosen = "c"
                    answered = True

            if answered and chosen:
                is_correct = chosen == q["correct"]
                st.session_state.quiz_answers.append({
                    "answer": f"{chosen.upper()}) {q[chosen]}",
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
                st.session_state.quiz_index += 1
                st.session_state.quiz_q_start = time.time()
                st.rerun()
