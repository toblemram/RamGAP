# -*- coding: utf-8 -*-
"""
PlaxisWorker
============
Minimal standalone app that polls the RamGAP backend for pending Plaxis
jobs, executes them with Plaxis's own python.exe, and sends the result back.

This file should NEVER need updating — all logic lives in the RamGAP backend
(script_builder.py). The worker just exec()s whatever code it receives.

Package as .exe:
    pip install pyinstaller
    pyinstaller --onefile --windowed --name PlaxisWorker PlaxisWorker.py
"""

import json
import os
import subprocess
import sys
import tempfile
import threading
import time
import tkinter as tk
from tkinter import scrolledtext
import urllib.error
import urllib.request
from datetime import datetime

# ---------------------------------------------------------------------------
# Default settings
# ---------------------------------------------------------------------------
_PLAXIS_PYTHON = (
    r"C:\ProgramData\Bentley\Geotechnical\PLAXIS Python Distribution V1\python\python.exe"
)
_DEFAULT_BACKEND_URL = "http://localhost:5050"
_SETTINGS_FILE = os.path.join(
    os.environ.get("APPDATA", os.path.expanduser("~")),
    "PlaxisWorker",
    "settings.json",
)


# ---------------------------------------------------------------------------
# HTTP helpers (stdlib only — no requests needed)
# ---------------------------------------------------------------------------

def api_get(url: str) -> dict:
    req = urllib.request.Request(url, method='GET')
    req.add_header('Content-Type', 'application/json')
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode())


def api_post(url: str, body: dict) -> dict:
    data = json.dumps(body).encode()
    req = urllib.request.Request(url, data=data, method='POST')
    req.add_header('Content-Type', 'application/json')
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode())


# ---------------------------------------------------------------------------
# Job execution
# ---------------------------------------------------------------------------

def run_job(plaxis_python: str, code: str) -> dict:
    """Write *code* to a temp file, run with Plaxis python, parse JSON stdout."""
    fd, path = tempfile.mkstemp(suffix='.py', prefix='plaxis_job_')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            f.write(code)
        proc = subprocess.run(
            [plaxis_python, path],
            capture_output=True, text=True, timeout=600,
        )
        stdout = proc.stdout.strip()
        if not stdout:
            return {'success': False, 'error': proc.stderr or 'No output from script'}
        return json.loads(stdout)
    except subprocess.TimeoutExpired:
        return {'success': False, 'error': 'Script timed out (600s)'}
    except json.JSONDecodeError:
        return {'success': False, 'error': f'Bad JSON from script: {stdout[:500]}'}
    except Exception as exc:
        return {'success': False, 'error': str(exc)}
    finally:
        try:
            os.remove(path)
        except OSError:
            pass


# ---------------------------------------------------------------------------
# Settings persistence
# ---------------------------------------------------------------------------

def _load_settings() -> dict:
    try:
        with open(_SETTINGS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}


def _save_settings(data: dict):
    os.makedirs(os.path.dirname(_SETTINGS_FILE), exist_ok=True)
    with open(_SETTINGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)


# ---------------------------------------------------------------------------
# GUI Application
# ---------------------------------------------------------------------------

class PlaxisWorkerApp:
    # Colours
    _GREEN = "#22c55e"
    _RED   = "#ef4444"
    _AMBER = "#f59e0b"
    _BG    = "#1e1e2e"
    _FG    = "#cdd6f4"
    _CARD  = "#313244"
    _ENTRY = "#45475a"

    def __init__(self):
        self.running = False
        self.thread = None
        self.jobs_done = 0
        self.jobs_failed = 0

        # --- Root window ---
        self.root = tk.Tk()
        self.root.title("PlaxisWorker")
        self.root.configure(bg=self._BG)
        self.root.resizable(False, False)
        self.root.geometry("480x200")  # compact default; expands when log shown

        # --- Top status bar ---
        top = tk.Frame(self.root, bg=self._BG)
        top.pack(fill="x", padx=16, pady=(14, 6))

        self.status_dot = tk.Canvas(top, width=18, height=18, bg=self._BG,
                                    highlightthickness=0)
        self.status_dot.pack(side="left")
        self._dot = self.status_dot.create_oval(3, 3, 15, 15, fill=self._RED,
                                                 outline="")

        self.status_label = tk.Label(top, text="  Stopped", font=("Segoe UI", 11, "bold"),
                                     bg=self._BG, fg=self._FG)
        self.status_label.pack(side="left")

        self.jobs_label = tk.Label(top, text="", font=("Segoe UI", 9),
                                   bg=self._BG, fg="#a6adc8")
        self.jobs_label.pack(side="right")

        # --- Settings card ---
        card = tk.Frame(self.root, bg=self._CARD, highlightthickness=0)
        card.pack(fill="x", padx=16, pady=6)

        settings = _load_settings()

        # Backend URL
        row1 = tk.Frame(card, bg=self._CARD)
        row1.pack(fill="x", padx=10, pady=(8, 8))
        tk.Label(row1, text="Backend URL", width=14, anchor="w",
                 font=("Segoe UI", 9), bg=self._CARD, fg="#a6adc8").pack(side="left")
        self.url_var = tk.StringVar(value=settings.get("url", _DEFAULT_BACKEND_URL))
        tk.Entry(row1, textvariable=self.url_var, font=("Segoe UI", 9),
                 bg=self._ENTRY, fg=self._FG, insertbackground=self._FG,
                 relief="flat", bd=0).pack(side="left", fill="x", expand=True, ipady=3)

        # --- Button bar ---
        btns = tk.Frame(self.root, bg=self._BG)
        btns.pack(fill="x", padx=16, pady=(4, 6))

        self.start_btn = tk.Button(
            btns, text="▶  Start", command=self._toggle,
            font=("Segoe UI", 10, "bold"), bg=self._GREEN, fg="white",
            activebackground="#16a34a", relief="flat", cursor="hand2",
            width=14, pady=4,
        )
        self.start_btn.pack(side="left")

        self.log_toggle_btn = tk.Button(
            btns, text="▼  Show Log", command=self._toggle_log,
            font=("Segoe UI", 9), bg=self._CARD, fg="#a6adc8",
            activebackground=self._ENTRY, relief="flat", cursor="hand2",
            width=14, pady=4,
        )
        self.log_toggle_btn.pack(side="right")

        # --- Log pane (hidden by default) ---
        self.log_visible = False
        self.log_frame = tk.Frame(self.root, bg=self._BG)
        # Not packed yet

        self.log_text = scrolledtext.ScrolledText(
            self.log_frame, height=14, font=("Consolas", 9),
            bg="#11111b", fg="#a6adc8", insertbackground="#a6adc8",
            relief="flat", state="disabled", wrap="word",
        )
        self.log_text.pack(fill="both", expand=True, padx=16, pady=(0, 10))

        # Tag for highlighted lines
        self.log_text.tag_configure("ok", foreground=self._GREEN)
        self.log_text.tag_configure("err", foreground=self._RED)
        self.log_text.tag_configure("warn", foreground=self._AMBER)
        self.log_text.tag_configure("info", foreground="#89b4fa")

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        # Auto-start polling on launch
        self.root.after(100, self._start)

    # ------------------------------------------------------------------ log

    def _log(self, msg: str, tag: str = ""):
        ts = datetime.now().strftime("%H:%M:%S")
        line = f"[{ts}] {msg}\n"
        self.log_text.configure(state="normal")
        self.log_text.insert("end", line, tag)
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def _toggle_log(self):
        if self.log_visible:
            self.log_frame.pack_forget()
            self.log_toggle_btn.configure(text="▼  Show Log")
            self.root.geometry("480x200")
        else:
            self.log_frame.pack(fill="both", expand=True)
            self.log_toggle_btn.configure(text="▲  Hide Log")
            self.root.geometry("480x480")
        self.log_visible = not self.log_visible

    # -------------------------------------------------------------- actions

    def _toggle(self):
        if self.running:
            self._stop()
        else:
            self._start()

    def _start(self):
        url = self.url_var.get().strip().rstrip('/')
        if not url:
            self._log("Backend URL is required", "err")
            return
        if not os.path.isfile(_PLAXIS_PYTHON):
            self._log(f"Plaxis Python not found: {_PLAXIS_PYTHON}", "err")
            return

        # Save settings
        _save_settings({"url": url})

        self.running = True
        self.status_dot.itemconfig(self._dot, fill=self._GREEN)
        self.status_label.configure(text="  Running")
        self.start_btn.configure(text="■  Stop", bg=self._RED,
                                 activebackground="#dc2626")
        self._log(f"Started — polling {url}", "info")
        self._log(f"Plaxis Python: {_PLAXIS_PYTHON}", "info")

        self.thread = threading.Thread(target=self._poll_loop,
                                       args=(url, _PLAXIS_PYTHON), daemon=True)
        self.thread.start()

    def _stop(self):
        self.running = False
        self.status_dot.itemconfig(self._dot, fill=self._RED)
        self.status_label.configure(text="  Stopped")
        self.start_btn.configure(text="▶  Start", bg=self._GREEN,
                                 activebackground="#16a34a")
        self._log("Stopped", "warn")

    def _update_jobs_label(self):
        parts = []
        if self.jobs_done:
            parts.append(f"✓ {self.jobs_done}")
        if self.jobs_failed:
            parts.append(f"✗ {self.jobs_failed}")
        self.jobs_label.configure(text="   ".join(parts))

    # --------------------------------------------------------------- poller

    def _poll_loop(self, backend_url: str, plaxis_python: str):
        poll_url = f"{backend_url}/api/plaxis/jobs/poll"
        while self.running:
            try:
                resp = api_get(poll_url)
                job = resp.get('job')
                if not job:
                    time.sleep(2)
                    continue

                job_id   = job['id']
                job_type = job['job_type']
                code     = job['code']

                self.root.after(0, self._log,
                                f"Job {job_id} ({job_type}) — executing...", "info")

                result = run_job(plaxis_python, code)

                complete_url = f"{backend_url}/api/plaxis/jobs/{int(job_id)}/complete"
                if result.get('success'):
                    api_post(complete_url, {'result': result})
                    self.jobs_done += 1
                    self.root.after(0, self._log,
                                    f"Job {job_id} done ✓", "ok")
                else:
                    err = result.get('error', 'Unknown error')
                    api_post(complete_url, {'error': err})
                    self.jobs_failed += 1
                    self.root.after(0, self._log,
                                    f"Job {job_id} failed: {err[:200]}", "err")

                self.root.after(0, self._update_jobs_label)

            except urllib.error.URLError:
                # Backend unreachable — blink amber briefly
                self.root.after(0, lambda: self.status_dot.itemconfig(
                    self._dot, fill=self._AMBER))
                time.sleep(3)
                if self.running:
                    self.root.after(0, lambda: self.status_dot.itemconfig(
                        self._dot, fill=self._GREEN))
            except Exception as exc:
                self.root.after(0, self._log, f"Error: {exc}", "err")
                time.sleep(3)

    # ---------------------------------------------------------------- close

    def _on_close(self):
        self.running = False
        self.root.destroy()

    def run(self):
        self.root.mainloop()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    app = PlaxisWorkerApp()
    app.run()
