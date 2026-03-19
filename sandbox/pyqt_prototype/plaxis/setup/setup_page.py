import os
import customtkinter as ctk
from tkinter import messagebox
from dotenv import load_dotenv
from openai import OpenAI
from plxscripting.easy import new_server

# -------------------- Oppsett --------------------
load_dotenv()
API_KEY = os.getenv("OPENAI_API_KEY", "")
MODEL = "gpt-5"                 # alltid GPT-5 (kontoen din må ha tilgang)
DEFAULT_HOST = "localhost"
DEFAULT_PORT = 10000
DEFAULT_PWD  = ""               # PLAXIS-passord (Code) hvis du bruker det
DEFAULT_MAX_TOKENS = 2000       # senk for raskere svar

DEMO_AUTORUN = False            # sett True hvis du vil auto-kjøre etter tilkobling

client = OpenAI(api_key=API_KEY)

# PLAXIS-tilkobling
s = None
g = None

# -------------------- Prompt-regler --------------------
SYSTEM_PROMPT = (
    "Du er en PLAXIS-kodegenerator i et skrivebordsverktøy.\n"
    "- Returner ALLTID KUN ren Python-kode som kan kjøres med g (PLAXIS global) og s (server).\n"
    "- Ingen tekst, ingen markdown, ingen JSON, ingen ```-blokker, ingen kommentarer.\n"
    "- Ikke bruk imports. Ikke kall new_server. IKKE kall g.new(). Operer på eksisterende prosjekt i g.\n"
)

# -------------------- LLM --------------------
def call_llm_code(user_text: str, max_tokens: int) -> str:
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",    "content": user_text},
        ],
        max_completion_tokens=max_tokens
    )
    code = (resp.choices[0].message.content or "").strip()
    if code.startswith("```"):
        code = code.strip("`")
        if code.lower().startswith("python"):
            code = code[6:].lstrip()
    return code

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

# Toppbar (gradient-ish ved å bruke to lag)
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

# Innhold: venstre tilkoblingskort + høyre “chat”
content = ctk.CTkFrame(app, fg_color="#0e1726")
content.grid(row=1, column=0, sticky="nsew", padx=14, pady=14)
content.grid_columnconfigure(0, weight=0)
content.grid_columnconfigure(1, weight=1)
content.grid_rowconfigure(0, weight=1)

# Venstre kort
left = ctk.CTkFrame(content, fg_color="#12354a", corner_radius=16)
left.grid(row=0, column=0, sticky="nsw", padx=(0,12), pady=6)
for _ in range(6):
    left.grid_rowconfigure(_, weight=0)

ctk.CTkLabel(left, text="Tilkobling", text_color="white",
             font=ctk.CTkFont(size=18, weight="bold")).grid(row=0, column=0, sticky="w", padx=16, pady=(16,6))

host_var = ctk.StringVar(value=DEFAULT_HOST)
port_var = ctk.StringVar(value=str(DEFAULT_PORT))
pwd_var  = ctk.StringVar(value=DEFAULT_PWD)

ctk.CTkEntry(left, textvariable=host_var, placeholder_text="PLAXIS host").grid(row=1, column=0, padx=16, pady=6)
ctk.CTkEntry(left, textvariable=port_var, placeholder_text="Port").grid(row=2, column=0, padx=16, pady=6)
ctk.CTkEntry(left, textvariable=pwd_var,  placeholder_text="Passord (Code)", show="*").grid(row=3, column=0, padx=16, pady=6)

ctk.CTkButton(left, text="🔌 Koble til", command=connect_plaxis).grid(row=4, column=0, padx=16, pady=(14,6), sticky="ew")
ctk.CTkButton(left, text="❌ Koble fra", fg_color="#374151", hover_color="#4b5563",
              command=disconnect_plaxis).grid(row=5, column=0, padx=16, pady=(0,14), sticky="ew")

# Høyre kort (chat + input)
right = ctk.CTkFrame(content, fg_color="#101826", corner_radius=16)
right.grid(row=0, column=1, sticky="nsew", pady=6)
right.grid_columnconfigure(0, weight=1)
right.grid_rowconfigure(1, weight=1)

header = ctk.CTkLabel(right, text="Logg", text_color="#f8fafc",
                      font=ctk.CTkFont(size=18, weight="bold"))
header.grid(row=0, column=0, sticky="w", padx=16, pady=(16,4))

# Chat-boks (med boble-stil via tags)
log_box = ctk.CTkTextbox(right, wrap="word", font=("Segoe UI", 13), activate_scrollbars=True)
log_box.grid(row=1, column=0, sticky="nsew", padx=16, pady=10)

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

# Inndatalinje
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
        code = call_llm_code(txt, int(tokens_var.get()))
    except Exception as e:
        add_chat("system", f"API-feil: {e}")
        return
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
add_chat("system", "Klar. Koble til PLAXIS (fyll Passord/Code om nødvendig) og gi en kommando.")

app.mainloop()
