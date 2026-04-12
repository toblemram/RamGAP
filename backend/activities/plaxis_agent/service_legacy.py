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
    timeout: int = 180,
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
