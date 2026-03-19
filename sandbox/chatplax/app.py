import os
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import scrolledtext, messagebox
from dotenv import load_dotenv
from openai import OpenAI
from plxscripting.easy import new_server

# -------------------- Oppsett --------------------
load_dotenv()

API_KEY = os.getenv("OPENAI_API_KEY", "")
MODEL = os.getenv("OPENAI_MODEL", "gpt-5")  # sett f.eks. gpt-5 i .env hvis du har tilgang

DEFAULT_HOST = os.getenv("PLAXIS_HOST", "localhost")
DEFAULT_PORT = int(os.getenv("PLAXIS_PORT", "10000"))
DEFAULT_PWD  = os.getenv("PLAXIS_PASSWORD", "")

# OpenAI-klient
client = OpenAI(api_key=API_KEY)

# PLAXIS-tilkobling
s = None  # server
g = None  # globals

# -------------------- LLM-hjelper --------------------
# Tving modellen til KUN å skrive kjørbar Python for PLAXIS (g/s). Ingen tekst, ingen markdown.
SYSTEM_PROMPT = (
    "Du er en PLAXIS-kodegenerator. "
    "Svar ALLTID med KUN ren Python-kode som kan kjøres direkte med objektene g (PLAXIS global) og s (server). "
    "Ingen forklaringer, ingen tekst, ingen JSON, ingen markdown, ingen ```-blokker. Kun gyldige Python-setninger.\n"
    "Bruk KUN kjente PLAXIS-kall (eksempler):\n"
    "- g.new()\n"
    "- g.open(r\"C:\\sti\\til\\prosjekt.plxproj\") / g.save(r\"C:\\sti\\til\\prosjekt.plxproj\")\n"
    "- bh = g.borehole(x, y)\n"
    "- mat = g.soilmat(); mat.setproperties(\"MaterialName\", \"Navn\", \"gammaUnsat\", 18, \"phi\", 30, \"cRef\", 1)\n"
    "- bh.Layering.AddLayer(-dybde, mat)\n"
    "- g.phase(g.Phases[-1]); g.calculate()\n"
    "- g.close()\n"
    "Ikke finn på nye metoder. Ikke importer biblioteker. Ikke skriv kommentarer."
)

def call_llm_code(user_text: str, max_tokens: int) -> str:
    """Kaller LLM og forventer ren Python-kode."""
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_text},
        ],
        # Nye modeller bruker max_completion_tokens (ikke max_tokens)
        max_completion_tokens=max_tokens
    )
    code = (resp.choices[0].message.content or "").strip()
    # Stripp eventuell markdown-gjerde hvis modellen likevel la det til
    if code.startswith("```"):
        code = code.strip("`")
        if code.lower().startswith("python"):
            code = code[6:].lstrip()
    return code

# -------------------- PLAXIS-kjøring --------------------
def connect_plaxis():
    global s, g
    host = host_var.get().strip()
    port = int(port_var.get())
    pwd  = pwd_var.get()
    try:
        s, g = new_server(host, port, password=pwd)
        status_var.set(f"Tilkoblet: {host}:{port}")
        log_insert("System", f"Koblet til PLAXIS RSS på {host}:{port}.")
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
    log_insert("System", "Frakoblet fra PLAXIS.")

def run_plaxis_code(code: str) -> str:
    """Kjører Python-kode mot g/s (ikke vis koden i logg, den vises i egen fane)."""
    if not code.strip():
        return "Ingen kode generert."
    if g is None:
        return "Ikke tilkoblet PLAXIS."
    try:
        exec_globals = {"g": g, "s": s}
        exec_locals = {}
        exec(code, exec_globals, exec_locals)
        return "Handling gjennomført i PLAXIS."
    except Exception as e:
        msg = str(e)
        # Hint ved typisk krypterings-feil (mangler Code/passord)
        if "missing \"Code\"" in msg or "decryption" in msg.lower():
            return ("Server krever en 'Code'/passord for kryptert tilkobling. "
                    "Skriv samme kode i Passord-feltet og koble til på nytt.")
        return f"Kjøringsfeil: {msg}"

# -------------------- UI-hjelpere --------------------
def log_insert(speaker: str, text: str):
    log_view.configure(state="normal")
    log_view.insert(tk.END, f"{speaker}: {text}\n")
    log_view.see(tk.END)
    log_view.configure(state="disabled")

# -------------------- Hendlere --------------------
def on_send():
    user_text = input_entry.get("1.0", tk.END).strip()
    if not user_text:
        return
    input_entry.delete("1.0", tk.END)
    log_insert("Du", user_text)

    try:
        max_tokens = int(max_tokens_var.get())
    except ValueError:
        max_tokens = 2000

    try:
        # 1) Hent kode fra modellen
        code = call_llm_code(user_text, max_tokens)

        # 2) Vis koden i "Kode sendt"-fanen
        code_view.configure(state="normal")
        code_view.delete("1.0", tk.END)
        code_view.insert(tk.END, code)
        code_view.see(tk.END)
        code_view.configure(state="normal")  # lar deg kopiere/redigere om du vil

        # 3) Kjør koden i PLAXIS
        status = run_plaxis_code(code)
        log_insert("System", status)
    except Exception as e:
        log_insert("Feil", str(e))
        if "insufficient_quota" in str(e):
            log_insert("Hint", "API-kvoten er brukt opp. Sjekk Billing i OpenAI-kontoen.")

# -------------------- Tkinter UI --------------------
root = tk.Tk()
root.title("R2-BØLL2 – PLAXIS kodeassistent (med kodefane)")
root.minsize(780, 740)

# Topp: PLAXIS-tilkobling
top = tk.Frame(root, padx=8, pady=8)
top.pack(fill="x")

tk.Label(top, text="PLAXIS host:").grid(row=0, column=0, sticky="w")
host_var = tk.StringVar(value=DEFAULT_HOST)
tk.Entry(top, textvariable=host_var, width=18).grid(row=0, column=1, padx=6)

tk.Label(top, text="Port:").grid(row=0, column=2, sticky="w")
port_var = tk.StringVar(value=str(DEFAULT_PORT))
tk.Entry(top, textvariable=port_var, width=8).grid(row=0, column=3, padx=6)

tk.Label(top, text="Passord (Code):").grid(row=0, column=4, sticky="w")
pwd_var = tk.StringVar(value=DEFAULT_PWD)
tk.Entry(top, textvariable=pwd_var, width=16, show="*").grid(row=0, column=5, padx=6)

btn_conn = tk.Button(top, text="Koble til", command=connect_plaxis)
btn_conn.grid(row=0, column=6, padx=6)
btn_disc = tk.Button(top, text="Koble fra", command=disconnect_plaxis)
btn_disc.grid(row=0, column=7, padx=6)

status_var = tk.StringVar(value="Frakoblet")
tk.Label(root, textvariable=status_var, fg="gray").pack(anchor="w", padx=10)

# Midt: Notebook med faner
mid = tk.Frame(root, padx=10, pady=10)
mid.pack(fill="both", expand=True)

notebook = ttk.Notebook(mid)
notebook.pack(fill="both", expand=True)

# Fane 1: Logg
log_tab = tk.Frame(notebook)
log_view = scrolledtext.ScrolledText(log_tab, height=24, wrap=tk.WORD, state="disabled")
log_view.pack(fill="both", expand=True)
notebook.add(log_tab, text="Logg")

# Fane 2: Kode sendt
code_tab = tk.Frame(notebook)
code_view = scrolledtext.ScrolledText(code_tab, height=24, wrap=tk.WORD, state="normal")
code_view.pack(fill="both", expand=True)
notebook.add(code_tab, text="Kode sendt")

# Nederst: Input + send
bottom = tk.Frame(root, padx=10, pady=10)
bottom.pack(fill="x")

tk.Label(bottom, text="Skriv kommando (beskriv hva som skal gjøres):").pack(anchor="w")
input_entry = tk.Text(bottom, height=4, wrap=tk.WORD)
input_entry.pack(fill="x", expand=True, pady=(0,8))

max_tokens_var = tk.StringVar(value="2000")
row2 = tk.Frame(bottom)
row2.pack(fill="x")
tk.Label(row2, text="Max completion tokens:").pack(side="left")
tk.Entry(row2, textvariable=max_tokens_var, width=12).pack(side="left", padx=(6,12))

send_btn = tk.Button(row2, text="Send og kjør", command=on_send)
send_btn.pack(side="right")

log_insert("System", "Klar. Koble til PLAXIS (fyll Passord/Code om nødvendig) og gi en kommando.")
root.mainloop()
