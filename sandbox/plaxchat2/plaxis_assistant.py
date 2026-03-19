import os
import json
import sqlite3
import re
from typing import List, Dict, Tuple
import numpy as np

import customtkinter as ctk
from tkinter import messagebox
from dotenv import load_dotenv
from openai import OpenAI
from plxscripting.easy import new_server

import faiss


# ==================== Oppsett & konfig ====================
load_dotenv()

# ---- Viktig: les API-nøkkel fra .env ----
API_KEY = os.getenv("OPENAI_API_KEY")  # Sett i .env: OPENAI_API_KEY=sk-...
if not API_KEY:
    raise RuntimeError("OPENAI_API_KEY mangler i .env")

# Modellvalg
MODEL = os.getenv("GEN_MODEL", "gpt-5")
EMBED_MODEL = os.getenv("EMBED_MODEL", "text-embedding-3-large")  # beste for kode/tekst (3072 dim)

# PLAXIS
DEFAULT_HOST = "localhost"
DEFAULT_PORT = 10000
DEFAULT_PWD  = ""                # PLAXIS-passord (Code) hvis du bruker det
DEFAULT_MAX_TOKENS = 6000        # sett høyt, men ikke helt maks for latency

DEMO_AUTORUN = False             # sett True hvis du vil auto-kjøre etter tilkobling

# Kunnskapsbase
KNOWLEDGE_DIR = os.getenv("KNOWLEDGE_DIR", "plaxis_knowledge")
DB_FILE       = os.getenv("DB_FILE", "plaxis.db")
IDX_SHORT     = os.getenv("IDX_SHORT", "faiss_short.index")
IDX_FULL      = os.getenv("IDX_FULL",  "faiss_full.index")
IDS_FILE      = os.getenv("IDS_FILE",  "doc_ids.json")
FORCE_REINDEX = os.getenv("FORCE_REINDEX", "false").lower() == "true"

client = OpenAI(api_key=API_KEY)


# ==================== Global tilstand ====================
# PLAXIS-tilkobling
s = None
g = None

# Siste genererte kode (vises i "Kode"-fanen)
last_code = ""

# In-memory kunnskapsbase for rask oppslag
DOCS_INDEX: Dict[str, Dict] = {}  # id -> document dict
DOC_IDS: List[str] = []           # i samme rekkefølge som FAISS
FAISS_SHORT = None                # cosine index over kort tekst
FAISS_FULL  = None                # cosine index over full tekst


# ==================== Hjelpere: Kunnskapsbase ====================
def list_json_files(root: str):
    if not os.path.isdir(root):
        return []
    return [os.path.join(root, name) for name in os.listdir(root) if name.endswith(".json")]

def load_doc_file(path: str) -> Dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def normalize_ws(s: str) -> str:
    return re.sub(r"\s+", " ", s or "").strip()

def doc_title(doc: Dict) -> str:
    return f"{doc.get('object','')}.{doc.get('method','')}"

def signatures_text(doc: Dict) -> str:
    sigs = []
    for v in doc.get("signature_variants", []):
        args = ", ".join(v.get("args", []))
        ret  = v.get("returns", "")
        sigs.append(f"{args} -> {ret}")
    return " | ".join(sigs)

def examples_text(doc: Dict, max_len: int = 2000) -> str:
    """Samle eksempler, men kutt hvis veldig langt."""
    exs = "\n".join(doc.get("minimal_examples", []))
    return exs[:max_len]

def embed_text(text: str) -> np.ndarray:
    text = text or ""
    vec = client.embeddings.create(model=EMBED_MODEL, input=text).data[0].embedding
    x = np.asarray(vec, dtype="float32")
    # Normaliser for cosine/IP
    norm = np.linalg.norm(x)
    if norm == 0.0:
        return x
    return x / norm

def faiss_index_ip(dim: int):
    # IP (dot-product) + normaliserte vektorer gir cosine-likhet
    return faiss.IndexFlatIP(dim)

def build_indexes():
    """
    Leser alle JSON-dokumenter, bygger:
      - SQLite FTS5 (BM25) over tittel/objekt/metode/aliases/innhold
      - FAISS 'short' (title + synopsis + aliases)
      - FAISS 'full'  (short + signaturer + eksempler)
    Lagrer til disk og laster inn i minnet.
    """
    global DOCS_INDEX, DOC_IDS, FAISS_SHORT, FAISS_FULL

    os.makedirs(os.path.dirname(DB_FILE) or ".", exist_ok=True)

    # Les dokumenter
    doc_paths = list_json_files(KNOWLEDGE_DIR)
    if not doc_paths:
        raise RuntimeError(f"Fant ingen .json-filer i {KNOWLEDGE_DIR}. Legg inn kunnskapsbasen først.")

    docs: List[Dict] = []
    for p in doc_paths:
        d = load_doc_file(p)
        # Normaliser litt
        d["id"] = d["id"].strip()
        d["object"] = d["object"].strip()
        d["method"] = d["method"].strip()
        d["synopsis"] = d.get("synopsis", "")
        d["aliases"] = d.get("aliases", [])
        docs.append(d)
        DOCS_INDEX[d["id"]] = d

    # --- SQLite FTS5 ---
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS docs_fts")
    cur.execute("""
        CREATE VIRTUAL TABLE docs_fts USING fts5(
            id, title, object, method, aliases, content,
            tokenize = 'unicode61 remove_diacritics 2 tokenchars "-_."'
        )
    """)

    # --- FAISS for short og full ---
    # Dim følger embedding-modell (text-embedding-3-large = 3072)
    # Vi embedder første korttekst for å finne dim
    probe = embed_text("probe")
    dim = probe.shape[0]
    FAISS_SHORT = faiss_index_ip(dim)
    FAISS_FULL  = faiss_index_ip(dim)

    short_vecs = []
    full_vecs  = []
    DOC_IDS = []

    for d in docs:
        _title = doc_title(d)
        _aliases = " ".join(d.get("aliases", []))
        _synopsis = normalize_ws(d.get("synopsis", ""))

        short_text = normalize_ws(f"{_title} {_synopsis} {_aliases}")
        sigs = signatures_text(d)
        exs  = examples_text(d)
        full_text  = normalize_ws(f"{short_text} {sigs} {exs}")

        e_short = embed_text(short_text)
        e_full  = embed_text(full_text)

        FAISS_SHORT.add(e_short.reshape(1, -1))
        FAISS_FULL.add(e_full.reshape(1, -1))

        short_vecs.append(e_short)
        full_vecs.append(e_full)
        DOC_IDS.append(d["id"])

        # Innhold for FTS
        cur.execute(
            "INSERT INTO docs_fts (id, title, object, method, aliases, content) VALUES (?, ?, ?, ?, ?, ?)",
            (d["id"], _title, d["object"], d["method"], _aliases, f"{_synopsis} {sigs} {exs}")
        )

    conn.commit()
    conn.close()

    # Lagre FAISS og id-liste
    faiss.write_index(FAISS_SHORT, IDX_SHORT)
    faiss.write_index(FAISS_FULL, IDX_FULL)
    with open(IDS_FILE, "w", encoding="utf-8") as f:
        json.dump(DOC_IDS, f, ensure_ascii=False, indent=2)

def ensure_indexes_loaded():
    """
    Laster eksisterende indekser hvis de finnes.
    Hvis noe mangler (eller FORCE_REINDEX=True), bygg på nytt.
    """
    need_build = FORCE_REINDEX or \
                 (not os.path.exists(IDX_SHORT)) or \
                 (not os.path.exists(IDX_FULL)) or \
                 (not os.path.exists(IDS_FILE)) or \
                 (not os.path.exists(DB_FILE))

    # Last DOCS_INDEX for rask doc-id -> doc
    if not DOCS_INDEX:
        for p in list_json_files(KNOWLEDGE_DIR):
            d = load_doc_file(p)
            DOCS_INDEX[d["id"]] = d

    if need_build:
        add_chat_safe("system", "Bygger kunnskapsindekser (FAISS + SQLite FTS5) ...")
        build_indexes()

    # Les FAISS + id-liste
    global FAISS_SHORT, FAISS_FULL, DOC_IDS
    FAISS_SHORT = faiss.read_index(IDX_SHORT)
    FAISS_FULL  = faiss.read_index(IDX_FULL)
    with open(IDS_FILE, "r", encoding="utf-8") as f:
        DOC_IDS = json.load(f)

def hybrid_search(query: str,
                  k_final: int = 4,
                  k_short: int = 4,
                  k_full: int = 6,
                  k_fts: int = 6,
                  w_short: float = 0.25,
                  w_full: float = 0.55,
                  w_fts: float = 0.20) -> List[str]:
    """
    Kombinerer:
      - FAISS 'short' + 'full' (cosine) på normaliserte embeddings
      - SQLite FTS5 BM25
      - Heuristikk-boost for eksakt object.method/metodenavn i spørring
    Returnerer topp k_final id'er.
    """
    ensure_indexes_loaded()
    qv = embed_text(query).reshape(1, -1)

    # FAISS
    hits: Dict[str, float] = {}

    def add_faiss(index, k, w):
        D, I = index.search(qv, k)
        if len(D[0]) == 0:
            return
        dmax = float(D[0].max())
        dmin = float(D[0].min())
        rng  = max(1e-9, dmax - dmin)
        for idx, score in zip(I[0], D[0]):
            if idx < 0:
                continue
            doc_id = DOC_IDS[idx]
            s = (float(score) - dmin) / rng  # [0,1]
            hits[doc_id] = max(hits.get(doc_id, 0.0), w * s)

    add_faiss(FAISS_SHORT, k_short, w_short)
    add_faiss(FAISS_FULL,  k_full,  w_full)

    # FTS5
    try:
        conn = sqlite3.connect(DB_FILE)
        cur = conn.cursor()
        cur.execute("SELECT id, bm25(docs_fts) AS s FROM docs_fts WHERE docs_fts MATCH ? ORDER BY s LIMIT ?", (query, k_fts))
        rows = cur.fetchall()
        for (doc_id, bm25) in rows:
            score = 1.0 / (1.0 + float(bm25))  # høyere er bedre
            hits[doc_id] = max(hits.get(doc_id, 0.0), w_fts * score)
        conn.close()
    except Exception:
        pass

    # Heuristikk-boost: eksakt tittel/metode nevnt i query
    qlow = query.lower()
    try:
        conn = sqlite3.connect(DB_FILE)
        cur = conn.cursor()
        cur.execute("SELECT id, title FROM docs_fts")
        for did, title in cur.fetchall():
            tlow = (title or "").lower()
            if did in hits:
                if tlow and tlow in qlow:
                    hits[did] += 0.8
                meth = tlow.split(".")[-1] if "." in tlow else tlow
                if meth and meth in qlow:
                    hits[did] += 0.4
        conn.close()
    except Exception:
        pass

    ranked = sorted(hits.items(), key=lambda x: x[1], reverse=True)
    return [doc_id for doc_id, _ in ranked[:k_final]]

def load_docs_by_ids(ids: List[str]) -> List[Dict]:
    out = []
    for i in ids:
        d = DOCS_INDEX.get(i)
        if d:
            out.append(d)
    return out

def build_api_cards(docs: List[Dict],
                    max_examples_per_doc: int = 2,
                    max_chars_per_doc: int = 1400,
                    max_total_chars: int = 6000) -> str:
    parts = []
    total = 0
    for d in docs:
        title = f"{d.get('object','')}.{d.get('method','')}  (ID: {d.get('id','')})"
        sigs  = "; ".join([", ".join(v.get("args", [])) + " -> " + v.get("returns","") for v in d.get("signature_variants", [])])
        exs   = (d.get("minimal_examples", []) or [])[:max_examples_per_doc]
        card  = f"[{title}]\nSignaturer: {sigs}\nEksempler:\n" + "\n---\n".join(exs)
        if len(card) > max_chars_per_doc:
            card = card[:max_chars_per_doc] + " …"
        if total + len(card) > max_total_chars:
            break
        parts.append(card)
        total += len(card)
    return "\n\n".join(parts)

def retrieve_docs(query: str, k: int = 4) -> List[Dict]:
    ids = hybrid_search(query, k_final=k)
    return load_docs_by_ids(ids)


# ==================== Prompt-regler ====================
SYSTEM_PROMPT = (
    "Du er en PLAXIS-kodegenerator i et skrivebordsverktøy.\n"
    "- Returner ALLTID KUN ren Python-kode som kan kjøres med g (PLAXIS global) og s (server).\n"
    "- Ingen tekst, ingen markdown, ingen JSON, ingen ```-blokker, ingen kommentarer, ingen print.\n"
    "- Ikke bruk imports. Ikke kall new_server. IKKE kall g.new(). Operer på eksisterende prosjekt i g.\n"
    "- Følg signaturer og eksempler fra API-kortene som er gitt.\n"
    "- Bruk alltid variablene g og s (ikke g_i/s_i). Skriv kort og deterministisk kode.\n"
)

# ==================== LLM (med hybrid-søk & retry) ====================
def call_llm_code_with_retry(user_text: str, max_tokens: int, retries: int = 2) -> str:
    """
    Sender brukerens spørsmål til GPT.
    Slår opp relevante API-kort (hybrid-søk) og injiserer dem i systemkontekst.
    Kjører koden. Hvis den feiler, send feilmeldingen tilbake og prøv på nytt.
    """
    # Hent API-kort via hybrid-søk
    docs = retrieve_docs(user_text, k=4)
    api_cards = build_api_cards(docs, max_examples_per_doc=2)

    attempt = 0
    last_code = ""
    last_error = ""

    while attempt <= retries:
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "system", "content": f"API-kort (referanse):\n{api_cards}"},
            {"role": "user", "content": user_text},
        ]
        if attempt > 0:
            messages += [
                {"role": "system", "content": f"Dette var koden du foreslo:\n{last_code}"},
                {"role": "system", "content": f"Dette var feilmeldingen som kom fra PLAXIS:\n{last_error}"},
                {"role": "user", "content": "Rett opp og gi ny KUN-kode basert på API-kortene og reglene."}
            ]

        resp = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            max_completion_tokens=max_tokens
        )

        code = (resp.choices[0].message.content or "").strip()
        # fjern eventuelle ``` blokker
        if code.startswith("```"):
            code = code.strip("`")
            if code.lower().startswith("python"):
                code = code[6:].lstrip()

        # Forsøk å kjøre koden
        status = run_plaxis_code(code)

        if status == "OK":
            return code  # suksess

        # ellers: lagre feilen og prøv igjen
        last_code = code
        last_error = status
        attempt += 1

    # Hvis alle forsøk feilet
    raise RuntimeError(f"Klarte ikke kjøre koden etter {retries+1} forsøk.\nSiste feilmelding: {last_error}")


# ==================== PLAXIS-tilkobling & eksekvering ====================
def run_plaxis_code(code: str) -> str:
    if not code or not code.strip():
        return "Ingen kode generert."
    if g is None:
        return "Ikke tilkoblet PLAXIS."
    flat = code.replace(" ", "").replace("\t", "")
    if "g.new(" in flat or flat.startswith("g.new"):
        return "Avvist: koden inneholder g.new()."
    try:
        exec_globals = {"g": g, "s": s}
        exec(code, exec_globals, {})
        return "OK"
    except Exception as e:
        msg = str(e)
        if "missing \"Code\"" in msg or "decryption" in msg.lower():
            return ("Server krever en 'Code'/passord for kryptert tilkobling. "
                    "Skriv samme kode i Passord-feltet og koble til på nytt.")
        return f"Feil: {msg}"

def connect_plaxis():
    global s, g
    host = host_var.get().strip()
    port = int(port_var.get())
    pwd  = pwd_var.get()
    try:
        s, g = new_server(host, port, password=pwd)
        status_var.set(f"Tilkoblet: {host}:{port}")
        add_chat("system", f"Koblet til PLAXIS RSS på {host}:{port}.")
        # bygg/lås indekser ved første tilkobling (viser status i logg)
        try:
            ensure_indexes_loaded()
            add_chat("system", "Kunnskapsindekser klare.")
        except Exception as e:
            add_chat("system", f"Kunne ikke bygge/laste indekser: {e}")
        if DEMO_AUTORUN:
            app.after(300, send_and_run)
    except Exception as e:
        status_var.set("Frakoblet")
        messagebox.showerror("PLAXIS-tilkobling feilet", str(e))

def disconnect_plaxis():
    global s, g
    try:
        if s:
            s.close()
    except Exception:
        pass
    s = None
    g = None
    status_var.set("Frakoblet")
    add_chat("system", "Frakoblet fra PLAXIS.")


# ==================== UI (CustomTkinter, farger) ====================
ctk.set_appearance_mode("dark")       # "dark" | "light" | "system"
ctk.set_default_color_theme("green")  # "blue" | "green" | "dark-blue"

app = ctk.CTk()
app.title("Tobs2 – PLAXIS kodeassistent")
app.geometry("1080x720")
app.grid_columnconfigure(0, weight=1)
app.grid_rowconfigure(1, weight=1)

# Toppbar
topbar = ctk.CTkFrame(app, height=64, fg_color="#0b1220")
topbar.grid(row=0, column=0, sticky="nsew")
topbar.grid_columnconfigure(0, weight=1)
topbar.grid_columnconfigure(1, weight=0)

title = ctk.CTkLabel(
    topbar, text="PLAXIS Assistent (AI)",
    font=ctk.CTkFont(size=22, weight="bold"),
    text_color="#9ae6b4",
)
title.grid(row=0, column=0, sticky="w", padx=18, pady=18)

status_var = ctk.StringVar(value="Frakoblet")
status_badge = ctk.CTkLabel(
    topbar, textvariable=status_var,
    fg_color="#1f2937", corner_radius=14, padx=12, pady=6,
    text_color="#e5e7eb"
)
status_badge.grid(row=0, column=1, sticky="e", padx=18)

# Innhold
content = ctk.CTkFrame(app, fg_color="#0e1726")
content.grid(row=1, column=0, sticky="nsew", padx=14, pady=14)
content.grid_columnconfigure(0, weight=0)
content.grid_columnconfigure(1, weight=1)
content.grid_rowconfigure(0, weight=1)

# Venstre kort (tilkobling)
left = ctk.CTkFrame(content, fg_color="#12354a", corner_radius=16)
left.grid(row=0, column=0, sticky="nsw", padx=(0,12), pady=6)
for _ in range(7):
    left.grid_rowconfigure(_, weight=0)

ctk.CTkLabel(left, text="Tilkobling", text_color="white",
             font=ctk.CTkFont(size=18, weight="bold")).grid(row=0, column=0, sticky="w", padx=16, pady=(16,6))

host_var = ctk.StringVar(value=DEFAULT_HOST)
port_var = ctk.StringVar(value=str(DEFAULT_PORT))
pwd_var  = ctk.StringVar(value=DEFAULT_PWD)

ctk.CTkEntry(left, textvariable=host_var, placeholder_text="PLAXIS host").grid(row=1, column=0, padx=16, pady=6, sticky="ew")
ctk.CTkEntry(left, textvariable=port_var, placeholder_text="Port").grid(row=2, column=0, padx=16, pady=6, sticky="ew")
ctk.CTkEntry(left, textvariable=pwd_var,  placeholder_text="Passord (Code)", show="*").grid(row=3, column=0, padx=16, pady=6, sticky="ew")

ctk.CTkButton(left, text="🔌 Koble til", command=connect_plaxis).grid(row=4, column=0, padx=16, pady=(14,6), sticky="ew")
ctk.CTkButton(left, text="❌ Koble fra", fg_color="#374151", hover_color="#4b5563",
              command=disconnect_plaxis).grid(row=5, column=0, padx=16, pady=(0,10), sticky="ew")

# Info-tekst på venstre kort
ctk.CTkLabel(left, text="Tips: Se generert kode i fanen «Kode».",
             text_color="#d1fae5", wraplength=220, justify="left").grid(row=6, column=0, padx=16, pady=(0,12), sticky="w")

# Høyre kort (tabview: Logg + Kode)
right = ctk.CTkFrame(content, fg_color="#101826", corner_radius=16)
right.grid(row=0, column=1, sticky="nsew", pady=6)
right.grid_columnconfigure(0, weight=1)
right.grid_rowconfigure(1, weight=1)

header = ctk.CTkLabel(right, text="Visning", text_color="#f8fafc",
                      font=ctk.CTkFont(size=18, weight="bold"))
header.grid(row=0, column=0, sticky="w", padx=16, pady=(16,4))

tabview = ctk.CTkTabview(right, segmented_button_selected_color="#0e7490", segmented_button_unselected_color="#1f2937")
tabview.grid(row=1, column=0, sticky="nsew", padx=12, pady=8)
tabview.add("Logg")
tabview.add("Kode")

# Logg-fane
log_tab = tabview.tab("Logg")
log_tab.grid_columnconfigure(0, weight=1)
log_tab.grid_rowconfigure(0, weight=1)

log_box = ctk.CTkTextbox(log_tab, wrap="word", font=("Segoe UI", 13), activate_scrollbars=True)
log_box.grid(row=0, column=0, sticky="nsew", padx=6, pady=6)

log_box.tag_config("system", background="#1f2937", foreground="#e5e7eb", lmargin1=12, lmargin2=12, rmargin=100, spacing3=8)
log_box.tag_config("user",   background="#0e7490", foreground="#e0f2fe", lmargin1=120, lmargin2=120, rmargin=12, spacing3=8)
log_box.tag_config("ai",     background="#3b0764", foreground="#f3e8ff", lmargin1=12,  lmargin2=12,  rmargin=120, spacing3=8)

def add_chat(role: str, text: str):
    log_box.configure(state="normal")
    if log_box.index("end-1c") != "1.0":
        log_box.insert("end", "\n")
    tag = role if role in ("system", "user", "ai") else "system"
    log_box.insert("end", text, tag)
    log_box.insert("end", "\n")
    log_box.see("end")
    log_box.configure(state="disabled")

def add_chat_safe(role: str, text: str):
    # Kan kalles før UI er fullstendig ferdig initialisert
    try:
        add_chat(role, text)
    except Exception:
        pass

# Kode-fane
code_tab = tabview.tab("Kode")
code_tab.grid_columnconfigure(0, weight=1)
code_tab.grid_rowconfigure(0, weight=1)

code_box = ctk.CTkTextbox(code_tab, wrap="none", font=("Consolas", 12), activate_scrollbars=True)
code_box.grid(row=0, column=0, sticky="nsew", padx=6, pady=6)
code_box.configure(state="disabled")

# Knapper i kode-fanen
code_btnbar = ctk.CTkFrame(code_tab, fg_color="#0b1220")
code_btnbar.grid(row=1, column=0, sticky="ew", padx=6, pady=(0,6))
code_btnbar.grid_columnconfigure(0, weight=0)
code_btnbar.grid_columnconfigure(1, weight=0)
code_btnbar.grid_columnconfigure(2, weight=1)

def update_code_view(code: str):
    global last_code
    last_code = code
    code_box.configure(state="normal")
    code_box.delete("1.0", "end")
    code_box.insert("1.0", code)
    code_box.configure(state="disabled")

def copy_code_to_clipboard():
    app.clipboard_clear()
    app.clipboard_append(last_code or "")
    add_chat("system", "Kode kopiert til utklippstavle.")

def run_last_code():
    if not (last_code and last_code.strip()):
        add_chat("system", "Ingen kode å kjøre.")
        return
    status = run_plaxis_code(last_code)
    if status == "OK":
        add_chat("system", "Kjøring fullført (fra Kode-fane).")
    else:
        add_chat("system", status)

ctk.CTkButton(code_btnbar, text="Kjør på nytt", command=run_last_code).grid(row=0, column=0, padx=(6,6), pady=6)
ctk.CTkButton(code_btnbar, text="Kopier kode", command=copy_code_to_clipboard).grid(row=0, column=1, padx=(0,6), pady=6)

# Inndata-linje (under tabview)
input_area = ctk.CTkFrame(right, fg_color="#0b1220", corner_radius=12)
input_area.grid(row=2, column=0, sticky="ew", padx=12, pady=(6,12))
input_area.grid_columnconfigure(0, weight=1)
input_area.grid_columnconfigure(1, weight=0)

prompt_var = ctk.StringVar(value="Beskriv hva som skal gjøres i PLAXIS (kun kode genereres)")
prompt_entry = ctk.CTkEntry(input_area, textvariable=prompt_var)
prompt_entry.grid(row=0, column=0, sticky="ew", padx=8, pady=8)

def send_and_run():
    txt = prompt_var.get().strip()
    if not txt:
        return
    add_chat("user", txt)
    try:
        code = call_llm_code_with_retry(txt, int(tokens_var.get()))
    except Exception as e:
        add_chat("system", f"API-feil: {e}")
        return

    update_code_view(code)

    status = run_plaxis_code(code)
    if status == "OK":
        add_chat("system", "Kjøring fullført.")
    else:
        add_chat("system", status)

send_btn = ctk.CTkButton(input_area, text="Send og kjør!", command=send_and_run)
send_btn.grid(row=0, column=1, padx=8, pady=8)

# Token-velger
footer = ctk.CTkFrame(app, height=44, fg_color="#0b1220")
footer.grid(row=2, column=0, sticky="nsew")
footer.grid_columnconfigure(1, weight=1)

ctk.CTkLabel(footer, text="Max completion tokens:", text_color="#cbd5e1").grid(row=0, column=0, sticky="w", padx=14, pady=10)
tokens_var = ctk.StringVar(value=str(DEFAULT_MAX_TOKENS))
ctk.CTkEntry(footer, textvariable=tokens_var, width=100).grid(row=0, column=1, sticky="w", padx=6, pady=10)

# Forhåndsmelding
add_chat_safe("system", "Klar. Koble til PLAXIS (fyll Passord/Code om nødvendig) og gi en kommando.\n"
                        "Første tilkobling vil sikre at kunnskapsindekser (FAISS + FTS5) er klare.")

app.mainloop()
