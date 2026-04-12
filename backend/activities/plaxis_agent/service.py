# -*- coding: utf-8 -*-
"""
GAPI Pipeline Service — full multi-step flow
=============================================
Step 0  — Context gathering  (0 LLM calls, only lookups)
Step 1  — Planning           (LLM call #1, returns structured JSON plan)
Step 2  — User approval gate (handled by frontend / routes — not here)
Step 3  — Code generation    (LLM call #2, uses full plan + context)
Step 4  — Reference validation (LLM call #3, API signature check)
Step 5  — Execution via PlaxisWorker with retry
Step 6  — Observer → database (LLM call #4, updates GapiLearning)
"""

import json
import re
import textwrap
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from openai import AzureOpenAI

from config import (
    AZURE_OPENAI_API_KEY,
    AZURE_OPENAI_DEPLOYMENT,
    AZURE_OPENAI_ENDPOINT,
    AZURE_OPENAI_API_VERSION,
    OPENAI_API_KEY,
    OPENAI_MODEL,
)
from activities.plaxis_agent.knowledge import (
    build_api_cards,
    retrieve_docs,
    retrieve_reference_for_code,
    extract_pdf_text,
)

# ---------------------------------------------------------------------------
# LLM client
# ---------------------------------------------------------------------------

_client = None


def _get_client():
    global _client
    if _client is not None:
        return _client, AZURE_OPENAI_DEPLOYMENT or OPENAI_MODEL
    if AZURE_OPENAI_API_KEY and AZURE_OPENAI_ENDPOINT:
        _client = AzureOpenAI(
            api_key=AZURE_OPENAI_API_KEY,
            azure_endpoint=AZURE_OPENAI_ENDPOINT,
            api_version=AZURE_OPENAI_API_VERSION,
        )
        return _client, AZURE_OPENAI_DEPLOYMENT
    elif OPENAI_API_KEY:
        from openai import OpenAI
        _client = OpenAI(api_key=OPENAI_API_KEY)
        return _client, OPENAI_MODEL
    raise RuntimeError(
        "Ingen AI-nøkkel konfigurert. Sett AZURE_OPENAI_API_KEY + AZURE_OPENAI_ENDPOINT "
        "eller OPENAI_API_KEY i .env."
    )


def _strip_fences(text: str) -> str:
    text = text.strip()
    m = re.match(r'^```(?:json|python)?\s*\n?(.*?)\n?```\s*$', text, re.DOTALL)
    return m.group(1).strip() if m else text


# ---------------------------------------------------------------------------
# STEP 0 — Context gathering  (no LLM calls)
# ---------------------------------------------------------------------------

def gather_context(
    user_message: str,
    session_id: str = "default",
    username: str = "default",
    model_info: Optional[Dict] = None,
    pdf_text: Optional[str] = None,
    selected_context: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Gather all context needed for planning and code generation."""
    ctx: Dict[str, Any] = {
        "learnings_md": "",
        "standards": [],
        "manual_docs": [],
        "ref_cards": "",
        "model_info": model_info or {},
        "pdf_text": pdf_text or "",
        "selected": selected_context or [],
    }

    # 1. Persistent learnings from database
    try:
        from core.database import get_db_session
        from core.models import GapiLearning
        db = get_db_session()
        try:
            parts = []
            global_e = (
                db.query(GapiLearning)
                .filter(GapiLearning.scope == "global")
                .order_by(GapiLearning.updated_at.desc())
                .first()
            )
            if global_e:
                parts.append(global_e.content)
            user_e = (
                db.query(GapiLearning)
                .filter(GapiLearning.scope == "user",
                        GapiLearning.scope_key == username)
                .order_by(GapiLearning.updated_at.desc())
                .first()
            )
            if user_e:
                parts.append(user_e.content)
            ctx["learnings_md"] = "\n\n---\n\n".join(parts)
        finally:
            db.close()
    except Exception as exc:
        print(f"GAPI ctx learnings: {exc}")

    # 2. Standards search
    try:
        import os as _os
        import json as _json
        _storage = _os.path.join(_os.path.dirname(__file__), "..", "..", "data", "standarder")
        _idx_file = _os.path.join(_storage, "index.json")
        if _os.path.exists(_idx_file):
            with open(_idx_file, "r", encoding="utf-8") as f:
                docs_idx = _json.load(f)
            query_lower = user_message.lower()
            words = [w for w in query_lower.split() if len(w) > 3]
            for doc in docs_idx:
                sfile = _os.path.join(_storage, doc["id"], "sections.json")
                if not _os.path.exists(sfile):
                    continue
                with open(sfile, "r", encoding="utf-8") as f:
                    secs = _json.load(f)
                for sec in secs:
                    hay = f"{sec.get('id','')} {sec.get('title','')} {sec.get('content','')}".lower()
                    if any(w in hay for w in words):
                        ctx["standards"].append({
                            "doc_name": doc["name"],
                            "section_id": sec.get("id", ""),
                            "title": sec.get("title", ""),
                            "content": sec.get("content", "")[:1200],
                        })
                    if len(ctx["standards"]) >= 8:
                        break
                if len(ctx["standards"]) >= 8:
                    break
    except Exception as exc:
        print(f"GAPI ctx standards: {exc}")

    # 3. PLAXIS manual search
    try:
        from activities.plaxis_agent.indexer import search_manual
        manual_docs, _ = search_manual(user_message, top=5)
        ctx["manual_docs"] = manual_docs
    except Exception as exc:
        print(f"GAPI ctx manual: {exc}")

    # 4. Reference cards
    try:
        docs = retrieve_docs(user_message, k=6)
        ctx["ref_cards"] = build_api_cards(docs)
    except Exception as exc:
        print(f"GAPI ctx ref_cards: {exc}")

    return ctx


# ---------------------------------------------------------------------------
# STEP 1 — Planning  (LLM call #1)
# ---------------------------------------------------------------------------

_PLAN_SYSTEM_PROMPT = textwrap.dedent("""\
    Du er en PLAXIS-planlegger innebygd i RamGAP. Basert på brukerens forespørsel,
    modellstatus, relevante standarder, tutorial-veiledning og API-referanse,
    lager du en DETALJERT PLAN.

    Svar ALLTID med gyldig JSON (kun JSON, ingen markdown-omslutning):
    {
      "forståelse": "Kort beskrivelse av hva brukeren ønsker",
      "steg": [
        {
          "nr": 1,
          "beskrivelse": "Hva dette steget gjør",
          "kommandoer": ["kommando1", "kommando2"],
          "risiko": "lav|medium|høy",
          "kan_automatiseres": true
        }
      ],
      "standard_advarsler": ["..."],
      "modellerings_tips": ["..."],
      "manglende_info": [],
      "ønsket_output": "Hva brukeren forventer"
    }

    REGLER:
    • risiko lav = data-henting/lesing
    • risiko medium = opprette/endre strukturer, materialer
    • risiko høy = mesh, calculate, langvarige operasjoner
    • Inkluder ALLTID et første steg med risiko=lav for å verifisere modell
    • Returner KUN gyldig JSON på norsk. Ingen ```-omslutning.
""")


def create_plan(
    user_message: str,
    context: Dict[str, Any],
    history: Optional[List[Dict[str, str]]] = None,
) -> Dict[str, Any]:
    """LLM call #1 — create a structured plan."""
    messages: List[Dict[str, str]] = [
        {"role": "system", "content": _PLAN_SYSTEM_PROMPT},
    ]

    if context.get("learnings_md"):
        messages.append({"role": "system", "content":
                          "## Læringslogg — unngå kjente feil:\n\n"
                          + context["learnings_md"][:3000]})
    if context.get("standards"):
        parts = ["## Relevante standardseksjoner\n"]
        for s in context["standards"][:5]:
            parts.append(f"**{s['doc_name']} — {s.get('title','')}**\n{s['content'][:800]}")
        messages.append({"role": "system", "content": "\n\n".join(parts)})
    if context.get("manual_docs"):
        parts = ["## PLAXIS Tutorial Manual\n"]
        for d in context["manual_docs"][:3]:
            parts.append(f"**{d.get('title', d.get('source',''))}**\n{d.get('content','')[:1000]}")
        messages.append({"role": "system", "content": "\n\n".join(parts)})
    if context.get("ref_cards"):
        messages.append({"role": "system", "content":
                          "## PLAXIS API-referansekort\n\n" + context["ref_cards"][:4000]})
    if context.get("model_info"):
        messages.append({"role": "system", "content":
                          "## Modellstatus\n\n"
                          + json.dumps(context["model_info"], ensure_ascii=False, indent=2)[:2000]})
    if history:
        messages.extend(history[-10:])
    messages.append({"role": "user", "content": user_message})

    client, model = _get_client()
    resp = client.chat.completions.create(model=model, messages=messages, max_completion_tokens=2048)
    raw = _strip_fences(resp.choices[0].message.content or "")

    try:
        plan = json.loads(raw)
    except json.JSONDecodeError:
        m = re.search(r'\{.*\}', raw, re.DOTALL)
        if m:
            try:
                plan = json.loads(m.group(0))
            except Exception:
                plan = _fallback_plan(user_message, raw)
        else:
            plan = _fallback_plan(user_message, raw)
    return plan


def _fallback_plan(user_message: str, raw: str) -> Dict:
    return {
        "forståelse": user_message,
        "steg": [{"nr": 1, "beskrivelse": "Kjør forespørsel", "kommandoer": [],
                  "risiko": "medium", "kan_automatiseres": True}],
        "standard_advarsler": [],
        "modellerings_tips": [],
        "manglende_info": [],
        "ønsket_output": "Se output",
        "_parse_error": raw[:200],
    }


# ---------------------------------------------------------------------------
# STEP 3 — Code generation  (LLM call #2)
# ---------------------------------------------------------------------------

_CODE_SYSTEM_PROMPT = textwrap.dedent("""\
    Du er en PLAXIS Python-kodegenerator innebygd i RamGAP.
    Du får en godkjent plan og skal generere kode som implementerer ALLE stegene.

    ABSOLUTTE REGLER:
    • Returner KUN ren Python-kode — ingen markdown, ingen ```-blokker.
    • ALDRI kall new_server(), ALDRI importer plxscripting — allerede tilkoblet.
    • ALDRI kall g_i.new() — operer på eksisterende prosjekt.
    • Tilgjengelige variabler (ferdig tilkoblet):
      g_i  = PLAXIS input-server   (alias: g)
      s_i  = input connection       (alias: s)
      g_o  = PLAXIS output-server
      s_o  = output connection
    • ALLTID try/except rundt hver seksjon.
    • ALLTID print() med === SEKSJONSNAVN === og ITEM: prefix.
    • Siste linje: # FERDIG

    KORREKTE PLAXIS PYTHON MØNSTRE (OBLIGATORISK):

    KRITISK — MODUS BESTEMMER HVA SAMLINGER RETURNERER:
      g_i.gotostructures() → g_i.Plates gir strukturelle objekter (Spunt_venstre, Plate_2)
      g_i.gotostages()     → g_i.Plates gir FASE-sub-elementer (Plate_1_1, Plate_1_2, …)
      Du MÅ kalle gotostructures() FØR du leser Plates, Anchors, etc.
      Du MÅ kalle gotostages() FØR du bruker Phases eller calculate().
      Bytt ALLTID modus eksplisitt før du aksesserer samlinger.

    Fase-tilgang — kall gotostages() først (ALDRI g_i.Phase_xxx):
      g_i.gotostages()
      phase = None
      for ph in g_i.Phases:
          if ph.Identification.value == "fasenavn":
              phase = ph
              break

    Fase-type — DeformCalcType.value er INT, ALDRI streng:
      calc_type_str = str(phase.DeformCalcType)  # bruk str()

    Plate-tilgang — kall gotostructures() først (ALDRI g_i.Spunt_venstre):
      g_i.gotostructures()
      target = None
      for p in g_i.Plates:
          if p.Name.value == "Spunt_venstre":
              target = p
              break

    Plate-geometri — ALDRI plate.Point_1/StartPoint/EndPoint:
      x1 = plate.Parent.First.x.value
      y1 = plate.Parent.First.y.value
      x2 = plate.Parent.Second.x.value
      y2 = plate.Parent.Second.y.value

    Flytte plate-punkt — DISPLACEMENT, ALDRI absolutt tilordning:
      g_i.gotostructures()
      pt = plate.Parent.Second
      dy = new_y - pt.y.value
      g_i.move(pt, (0, dy))

    Etter geometriendring MÅ du remeshe og beregne ALLE faser:
      g_i.gotomesh()
      g_i.mesh(0.06)
      g_i.gotostages()
      # KRITISK: Tving rekalkulerinsg — etter første beregning setter PLAXIS
      # ShouldCalculate=False på ferdige faser. Uten dette returnerer
      # g_i.calculate() CACHED resultater og ΣMsf endres IKKE!
      for ph in g_i.Phases:
          ph.ShouldCalculate = True
      g_i.calculate()
      # ALDRI bare g_i.calculate(target_phase) etter remesh — forgjengere mangler!

    VIKTIG for optimalisering (iterativ geometriendring):
      Hvert steg i loopen MÅ:
        1. g_i.gotostructures()
        2. Hent plate-referanser PÅ NYTT — for p in g_i.Plates: ...
           (referanser KAN bli stale etter remesh)
        3. g_i.move(punkt, (dx, dy))
        4. g_i.gotomesh(); g_i.mesh(0.06)
        5. g_i.gotostages()
        6. for ph in g_i.Phases: ph.ShouldCalculate = True   ← OBLIGATORISK!
        7. g_i.calculate()
        8. Les ΣMsf
      ΣMsf VIL IKKE endre seg uten ShouldCalculate=True + full rekalkuleringssyklus.
      Begrens til 5-7 iterasjoner (tar minutter per iterasjon).

    Safety-faktor (ΣMsf) etter beregning:
      try:
          msf = phase.Reached.SumMsf.value
      except Exception:
          msf = phase.SumMsf.value

    Resultater via output-server:
      g_o.getresults(plate, phase, g_o.ResultTypes.Plate.Nx2D, 'max')

    Materialer:
      mat.Identification.value, mat.GammaUnsat.value
""")


def generate_code_from_plan(
    user_message: str,
    plan: Dict[str, Any],
    context: Dict[str, Any],
    history: Optional[List[Dict[str, str]]] = None,
) -> Dict[str, Any]:
    """LLM call #2 — generate code from approved plan."""
    messages: List[Dict[str, str]] = [
        {"role": "system", "content": _CODE_SYSTEM_PROMPT},
    ]

    # Plan summary
    plan_text = (
        f"## Godkjent plan: {plan.get('forståelse', user_message)}\n\n"
        "Steg som skal implementeres:\n"
    )
    for s in plan.get("steg", []):
        plan_text += f"  {s['nr']}. {s['beskrivelse']} [kommandoer: {', '.join(s.get('kommandoer', []))}]\n"
    if plan.get("standard_advarsler"):
        plan_text += "\nStandard-advarsler:\n" + "\n".join(f"  • {w}" for w in plan["standard_advarsler"])
    if plan.get("modellerings_tips"):
        plan_text += "\nModelleringstips:\n" + "\n".join(f"  • {t}" for t in plan["modellerings_tips"])
    messages.append({"role": "system", "content": plan_text})

    # Reference cards for planned commands
    all_cmds = [c for s in plan.get("steg", []) for c in s.get("kommandoer", [])]
    query = " ".join(all_cmds) + " " + user_message
    docs = retrieve_docs(query, k=8)
    ref_cards = build_api_cards(docs)
    if ref_cards:
        messages.append({"role": "system", "content": "## API-referansekort\n\n" + ref_cards})

    if context.get("learnings_md"):
        messages.append({"role": "system", "content":
                          "## Læringslogg — unngå disse feilene:\n\n"
                          + context["learnings_md"][:2000]})
    if context.get("selected"):
        messages.append({"role": "system", "content":
                          "## Valgt kontekst:\n" + "\n".join(f"• {i}" for i in context["selected"])})
    if context.get("model_info"):
        messages.append({"role": "system", "content":
                          "## Modellstatus:\n\n"
                          + json.dumps(context["model_info"], ensure_ascii=False, indent=2)[:1500]})
    if context.get("pdf_text"):
        messages.append({"role": "system", "content":
                          "## Brukerens PDF:\n\n" + context["pdf_text"][:6000]})
    if history:
        messages.extend(history[-8:])

    messages.append({"role": "user",
                     "content": f"Generer kode som implementerer planen for: {user_message}"})

    client, model = _get_client()
    resp = client.chat.completions.create(model=model, messages=messages, max_completion_tokens=4096)
    code = _strip_fences(resp.choices[0].message.content or "")
    return {"code": code, "docs_used": all_cmds[:8]}


# ---------------------------------------------------------------------------
# STEP 4 — Reference validation  (LLM call #3)
# ---------------------------------------------------------------------------

_VALIDATION_PROMPT = textwrap.dedent("""\
    Du er en Plaxis API-ekspert. Valider Python-kode mot Plaxis 2D-referansen.

    SJEKK OG RETT OPP disse vanlige feil:
    1. MODUS: g_i.gotostructures() MÅ kalles FØR Plates/Anchors-tilgang.
       I gotostages()-modus returnerer Plates fase-sub-elementer (Plate_1_1), IKKE strukturer.
    2. DeformCalcType.value er INT — ALDRI "Safety" in int. Bruk str().
    3. Plater: iterer g_i.Plates og match Name.value. ALDRI g_i.PlateName.
    4. Geometri: plate.Parent.First/Second. ALDRI plate.Point_1/StartPoint/EndPoint.
    5. Flytte: g_i.move(punkt, (dx, dy)). ALDRI punkt.y.value = verdi.
    6. Safety: phase.Reached.SumMsf.value ELLER phase.SumMsf.value.
    7. Fase: g_i.gotostages() først, iterer g_i.Phases. ALDRI g_i.Phase_xxx.
    8. ETTER geometriendring: g_i.gotomesh(); g_i.mesh(0.06); g_i.gotostages(); g_i.calculate()
       ALDRI bare calculate(target_phase) etter remesh — forgjengerfaser mangler!
    9. Før move() → g_i.gotostructures().
    10. Optimalisering: move → mesh → calculate() (ALLE faser) per iterasjon.
    11. KRITISK: Før g_i.calculate() i en loop MÅ du sette ShouldCalculate=True på
        ALLE faser: `for ph in g_i.Phases: ph.ShouldCalculate = True`.
        Uten dette returnerer beregninga CACHED resultater og ΣMsf endres IKKE.
    12. I optimaliseringsloop: hent plate/linje/punkt-referanser PÅ NYTT etter remesh
        (iterer g_i.Plates på nytt). Stale referanser kan gi feil.

    Returner KUN korrigert Python-kode. Ingen forklaring. Ingen markdown.
    Hvis koden er korrekt, returner den UENDRET.
""")


def validate_code(code: str) -> str:
    """LLM call #3 — validate generated code against plaxis_2d_reference.md."""
    ref_cards = retrieve_reference_for_code(code)
    if not ref_cards:
        return code

    client, model = _get_client()
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": _VALIDATION_PROMPT},
            {"role": "system", "content": f"Referansekort:\n\n{ref_cards}"},
            {"role": "user", "content": f"Valider:\n\n{code}"},
        ],
        max_completion_tokens=4096,
    )
    validated = _strip_fences(resp.choices[0].message.content or "")
    return validated if validated and len(validated) >= len(code) * 0.3 else code


# ---------------------------------------------------------------------------
# STEP 5 — Execution via PlaxisWorker
# ---------------------------------------------------------------------------

_BLOCKED = [
    re.compile(r"\bg\.new\s*\("),
    re.compile(r"\bnew_server\s*\("),
    re.compile(r"\bimport\s+os\b"),
    re.compile(r"\bimport\s+subprocess"),
    re.compile(r"\bopen\s*\("),
    re.compile(r"\b__import__\s*\("),
    re.compile(r"\beval\s*\("),
]


def execute_code(
    code: str,
    connection_params: Dict[str, Any],
    session_id: str = "default",
    timeout: int = 7200,
) -> Dict[str, Any]:
    """Safety-check, wrap, submit to PlaxisWorker, poll for result."""
    from core.database import get_db_session
    from core.models import PlaxisJob
    from activities.plaxis.script_builder import build_agent_exec_script

    if not code or not code.strip():
        return {"success": False, "output": "", "error": "Ingen kode å kjøre."}
    for pat in _BLOCKED:
        if pat.search(code):
            return {"success": False, "output": "",
                    "error": f"Blokkert: forbudt mønster ({pat.pattern})."}

    script = build_agent_exec_script(
        host=connection_params["host"],
        port=connection_params["port"],
        password=connection_params["password"],
        output_port=connection_params.get("output_port"),
        output_password=connection_params.get("output_password"),
        agent_code=code,
    )

    db = get_db_session()
    try:
        job = PlaxisJob(session_id=session_id, job_type="agent_exec",
                        code=script, status="pending")
        db.add(job)
        db.commit()
        job_id = job.id
    except Exception as exc:
        db.rollback()
        return {"success": False, "output": "", "error": f"Jobb-feil: {exc}"}
    finally:
        db.close()

    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        time.sleep(1.0)
        db = get_db_session()
        try:
            job = db.query(PlaxisJob).filter(PlaxisJob.id == job_id).first()
            if not job:
                return {"success": False, "output": "", "error": "Jobb forsvant."}
            if job.status == "done":
                r = json.loads(job.result_json) if job.result_json else {}
                return {"success": r.get("success", False),
                        "output": r.get("output", ""),
                        "error": r.get("error")}
            if job.status == "failed":
                return {"success": False, "output": "",
                        "error": job.error or "Jobb feilet."}
        finally:
            db.close()

    return {"success": False, "output": "",
            "error": f"Tidsavbrudd etter {timeout}s. Kjører PlaxisWorker?"}


# ---------------------------------------------------------------------------
# STEP 5b — Result analysis  (LLM call #3.5)
# ---------------------------------------------------------------------------

_RESULT_ANALYSIS_PROMPT = textwrap.dedent("""\
    Du er en kritisk evaluator for GAPI, et AI-system som kjører PLAXIS-kode.

    Du får:
    - «Ønsket output» fra planen (hva brukeren forventet)
    - Faktisk output fra kjøringen
    - Eventuell feilmelding

    Evaluer om kjøringen leverte det som ble forventet, og svar ALLTID med gyldig JSON:
    {
      "status": "success" | "partial" | "wrong" | "error",
      "matched": true | false,
      "forklaring": "Kort norsk forklaring av hva som skjedde",
      "mangler": ["Liste med konkrete ting som mangler eller er feil"],
      "retry_hint": "Konkret instruksjon til neste kodegenerering for å fikse dette"
    }

    DEFINISJONER:
    • success  — output inneholder det som ble etterspurt, ingen feil
    • partial  — noe output finnes men deler mangler (f.eks. kun noen seksjoner)
    • wrong    — output finnes men er feil type/innhold (f.eks. henter feil data)
    • error    — kjøringen produserte en feil eller tom output

    REGLER:
    • Returner KUN gyldig JSON — ingen forklaring utenfor JSON.
    • Svar på norsk i tekstfeltene.
    • retry_hint skal være presis nok til å bruke direkte som instruksjon.
    • Sjekk om print-seksjoner matcher det planen bad om.
""")


def analyze_result(
    plan: Dict[str, Any],
    execution_result: Dict[str, Any],
) -> Dict[str, Any]:
    """LLM call #3.5 — compare actual output against the plan's ønsket_output."""
    expected = plan.get("ønsket_output", "")
    raw_output = execution_result.get("output", "")
    error = execution_result.get("error")
    success_flag = execution_result.get("success", False)

    # Fast-path: obvious total failure
    if not success_flag and not raw_output and error:
        return {
            "status": "error",
            "matched": False,
            "forklaring": f"Kjøringen feilet med feil: {error[:300]}",
            "mangler": [error[:200]] if error else [],
            "retry_hint": f"Koden feilet med: {error[:300]}. Rett opp og prøv igjen.",
        }

    try:
        client, model = _get_client()
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": _RESULT_ANALYSIS_PROMPT},
                {"role": "user", "content": (
                    f"## Ønsket output (fra planen)\n{expected}\n\n"
                    f"## Faktisk output\n```\n{raw_output[:3000]}\n```\n"
                    + (f"\n## Feilmelding\n{error}" if error else "")
                )},
            ],
            max_completion_tokens=512,
        )
        raw = _strip_fences(resp.choices[0].message.content or "")
        try:
            verdict = json.loads(raw)
        except json.JSONDecodeError:
            m = re.search(r'\{.*\}', raw, re.DOTALL)
            verdict = json.loads(m.group(0)) if m else {}
        # Ensure required keys
        verdict.setdefault("status", "success" if success_flag else "error")
        verdict.setdefault("matched", success_flag)
        verdict.setdefault("forklaring", "")
        verdict.setdefault("mangler", [])
        verdict.setdefault("retry_hint", "")
        return verdict
    except Exception as exc:
        print(f"GAPI result analysis: {exc}")
        return {
            "status": "success" if success_flag else "error",
            "matched": success_flag,
            "forklaring": str(exc)[:200],
            "mangler": [],
            "retry_hint": "",
        }


# ---------------------------------------------------------------------------
# STEP 6 — Observer → database  (LLM call #4)
# ---------------------------------------------------------------------------

_OBSERVER_PROMPT = textwrap.dedent("""\
    Du er en teknisk observatør for GAPI. Oppdater den persistente læringsloggen
    basert på den siste kjøringen.

    Loggen har disse seksjonene:
    ## Vanlige feil og løsninger
    ## Vellykkede mønstre
    ## PLAXIS-modell-innsikt
    ## Standarder og krav
    ## API-signaturer som krever særlig oppmerksomhet

    REGLER:
    • Returner HELE den oppdaterte markdown-filen.
    • Maks 300 linjer totalt.
    • Oppdater eksisterende seksjoner — ikke bare legg til.
    • Fjern utdaterte oppføringer.
    • Prioriter konkrete, tekniske lærdommer med eksempel-kode.
    • Svar på norsk. Returner KUN markdown — ingen forklaring.
""")


def update_learnings(
    user_message: str,
    plan: Dict[str, Any],
    code: str,
    validated_code: str,
    execution_result: Dict[str, Any],
    retry_count: int,
    verdict: Optional[Dict[str, Any]] = None,
    session_id: str = "default",
    username: str = "default",
) -> None:
    """LLM call #4 — update the persistent GapiLearning entry in the database."""
    from core.database import get_db_session
    from core.models import GapiLearning

    db = get_db_session()
    existing_log, existing_id = "", None
    try:
        e = (db.query(GapiLearning)
             .filter(GapiLearning.scope == "global")
             .order_by(GapiLearning.updated_at.desc())
             .first())
        if e:
            existing_log, existing_id = e.content, e.id
    finally:
        db.close()

    success = execution_result.get("success", False)
    v_status = (verdict or {}).get("status", "success" if success else "error")
    v_forklaring = (verdict or {}).get("forklaring", "")
    ctx = (
        f"## Siste kjøring\n"
        f"- Forespørsel: {user_message[:200]}\n"
        f"- Plan-steg: {len(plan.get('steg', []))}\n"
        f"- Ønsket output: {plan.get('ønsket_output','')[:200]}\n"
        f"- Standard-advarsler: {json.dumps(plan.get('standard_advarsler', []), ensure_ascii=False)[:300]}\n"
        f"- Resultat-status: {v_status.upper()}\n"
        f"- Evaluering: {v_forklaring}\n"
        f"- Retry: {retry_count}\n"
        f"- Feil: {(execution_result.get('error') or 'Ingen')[:300]}\n"
        f"- Output (utdrag):\n```\n{(execution_result.get('output') or '')[:1200]}\n```\n"
    )
    if validated_code != code:
        ctx += (
            f"\n## Validering endret koden\n"
            f"Originalt:\n```python\n{code[:600]}\n```\n"
            f"Korrigert:\n```python\n{validated_code[:600]}\n```\n"
        )

    prompt_content = (
        f"Nåværende logg:\n\n{existing_log}\n\n---\n\nOppdater basert på:\n\n{ctx}"
        if existing_log else
        f"Start ny læringslogg basert på:\n\n{ctx}"
    )

    try:
        client, model = _get_client()
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": _OBSERVER_PROMPT},
                {"role": "user", "content": prompt_content},
            ],
            max_completion_tokens=2048,
        )
        updated_md = _strip_fences(resp.choices[0].message.content or "")
        if not updated_md:
            return

        db = get_db_session()
        try:
            if existing_id:
                e = db.query(GapiLearning).filter(GapiLearning.id == existing_id).first()
                if e:
                    e.content = updated_md
                    e.updated_at = datetime.now(timezone.utc)
            else:
                db.add(GapiLearning(scope="global", session_id=session_id,
                                    title="GAPI læringslogg",
                                    content=updated_md, username=username))
            db.commit()
        except Exception as exc:
            db.rollback()
            print(f"GAPI observer DB: {exc}")
        finally:
            db.close()
    except Exception as exc:
        print(f"GAPI observer LLM: {exc}")


# ---------------------------------------------------------------------------
# Pipeline orchestration — called from routes
# ---------------------------------------------------------------------------

def run_pipeline_plan(
    user_message: str,
    session_id: str = "default",
    username: str = "default",
    model_info: Optional[Dict] = None,
    pdf_text: Optional[str] = None,
    selected_context: Optional[List[str]] = None,
    history: Optional[List[Dict]] = None,
) -> Dict[str, Any]:
    """Steps 0+1: gather context and return plan for user approval."""
    ctx = gather_context(
        user_message=user_message, session_id=session_id, username=username,
        model_info=model_info, pdf_text=pdf_text, selected_context=selected_context,
    )
    plan = create_plan(user_message, ctx, history=history)
    return {
        "plan": plan,
        "context_summary": {
            "has_learnings": bool(ctx.get("learnings_md")),
            "standards_found": len(ctx.get("standards", [])),
            "manual_docs_found": len(ctx.get("manual_docs", [])),
            "ref_cards": bool(ctx.get("ref_cards")),
        },
        # Pass serialized context back so routes can store it in session
        "_context": ctx,
    }


def run_pipeline_execute(
    user_message: str,
    plan: Dict[str, Any],
    connection_params: Dict[str, Any],
    session_id: str = "default",
    username: str = "default",
    context: Optional[Dict] = None,
    pdf_text: Optional[str] = None,
    selected_context: Optional[List[str]] = None,
    history: Optional[List[Dict]] = None,
    max_retries: int = 2,
) -> Dict[str, Any]:
    """Steps 3+4+5+6: generate code, validate, execute, update learnings."""
    if not context:
        context = gather_context(
            user_message=user_message, session_id=session_id, username=username,
            pdf_text=pdf_text, selected_context=selected_context,
        )

    # Step 3: generate
    gen = generate_code_from_plan(user_message, plan, context, history=history)
    code = gen["code"]
    docs_used = gen.get("docs_used", [])

    # Step 4: validate
    validated_code = validate_code(code)

    # Step 5: execute with retry (error-based AND result-based)
    result: Dict[str, Any] = {"success": False, "output": "", "error": None}
    verdict: Dict[str, Any] = {}
    actual_retries = 0
    current_code = validated_code

    # Detect heavy scripts (optimization loops with calculate()) — never auto-retry
    _is_heavy = bool(re.search(r'(while\s|for\s.*range).*calculate', current_code, re.DOTALL))

    for attempt in range(1, max_retries + 2):
        result = execute_code(current_code, connection_params, session_id)

        # Step 5b: evaluate result quality vs expected output
        verdict = analyze_result(plan, result)

        if verdict.get("status") == "success":
            break

        # Heavy scripts (optimization) that ran to completion should NOT be retried.
        # The script already modified the PLAXIS model; re-running would start from
        # the modified state and produce wrong results.
        if _is_heavy and result.get("success") and result.get("output"):
            print("GAPI: Skipping retry — heavy script ran to completion")
            break

        actual_retries = attempt - 1
        if attempt > max_retries:
            break

        # Build retry feedback — include both error and result-analysis hint
        retry_feedback = ""
        if result.get("error"):
            retry_feedback += f"Feilmelding: {result['error']}\n"
        if verdict.get("retry_hint"):
            retry_feedback += f"Resultat-problem: {verdict['retry_hint']}\n"
        if verdict.get("mangler"):
            retry_feedback += "Mangler: " + ", ".join(verdict["mangler"]) + "\n"

        retry_history = list(history or [])
        retry_history.append({"role": "assistant", "content": current_code})
        retry_history.append({
            "role": "user",
            "content": (
                f"Koden ga feil resultat. {retry_feedback}\n"
                f"Forventet: {plan.get('ønsket_output', '')}\n\n"
                "Rett opp koden og returner KUN korrekt Python-kode."
            ),
        })
        retry_gen = generate_code_from_plan(user_message, plan, context, history=retry_history)
        current_code = validate_code(retry_gen["code"])

    # Step 6: update learnings (non-blocking)
    try:
        update_learnings(
            user_message=user_message, plan=plan,
            code=code, validated_code=validated_code,
            execution_result=result, retry_count=actual_retries,
            verdict=verdict,
            session_id=session_id, username=username,
        )
    except Exception as exc:
        print(f"GAPI observer (non-critical): {exc}")

    return {
        "code": current_code,
        "original_code": code if validated_code != code else None,
        "output": result.get("output", ""),
        "success": verdict.get("matched", result.get("success", False)),
        "error": result.get("error"),
        "verdict": verdict,
        "docs_used": docs_used,
        "attempts": actual_retries + 1,
        "steps": len(plan.get("steg", [])),
    }


# ---------------------------------------------------------------------------
# Legacy compatibility — kept for the old /chat route
# ---------------------------------------------------------------------------

def generate_code(user_message, history=None, pdf_text=None, selected_context=None):
    docs = retrieve_docs(user_message, k=4)
    api_cards = build_api_cards(docs)
    docs_used = [d.get("name", "") for d in docs]

    from activities.plaxis_agent.service_legacy import SYSTEM_PROMPT
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    if api_cards:
        messages.append({"role": "system", "content": f"API-kort:\n{api_cards}"})
    if selected_context:
        messages.append({"role": "system",
                         "content": "Valgt:\n" + "\n".join(f"• {i}" for i in selected_context)})
    if pdf_text:
        messages.append({"role": "system", "content": f"PDF:\n{pdf_text[:8000]}"})
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": user_message})
    client, model = _get_client()
    resp = client.chat.completions.create(model=model, messages=messages, max_completion_tokens=4096)
    return {"code": _strip_fences(resp.choices[0].message.content or ""),
            "api_cards": api_cards, "docs_used": docs_used}


def execute_via_worker(code, connection_params, session_id="default"):
    return execute_code(code, connection_params, session_id)


def chat_and_execute(user_message, connection_params, session_id="default",
                     history=None, pdf_text=None, selected_context=None,
                     max_retries=2, max_steps=5):
    ctx = gather_context(user_message, session_id=session_id,
                         pdf_text=pdf_text, selected_context=selected_context)
    plan = create_plan(user_message, ctx, history=history)
    return run_pipeline_execute(
        user_message=user_message, plan=plan,
        connection_params=connection_params, session_id=session_id,
        context=ctx, history=history, max_retries=max_retries,
    )


def get_observer_log(session_id: str) -> str:
    return ""
# -*- coding: utf-8 -*-
"""
Plaxis Agent Service
=====================
Orchestrates:
  1.  Knowledge retrieval (hybrid search over Plaxis API docs + optional PDF)
  2.  LLM code generation via Azure OpenAI (Azure AI Foundry deployment)
  3.  Safe execution of generated code against a live Plaxis session
  4.  Automatic retry with error feedback when execution fails

The service is stateless per call — conversation history is passed in from the
frontend via the messages list.
"""

import re
import textwrap
from typing import Any, Dict, List, Optional

from openai import AzureOpenAI

from config import (
    AZURE_OPENAI_API_KEY,
    AZURE_OPENAI_DEPLOYMENT,
    AZURE_OPENAI_ENDPOINT,
    AZURE_OPENAI_API_VERSION,
    OPENAI_API_KEY,
    OPENAI_MODEL,
)
from activities.plaxis_agent.knowledge import (
    build_api_cards,
    extract_pdf_text,
    retrieve_docs,
    retrieve_reference_for_code,
)

# ---------------------------------------------------------------------------
# System prompt — instructs the LLM how to behave
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = textwrap.dedent("""\
    Du er en PLAXIS-ekspert og kodegenerator innebygd i RamGAP.  Du tenker GRUNDIG
    og NØYAKTIG — du henter ALLTID mer data enn brukeren eksplisitt ber om, fordi
    kontekst er viktig for å ta gode beslutninger.

    VIKTIGST — FLERSTEGS-TENKNING:
    Komplekse oppgaver (optimalisering, analyse, endringer) krever FLERE STEG.
    Du skal ALLTID starte med å hente data FØR du analyserer / endrer noe.
    Etter hvert kodesteg vil du se resultatene.  Basert på resultatene bestemmer
    du hva neste steg skal være.

    Når du er ferdig med siste steg, skriv «FERDIG» som siste linje i koden
    (som kommentar: # FERDIG).

    Dersom du trenger MER informasjon fra brukeren for å fortsette, print en
    linje som starter med «SPØRSMÅL:» fulgt av spørsmålet ditt.  Da vil
    systemet vise spørsmålet til brukeren og vente på svar.
    Eksempel:
        print("SPØRSMÅL: Hvilken fase skal optimaliseres?  Velg fra listen ovenfor.")

    Dersom koden din kjørte men ga TOMME eller MANGLENDE data, prøv en ANNEN
    tilnærming i neste steg.  Ikke gi opp — utforsk andre attributter, metoder
    eller samlinger.

    TENKEPROSESS:
    • Tenk først over HVA brukeren egentlig trenger, ikke bare hva de bokstavelig spør om.
    • Dersom brukeren spør om f.eks. «plater», hent også materialegenskaper, tilkoblinger,
      og faseresultater for platene — ikke bare navnene.
    • Dersom brukeren spør om «materialer», vis også ALLE egenskaper/parametere per material,
      ikke bare navn og type.
    • Vær ALLTID grundig: vis verdi, enhet, og kontekst for hvert element.

    REGLER:
    • Returner ALLTID KUN ren Python-kode som kan kjøres med variablene `g` (PLAXIS global)
      og `s` (server-objekt fra plxscripting).
    • INGEN markdown, INGEN ```-blokker, INGEN forklarende tekst, INGEN import-setninger.
    • ALDRI kall `g.new()` — operer på det eksisterende prosjektet i `g`.
    • ALDRI kall `new_server()` — tilkoblingen er allerede opprettet.
    • Bruk variablene `g` og `s` (IKKE `g_i`/`s_i`) med mindre brukeren ber om output.
      For output-operasjoner, bruk `g_o` og `s_o` som allerede er tilgjengelige.
    • Følg signaturene og eksemplene i API-kortene som er oppgitt nedenfor.
    • Skriv grundig, deterministisk kode.  Inkluder `print()` for ALT brukeren trenger.
    • Dersom brukeren ber om å «hente» / «extrahere» / «liste» data, skriv kode som samler
      resultatene i en variabel og `print()`-er dem MED ALLE detaljer.
    • Dersom brukeren ber om å «lage» / «opprette» / «endre», skriv kode som utfører
      handlingen direkte på modellen via g / s.

    VIKTIG — OUTPUT-FORMAT:
    Hver logisk gruppe med data skal ha en overskrift på formen:
        print("=== SEKSJONSNAVN ===")
    Hvert element i en gruppe skal være på én linje med format:
        print("ITEM: verdi1 | verdi2 | verdi3")
    Slik at resultater kan parses strukturert.

    VIKTIG — PLAXIS PYTHON SCRIPTING-MØNSTRE:
    KRITISK: Ikke alle Plaxis-prosjekter har alle objekttyper.  Noen samlinger
    (f.eks. g.Boreholes, g.Geogrids) finnes IKKE i alle modeller.
    Du MÅ ALLTID pakke inn hver seksjon i try/except slik at koden fortsetter
    selv om en samling mangler.

    Bruk ALLTID iterasjon over samlinger (g.Plates, g.Phases, g.Materials osv.)
    for å hente faktisk data — g.info() gir bare en metadataoversikt og er ALDRI nok.

    VIKTIG — GEOMETRI & RESULTATER:
    For plater: bruk attributter som plate.Parent.x, plate.Parent.y, etc.
    Prøv ALLTID å hente geometri via flere tilnærminger:
      1) plate.Parent.Points[0].x, plate.Parent.Points[1].x
      2) g.tabulate(plate, "x y")
      3) g_o.getresults(plate, phase, g_o.ResultTypes.Plate.X)
    Dersom en tilnærming gir tomme resultater, prøv næste.

    For resultater (krefter/momenter), sjekk ALLTID at beregningen er kjørt:
      - Sjekk phase.ShouldCalculate, phase.Identification
      - Bruk g_o/s_o for output-resultater (IKKE g/s)
""")

# ---------------------------------------------------------------------------
# LLM client helpers
# ---------------------------------------------------------------------------

_client = None


def _get_client():
    """Return an Azure OpenAI client (preferred) or fall back to plain OpenAI."""
    global _client
    if _client is not None:
        return _client, AZURE_OPENAI_DEPLOYMENT or OPENAI_MODEL

    if AZURE_OPENAI_API_KEY and AZURE_OPENAI_ENDPOINT:
        _client = AzureOpenAI(
            api_key=AZURE_OPENAI_API_KEY,
            azure_endpoint=AZURE_OPENAI_ENDPOINT,
            api_version=AZURE_OPENAI_API_VERSION,
        )
        return _client, AZURE_OPENAI_DEPLOYMENT
    elif OPENAI_API_KEY:
        from openai import OpenAI
        _client = OpenAI(api_key=OPENAI_API_KEY)
        return _client, OPENAI_MODEL
    else:
        raise RuntimeError(
            "Ingen AI-nøkkel konfigurert.  Sett AZURE_OPENAI_API_KEY + AZURE_OPENAI_ENDPOINT "
            "eller OPENAI_API_KEY i .env."
        )


def _strip_code_fences(text: str) -> str:
    """Remove markdown code fences if the LLM accidentally included them."""
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:python)?\s*\n?", "", text)
        text = re.sub(r"\n?```\s*$", "", text)
    return text.strip()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_code(
    user_message: str,
    history: Optional[List[Dict[str, str]]] = None,
    pdf_text: Optional[str] = None,
    selected_context: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Generate Plaxis Python code for *user_message*.

    Args:
        user_message:     The natural-language request from the user.
        history:          Previous conversation turns ``[{"role": …, "content": …}, …]``.
        pdf_text:         Extracted text from an uploaded PDF to include as context.
        selected_context: Items the user selected from the findings panel to
                          include as extra context in the prompt.

    Returns:
        ``{"code": str, "api_cards": str, "docs_used": list[str]}``
    """
    docs = retrieve_docs(user_message, k=4)
    api_cards = build_api_cards(docs)
    docs_used = [d.get("name", "") for d in docs]

    messages: List[Dict[str, str]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
    ]

    if api_cards:
        messages.append({"role": "system", "content": f"API-kort (referanse):\n{api_cards}"})

    if selected_context:
        ctx_text = "\n".join(f"• {item}" for item in selected_context)
        messages.append({
            "role": "system",
            "content": (
                "Brukeren har valgt følgende elementer fra tidligere resultater "
                "som kontekst. Bruk disse aktivt i svaret ditt:\n" + ctx_text
            ),
        })

    if pdf_text:
        # Truncate to avoid token overflow
        truncated = pdf_text[:8000]
        messages.append({
            "role": "system",
            "content": f"Innhold fra brukerens opplastede dokument:\n{truncated}",
        })

    # Append conversation history
    if history:
        messages.extend(history)

    messages.append({"role": "user", "content": user_message})

    client, model = _get_client()
    resp = client.chat.completions.create(
        model=model,
        messages=messages,
        max_completion_tokens=4096,
    )

    code = _strip_code_fences(resp.choices[0].message.content or "")
    return {"code": code, "api_cards": api_cards, "docs_used": docs_used}


def generate_code_with_retry(
    user_message: str,
    history: Optional[List[Dict[str, str]]] = None,
    pdf_text: Optional[str] = None,
    selected_context: Optional[List[str]] = None,
    error_message: Optional[str] = None,
    failed_code: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Retry code generation after a previous execution failure.

    Appends the failed code and error message to the conversation so the LLM
    can self-correct.
    """
    retry_history = list(history or [])
    if failed_code:
        retry_history.append({"role": "assistant", "content": failed_code})
    if error_message:
        retry_history.append({
            "role": "user",
            "content": (
                f"Koden over feilet med denne meldingen:\n{error_message}\n\n"
                "Rett opp og gi ny KUN-kode basert på API-kortene og reglene."
            ),
        })
    return generate_code(
        user_message, history=retry_history, pdf_text=pdf_text,
        selected_context=selected_context,
    )


# ---------------------------------------------------------------------------
# Code execution via PlaxisWorker job queue
# ---------------------------------------------------------------------------

import json
import time

from core.database import get_db_session
from core.models import PlaxisJob
from activities.plaxis.script_builder import build_agent_exec_script

# Safety: do not allow dangerous patterns in agent-generated code
_BLOCKED_PATTERNS = [
    re.compile(r"\bg\.new\s*\("),        # creating new project
    re.compile(r"\bnew_server\s*\("),     # opening new connection
    re.compile(r"\bimport\s+os\b"),       # filesystem access
    re.compile(r"\bimport\s+subprocess"), # shell access
    re.compile(r"\bopen\s*\("),           # file I/O
    re.compile(r"\b__import__\s*\("),     # dynamic imports
    re.compile(r"\beval\s*\("),           # eval
]


def _check_safety(code: str) -> str | None:
    """Return an error message if *code* contains a blocked pattern, else None."""
    for pat in _BLOCKED_PATTERNS:
        if pat.search(code):
            return f"Blokkert: koden inneholder et forbudt mønster ({pat.pattern})."
    return None


def execute_via_worker(
    code: str,
    connection_params: Dict[str, Any],
    session_id: str = "default",
    timeout: int = 7200,
) -> Dict[str, Any]:
    """
    Execute agent-generated code through the PlaxisWorker job queue.

    1. Check safety
    2. Wrap code with Plaxis connection (build_agent_exec_script)
    3. Submit as PlaxisJob
    4. Poll DB until worker finishes
    5. Return ``{"success": bool, "output": str, "error": str | None}``
    """
    if not code or not code.strip():
        return {"success": False, "output": "", "error": "Ingen kode å kjøre."}

    safety_err = _check_safety(code)
    if safety_err:
        return {"success": False, "output": "", "error": safety_err}

    # Build self-contained script
    script = build_agent_exec_script(
        host=connection_params["host"],
        port=connection_params["port"],
        password=connection_params["password"],
        output_port=connection_params.get("output_port"),
        output_password=connection_params.get("output_password"),
        agent_code=code,
    )

    # Submit to job queue
    db = get_db_session()
    try:
        job = PlaxisJob(
            session_id=session_id,
            job_type="agent_exec",
            code=script,
            status="pending",
        )
        db.add(job)
        db.commit()
        job_id = job.id
    except Exception as exc:
        db.rollback()
        return {"success": False, "output": "", "error": f"Kunne ikke opprette jobb: {exc}"}
    finally:
        db.close()

    # Poll for result
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        time.sleep(1.0)
        db = get_db_session()
        try:
            job = db.query(PlaxisJob).filter(PlaxisJob.id == job_id).first()
            if not job:
                return {"success": False, "output": "", "error": "Jobb forsvant fra databasen."}
            if job.status == "done":
                result = json.loads(job.result_json) if job.result_json else {}
                return {
                    "success": result.get("success", False),
                    "output": result.get("output", ""),
                    "error": result.get("error"),
                }
            if job.status == "failed":
                return {
                    "success": False,
                    "output": "",
                    "error": job.error or "Jobb feilet i PlaxisWorker.",
                }
        finally:
            db.close()

    return {
        "success": False,
        "output": "",
        "error": f"Tidsavbrudd — PlaxisWorker svarte ikke innen {timeout}s. Kjører PlaxisWorker?",
    }


def _analyze_output(output: str) -> Dict[str, Any]:
    """
    Analyze execution output to decide if the agent should continue.

    Returns:
        {
            "has_data": bool,          # True if meaningful data was found
            "has_question": bool,      # True if the agent asks the user something
            "question": str | None,    # The question text if any
            "is_done": bool,           # True if '# FERDIG' marker found
            "empty_sections": list,    # Section names with no items
            "data_sections": list,     # Section names with items
        }
    """
    lines = output.splitlines()
    empty_sections = []
    data_sections = []
    current_section = None
    current_has_items = False
    has_question = False
    question = None
    is_done = False

    for line in lines:
        stripped = line.strip()

        # Check for question
        if stripped.startswith("SPØRSMÅL:"):
            has_question = True
            question = stripped[len("SPØRSMÅL:"):].strip()

        # Check for done marker
        if "# FERDIG" in stripped or stripped == "FERDIG":
            is_done = True

        # Parse sections
        sec_match = re.match(r'^===\s*(.+?)\s*===$', stripped)
        if sec_match:
            if current_section is not None:
                if current_has_items:
                    data_sections.append(current_section)
                else:
                    empty_sections.append(current_section)
            current_section = sec_match.group(1)
            current_has_items = False
        elif current_section and stripped.startswith("ITEM:"):
            current_has_items = True

    # Last section
    if current_section is not None:
        if current_has_items:
            data_sections.append(current_section)
        else:
            empty_sections.append(current_section)

    has_data = len(data_sections) > 0

    return {
        "has_data": has_data,
        "has_question": has_question,
        "question": question,
        "is_done": is_done,
        "empty_sections": empty_sections,
        "data_sections": data_sections,
    }


def _generate_next_step(
    user_message: str,
    step_history: List[Dict[str, str]],
    analysis: Dict[str, Any],
    step_num: int,
    pdf_text: Optional[str] = None,
    selected_context: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Generate code for the next step based on previous step results.
    """
    # Build continuation prompt
    if analysis["has_question"]:
        # Agent asked the user something — we stop and ask
        return {"code": "", "stop_reason": "question", "question": analysis["question"]}

    continuation = []
    if not analysis["has_data"] and analysis["empty_sections"]:
        continuation.append(
            f"Steg {step_num - 1} ga TOMME seksjoner: {', '.join(analysis['empty_sections'])}. "
            "Dataene var tomme.  Prøv en ANNEN tilnærming for å hente disse dataene. "
            "Utforsk andre attributter eller metoder.  Ikke gi opp — prøv alternative "
            "Plaxis API-kall."
        )
    elif analysis["has_data"] and not analysis["is_done"]:
        continuation.append(
            f"Steg {step_num - 1} hentet data i: {', '.join(analysis['data_sections'])}. "
            "Nå har du fakta fra modellen.  Basert på disse resultatene, "
            "utfør NESTE logiske steg for å fullføre brukerens forespørsel. "
            "Dersom brukeren ba om optimalisering/analyse: analyser dataene, "
            "beregn nøkkelverdier, og gi en KONKRET anbefaling med begrunnelse. "
            "Dersom du trenger resultater fra output (krefter, momenter), bruk g_o/s_o. "
            "Skriv '# FERDIG' som siste kommentar når du er ferdig."
        )

    if continuation:
        step_history.append({
            "role": "user",
            "content": "\n".join(continuation),
        })

    return generate_code(
        user_message=user_message,
        history=step_history,
        pdf_text=pdf_text,
        selected_context=selected_context,
    )


# ---------------------------------------------------------------------------
# Reference validation — check generated code against plaxis_2d_reference.md
# ---------------------------------------------------------------------------

_VALIDATION_PROMPT = textwrap.dedent("""\
    Du er en Plaxis API-ekspert.  Du har fått generert Python-kode og relevante
    referansekort fra den offisielle Plaxis 2D Python-dokumentasjonen.

    Din jobb er å VALIDERE koden mot referansen og returnere KORRIGERT kode.

    SJEKK:
    1. Er API-kall korrekte? (riktig metode-navn, riktig antall argumenter, riktig rekkefølge)
    2. Er property-tilganger korrekte? (f.eks. .value, .Identification, .Parent)
    3. Er variabelnavn konsistente? (g/s for input, g_o/s_o for output)
    4. Er det vanlige feil? (f.eks. manglende .value, feil fase-referanse, feil ResultType)
    5. Brukes try/except rundt samlinger som kanskje ikke finnes?
    6. Er rekkefølgen av operasjoner riktig? (f.eks. gotostages() før faseoperasjoner)

    REGLER:
    • Returner KUN korrigert Python-kode — INGEN forklaring, INGEN markdown.
    • Hvis koden er korrekt, returner den UENDRET.
    • Behold ALL funksjonalitet — bare fiks feil.
    • ALDRI legg til nye features eller endre intensjonen.
    • Bruk g og s (IKKE g_i/s_i) for input, g_o og s_o for output.
""")


def _validate_against_reference(code: str) -> str:
    """
    Validate generated code against plaxis_2d_reference.md.

    Looks up all API calls in the reference, then asks the LLM to verify
    and correct the code. Returns corrected code.
    """
    ref_cards = retrieve_reference_for_code(code)
    if not ref_cards:
        return code  # No reference found — return as-is

    messages: List[Dict[str, str]] = [
        {"role": "system", "content": _VALIDATION_PROMPT},
        {"role": "system", "content": f"Referansekort fra Plaxis-dokumentasjonen:\n\n{ref_cards}"},
        {"role": "user", "content": (
            f"Valider og korriger denne koden:\n\n```python\n{code}\n```\n\n"
            "Returner den korrigerte koden (eller uendret hvis den er korrekt)."
        )},
    ]

    client, model = _get_client()
    resp = client.chat.completions.create(
        model=model,
        messages=messages,
        max_completion_tokens=4096,
    )

    validated = _strip_code_fences(resp.choices[0].message.content or "")
    if not validated or len(validated) < len(code) * 0.3:
        # Validation likely failed — return original
        return code
    return validated


# ---------------------------------------------------------------------------
# Session observer — continuously updates a session .md knowledge file
# ---------------------------------------------------------------------------

_OBSERVER_PROMPT = textwrap.dedent("""\
    Du er en teknisk observatør som følger en PLAXIS AI-agent-sesjon.
    Du mottar informasjon om hva som skjedde i siste steg, og din jobb er å
    oppdatere en løpende session-logg i markdown-format.

    Loggen skal inneholde:
    1. **Oppsummering**: Hva brukeren ba om (kort)
    2. **Modellstatus**: Hva vi vet om PLAXIS-modellen (materialer, faser, strukturer)
    3. **Utførte steg**: Hva som er gjort så langt (kronologisk)
    4. **Viktige funn**: Data, verdier, problemer som er oppdaget
    5. **Advarsler**: Ting å passe på, potensielle feil, manglende data
    6. **Neste steg**: Hva som bør gjøres videre

    REGLER:
    • Returner HELE den oppdaterte markdown-filen — ikke bare endringer.
    • Hold det KOMPAKT — maks 200 linjer.
    • Bruk norsk.
    • Vær PRESIS med verdier og tekniske detaljer.
    • Oppdater eksisterende seksjoner — ikke bare legg til.
""")

# In-memory observer state per session
_observer_logs: Dict[str, str] = {}  # session_id -> markdown content


def _update_observer(
    session_id: str,
    user_message: str,
    step_num: int,
    action: str,
    code: str,
    output: str,
    error: Optional[str],
    docs_used: List[str],
) -> str:
    """
    Update the session observer log after a step.

    Returns the updated markdown content.
    """
    current_log = _observer_logs.get(session_id, "")

    # Build the update context
    update_info = (
        f"## Siste hendelse\n"
        f"- **Steg**: {step_num}\n"
        f"- **Handling**: {action}\n"
        f"- **Brukerforespørsel**: {user_message[:200]}\n"
        f"- **Kode utført**: {len(code.splitlines())} linjer\n"
        f"- **Output**: {len(output.splitlines())} linjer\n"
        f"- **Feil**: {error or 'Ingen'}\n"
        f"- **Dokumenter brukt**: {', '.join(docs_used) or 'Ingen'}\n"
    )

    if output:
        update_info += f"\n### Output (utdrag):\n```\n{output[:2000]}\n```\n"
    if code:
        update_info += f"\n### Kode (utdrag):\n```python\n{code[:1500]}\n```\n"

    messages: List[Dict[str, str]] = [
        {"role": "system", "content": _OBSERVER_PROMPT},
    ]

    if current_log:
        messages.append({
            "role": "user",
            "content": (
                f"Her er den nåværende session-loggen:\n\n{current_log}\n\n---\n\n"
                f"Oppdater loggen basert på dette nye steget:\n\n{update_info}"
            ),
        })
    else:
        messages.append({
            "role": "user",
            "content": (
                f"Start en ny session-logg basert på dette første steget:\n\n{update_info}"
            ),
        })

    try:
        client, model = _get_client()
        resp = client.chat.completions.create(
            model=model,
            messages=messages,
            max_completion_tokens=2048,
        )
        updated_log = resp.choices[0].message.content or ""
        # Strip any markdown fences the LLM might wrap around
        updated_log = _strip_code_fences(updated_log) if updated_log.startswith("```") else updated_log
        _observer_logs[session_id] = updated_log
        return updated_log
    except Exception:
        # Observer failure should never block the main pipeline
        return current_log


def get_observer_log(session_id: str) -> str:
    """Get the current observer log for a session."""
    return _observer_logs.get(session_id, "")


def chat_and_execute(
    user_message: str,
    connection_params: Dict[str, Any],
    session_id: str = "default",
    history: Optional[List[Dict[str, str]]] = None,
    pdf_text: Optional[str] = None,
    selected_context: Optional[List[str]] = None,
    max_retries: int = 2,
    max_steps: int = 5,
) -> Dict[str, Any]:
    """
    Multi-step agent loop that executes through PlaxisWorker:
      1. Generate code for current step
      2. Execute via worker job queue
      3. If execution fails → retry with error feedback (up to max_retries)
      4. If execution succeeds → analyze output
      5. Accumulate all output across steps
    """
    all_output_parts = []
    all_code_parts = []
    all_docs_used = []
    thinking_log: List[Dict[str, str]] = []   # [{step, action, detail}, …]
    total_attempts = 0
    step_history = list(history or [])

    def _log(step_n: int, action: str, detail: str):
        thinking_log.append({"step": step_n, "action": action, "detail": detail})

    def _make_result(**overrides) -> Dict[str, Any]:
        base = {
            "code": "\n\n".join(all_code_parts),
            "output": "\n".join(all_output_parts),
            "success": True,
            "error": None,
            "attempts": total_attempts,
            "steps": 0,
            "docs_used": list(dict.fromkeys(all_docs_used)),
            "thinking": thinking_log,
            "observer_log": _observer_logs.get(session_id, ""),
        }
        base.update(overrides)
        return base

    for step in range(1, max_steps + 1):
        # --- Generate code for this step ---
        if step == 1:
            _log(step, "🔍 Analyserer forespørsel",
                 f"Brukerens melding: «{user_message[:120]}»")
            _log(step, "📚 Henter dokumentasjon",
                 "Søker i Plaxis API-indeksen etter relevante kommandoer…")
            gen_result = generate_code(
                user_message, history=step_history, pdf_text=pdf_text,
                selected_context=selected_context,
            )
            docs_names = [d for d in gen_result.get("docs_used", []) if d]
            if docs_names:
                _log(step, "📖 Fant dokumenter",
                     ", ".join(docs_names))
            _log(step, "🧠 Genererer kode",
                 f"LLM genererer Python-kode for steg {step}…")
        else:
            _log(step, "🤔 Vurderer resultater",
                 f"Analyserer output fra steg {step - 1}: "
                 f"{len(analysis.get('data_sections', []))} seksjoner med data, "
                 f"{len(analysis.get('empty_sections', []))} tomme seksjoner")
            gen_result = _generate_next_step(
                user_message=user_message,
                step_history=step_history,
                analysis=analysis,
                step_num=step,
                pdf_text=pdf_text,
                selected_context=selected_context,
            )
            # Check if the generator said to stop (question)
            if gen_result.get("stop_reason") == "question":
                _log(step, "❓ Trenger svar fra bruker",
                     gen_result.get("question", ""))
                return _make_result(
                    steps=step - 1,
                    question=gen_result.get("question"),
                )
            _log(step, "🧠 Genererer kode",
                 f"LLM genererer Python-kode for steg {step}…")

        code = gen_result["code"]
        all_docs_used.extend(gen_result.get("docs_used", []))

        # --- Validate against plaxis_2d_reference.md ---
        _log(step, "📖 Validerer mot manualen",
             "Sjekker API-kall mot Plaxis 2D-referansen…")
        try:
            validated_code = _validate_against_reference(code)
            if validated_code != code:
                _log(step, "✏️ Kode korrigert",
                     "Referansevalidering fant og rettet API-feil")
                code = validated_code
            else:
                _log(step, "✅ Validering OK",
                     "Koden samsvarer med referansedokumentasjonen")
        except Exception as val_err:
            _log(step, "⚠️ Validering hoppet over",
                 f"Kunne ikke validere: {str(val_err)[:100]}")

        # --- Execute with retries ---
        exec_result = None
        for attempt in range(1, max_retries + 2):
            total_attempts += 1
            _log(step, "▶️ Kjører kode",
                 f"Forsøk {attempt} — kjører {len(code.splitlines())} linjer via PlaxisWorker…")
            exec_result = execute_via_worker(code, connection_params, session_id)

            if exec_result["success"]:
                output_lines = len(exec_result.get("output", "").splitlines())
                _log(step, "✅ Kode kjørt OK",
                     f"Fikk {output_lines} linjer output")
                break

            _log(step, "❌ Feil ved kjøring",
                 exec_result.get("error", "ukjent feil")[:200])

            if attempt > max_retries:
                break

            _log(step, "🔄 Prøver på nytt",
                 "Sender feilmelding til LLM for ny kode…")
            retry = generate_code_with_retry(
                user_message,
                history=step_history,
                pdf_text=pdf_text,
                selected_context=selected_context,
                error_message=exec_result["error"],
                failed_code=code,
            )
            code = retry["code"]

        # If execution failed after all retries, return what we have
        if not exec_result["success"]:
            all_code_parts.append(code)
            all_output_parts.append(exec_result.get("output", ""))
            _log(step, "⛔ Ga opp etter retries",
                 f"Mislyktes etter {total_attempts} forsøk")
            return _make_result(
                success=False, error=exec_result["error"], steps=step,
            )

        # --- Execution succeeded — analyze output ---
        step_output = exec_result["output"]
        all_code_parts.append(code)
        all_output_parts.append(step_output)

        # Add to step history so the LLM sees what happened
        step_history.append({"role": "assistant", "content": code})
        step_history.append({
            "role": "user",
            "content": f"Koden ble kjørt.  Output fra steg {step}:\n{step_output[:4000]}",
        })

        analysis = _analyze_output(step_output)

        # --- Update session observer ---
        _log(step, "📝 Oppdaterer observatør",
             "Oppdaterer session-loggen med resultater fra dette steget…")
        try:
            _update_observer(
                session_id=session_id,
                user_message=user_message,
                step_num=step,
                action="Kjørt kode" if analysis["has_data"] else "Feil/tomme data",
                code=code,
                output=step_output,
                error=None,
                docs_used=all_docs_used,
            )
        except Exception:
            pass  # Observer failure must never block the main pipeline

        # Check if agent asked the user a question
        if analysis["has_question"]:
            _log(step, "❓ Trenger svar fra bruker", analysis["question"])
            return _make_result(
                steps=step,
                question=analysis["question"],
            )

        # Check if agent signalled it's done
        if analysis["is_done"]:
            _log(step, "🏁 Ferdig", "Agenten signaliserte at oppgaven er fullført")
            break

        # Decide whether to continue to next step
        if step == 1 and analysis["has_data"]:
            _complex_kw = re.compile(
                r"optim|analys|endre|flytt|beregn|dimesjon|evaluer|vurder|"
                r"forbedre|reduser|sammenlign|finn.*beste|finn.*optimal",
                re.IGNORECASE,
            )
            if _complex_kw.search(user_message):
                _log(step, "🔄 Fortsetter",
                     "Kompleks forespørsel — trenger flere steg for analyse/optimalisering")
                continue
            else:
                _log(step, "🏁 Ferdig",
                     "Enkel forespørsel — data hentet, ingen videre steg nødvendig")
                break

        # Later steps: stop if we got data with no empties
        if analysis["has_data"] and not analysis["empty_sections"]:
            _log(step, "🏁 Ferdig",
                 f"Alle seksjoner har data: {', '.join(analysis['data_sections'])}")
            break
        elif analysis["empty_sections"]:
            _log(step, "🔄 Fortsetter",
                 f"Tomme seksjoner: {', '.join(analysis['empty_sections'])} — prøver på nytt")

    # --- Cleanup step: reformat accumulated output ---
    raw_output = "\n".join(all_output_parts)
    if raw_output.strip():
        _log(step + 1, "🧹 Rydder opp",
             "Sender all output til LLM for opprydding og formatering…")
        try:
            cleanup_code = _generate_cleanup(raw_output, user_message)
            if cleanup_code:
                total_attempts += 1
                cleanup_result = execute_via_worker(cleanup_code, connection_params, session_id)
                if cleanup_result["success"] and cleanup_result["output"].strip():
                    _log(step + 1, "✅ Opprydding ferdig",
                         f"Formatert output: {len(cleanup_result['output'].splitlines())} linjer")
                    all_output_parts.clear()
                    all_output_parts.append(cleanup_result["output"])
                    all_code_parts.append(cleanup_code)
                else:
                    _log(step + 1, "⚠️ Opprydding feilet",
                         "Bruker original output i stedet")
        except Exception:
            _log(step + 1, "⚠️ Opprydding hoppet over",
                 "Kunne ikke formatere — bruker original output")

    return _make_result(steps=step)


# ---------------------------------------------------------------------------
# Cleanup prompt — for the final formatting pass
# ---------------------------------------------------------------------------

_CLEANUP_PROMPT = textwrap.dedent("""\
    Du er en oppryddingsassistent.  Du har nettopp fått rå output fra en Plaxis-agent.
    Din eneste jobb er å reorganisere og formatere denne outputen til et rent, lesbart format.

    REGLER:
    • Returner KUN ren Python-kode som printer det ryddige resultatet.
    • INGEN Plaxis API-kall — bare print()-setninger med de ryddige dataene.
    • Behold ALLE data — ikke fjern noe!  Bare omorganiser og formater.
    • Fjern duplikater, tomme linjer, og irrelevant støy.
    • Grupper relaterte data under klare overskrifter.

    OUTPUT-FORMAT (MÅ følges):
    print("=== SEKSJONSNAVN ===")
    print("ITEM: felt1 | felt2 | felt3")

    EKSEMPEL — fra rotete input:
        Prosjekt: TestProsjekt123
        Plates[0] - Plate_1
        Plate_1 material = ConcreteMat  EA = 1.2e7
        Phase_1   Plate_1 M=23.5  N=100.2  Q=15.3
        Phase_1   Plate_1 M=23.5  N=100.2  Q=15.3   (duplikat)

    Til ren output:
        print("=== PROSJEKTINFO ===")
        print("ITEM: Prosjekt | TestProsjekt123")
        print("=== PLATER ===")
        print("ITEM: Plate_1 | Material: ConcreteMat | EA: 1.2e7")
        print("=== RESULTATER ===")
        print("ITEM: Phase_1 | Plate_1 | M: 23.5 | N: 100.2 | Q: 15.3")

    Gjør det RYDDIG, KOMPAKT og LESBART.  Skriv '# FERDIG' til slutt.
""")


def _generate_cleanup(raw_output: str, user_message: str) -> str:
    """
    Ask the LLM to produce a cleanup code that reformats *raw_output*.

    Returns Python code (only print statements) or empty string on failure.
    """
    # Truncate very long output to avoid token overflow
    truncated = raw_output[:12000]

    messages: List[Dict[str, str]] = [
        {"role": "system", "content": _CLEANUP_PROMPT},
        {"role": "user", "content": (
            f"Brukeren spurte: «{user_message[:200]}»\n\n"
            f"Rå output fra agenten:\n```\n{truncated}\n```\n\n"
            "Reorganiser og formater dette til et rent, strukturert format "
            "med ==='SEKSJON'=== overskrifter og ITEM:-linjer.  "
            "Returner KUN Python print()-kode."
        )},
    ]

    client, model = _get_client()
    resp = client.chat.completions.create(
        model=model,
        messages=messages,
        max_completion_tokens=4096,
    )

    code = _strip_code_fences(resp.choices[0].message.content or "")
    if not code or "print" not in code:
        return ""
    return code
