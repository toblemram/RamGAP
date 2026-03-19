import os
import customtkinter as ctk
from tkinter import messagebox
from dotenv import load_dotenv
from openai import OpenAI
from plxscripting.easy import new_server

import faiss, pickle, numpy as np


# -------------------- Oppsett --------------------
load_dotenv()
API_KEY = os.environ.get("OPENAI_API_KEY", "")
MODEL = "gpt-5"                 # alltid GPT-5 (kontoen din må ha tilgang)
DEFAULT_HOST = "localhost"
DEFAULT_PORT = 10000
DEFAULT_PWD  = ""               # PLAXIS-passord (Code) hvis du bruker det
DEFAULT_MAX_TOKENS = 10000       # senk for raskere svar

DEMO_AUTORUN = False            # sett True hvis du vil auto-kjøre etter tilkobling

client = OpenAI(api_key=API_KEY)

index = faiss.read_index("plaxis.index")
with open("plaxis_texts.pkl", "rb") as f:
    texts = pickle.load(f)

def search_docs(query, k=3):
    q_emb = client.embeddings.create(model="text-embedding-3-small", input=query).data[0].embedding
    q_emb = np.array([q_emb]).astype("float32")
    D, I = index.search(q_emb, k)
    return [texts[i] for i in I[0]]

# PLAXIS-tilkobling
s = None
g = None

# Siste genererte kode (vises i "Kode"-fanen)
last_code = ""

# -------------------- Prompt-regler --------------------
SYSTEM_PROMPT = (
    "Du er en PLAXIS-kodegenerator i et skrivebordsverktøy.\n"
    "- Returner ALLTID KUN ren Python-kode som kan kjøres med g (PLAXIS global) og s (server).\n"
    "- Ingen tekst, ingen markdown, ingen JSON, ingen ```-blokker, ingen kommentarer.\n"
    "- Ikke bruk imports. Ikke kall new_server. IKKE kall g.new(). Operer på eksisterende prosjekt i g.\n"
)

# -------------------- LLM --------------------
def call_llm_code_with_retry(user_text: str, max_tokens: int, retries: int = 2) -> str:
    """
    Sender brukerens spørsmål til GPT.
    Kjører koden. Hvis den feiler, send feilmeldingen tilbake og prøv på nytt.
    """
    attempt = 0
    last_code = ""
    last_error = ""

    while attempt <= retries:
        if attempt == 0:
            # Første forsøk: bare brukerens spørsmål
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_text}
            ]
        else:
            # Neste forsøk: legg til feilen og koden som kontekst
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_text},
                {"role": "system", "content": f"Dette var koden du foreslo:\n{last_code}"},
                {"role": "system", "content": f"Dette var feilmeldingen som kom fra PLAXIS:\n{last_error}"},
                {"role": "user", "content": "Forsøk å rette opp og gi en ny versjon av koden."}
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


# -------------------- PLAXIS --------------------
def connect_plaxis():
    global s, g
    host = host_var.get().strip()
    port = int(port_var.get())
    pwd  = pwd_var.get()
    try:
        s, g = new_server(host, port, password=pwd)
        status_var.set(f"Tilkoblet: {host}:{port}")
        add_chat("system", f"Koblet til PLAXIS RSS på {host}:{port}.")
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

def run_plaxis_code(code: str) -> str:
    if not code.strip():
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

# -------------------- UI (CustomTkinter, farger) --------------------
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
    # Hent fra last_code for å være sikker på at vi kopierer det som faktisk sendes
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

    # Oppdater kode-fanen med nøyaktig kode som sendes
    update_code_view(code)

    # (Valgfritt) bytt til Kode-fanen automatisk for synlighet
    # tabview.set("Kode")

    # Kjør koden
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
add_chat("system", "Klar. Koble til PLAXIS (fyll Passord/Code om nødvendig) og gi en kommando.\n"
                   "Se fanen «Kode» for å inspisere hva som blir sendt.")

app.mainloop()
