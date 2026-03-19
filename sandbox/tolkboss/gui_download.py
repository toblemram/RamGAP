# gui_download.py
# -*- coding: utf-8 -*-
"""
GUI-fane: Nedlasting av **SND-filer** via *metode*-endepunktet.

Funksjoner i fanen:
- Lim inn Bearer-token (vis/skjul)
- Sett base-URL (default https://api.fieldmanager.io/fieldmanager)
- Hent prosjekter → velg prosjekt → hent lokasjoner
- Velg hvilke lokasjoner som skal prosesseres (checkboxer + «Velg alle» / «Fjern alle»)
- Velg mappe, velg «Bytt X/Y (swap_x_y)» ved behov
- Start nedlasting: for hver valgt lokasjon hentes alle metoder, og for hver metode hentes SND (ikke ZIP)
- Progresjonsindikator og logg
- Lagrer delte state `shared_state["download_dir"]` for videre bruk i SND-graf-fanen

Avhenger av:
  - customtkinter, tkinter
  - api_client.ApiClient
  - snd_parser.parse_snd_text (for enkel validering etter lagring)
"""
from __future__ import annotations

import os
import re
import threading
from dataclasses import dataclass
from typing import List, Tuple, Dict, Optional

import customtkinter as ctk
from tkinter import filedialog, messagebox

from api_client import ApiClient, DEFAULT_BASE_URL
from snd_parser import parse_snd_text


# ---------------------------
# Hjelp
# ---------------------------

def sanitize_filename(name: str, max_len: int = 180) -> str:
    safe = re.sub(r"[^A-Za-z0-9._\-]+", "_", name).strip("._")
    return safe[:max_len] if safe else "fil"


@dataclass
class DownloadResult:
    ok: bool
    path: Optional[str]
    error: Optional[str]


# ---------------------------
# Fane
# ---------------------------

class DownloadTab(ctk.CTkFrame):
    """Tab for å autentisere, velge prosjekt/lokasjoner og laste ned SND pr metode."""

    def __init__(self, master, shared_state: Dict):
        super().__init__(master)
        self.shared = shared_state

        # Topp: token + baseURL
        top = ctk.CTkFrame(self)
        top.pack(fill="x", padx=10, pady=(10, 8))

        ctk.CTkLabel(top, text="Bearer‑token:").grid(row=0, column=0, sticky="w", padx=(8, 6), pady=6)
        self.token_var = ctk.StringVar()
        self.token_entry = ctk.CTkEntry(top, textvariable=self.token_var, show="•", width=520)
        self.token_entry.grid(row=0, column=1, sticky="we", padx=(0, 8), pady=6)
        self.show_token = ctk.CTkCheckBox(top, text="Vis", command=self._toggle_token)
        self.show_token.grid(row=0, column=2, sticky="w", padx=6, pady=6)

        ctk.CTkLabel(top, text="Base‑URL:").grid(row=1, column=0, sticky="w", padx=(8, 6), pady=6)
        self.base_var = ctk.StringVar(value=DEFAULT_BASE_URL)
        ctk.CTkEntry(top, textvariable=self.base_var).grid(row=1, column=1, sticky="we", padx=(0, 8), pady=6)
        self.fetch_btn = ctk.CTkButton(top, text="Hent prosjekter", command=self._on_fetch_projects)
        self.fetch_btn.grid(row=1, column=2, sticky="w", padx=6, pady=6)
        top.grid_columnconfigure(1, weight=1)

        # Prosjekt / lokasjoner
        mid = ctk.CTkFrame(self)
        mid.pack(fill="both", expand=True, padx=10, pady=8)

        projf = ctk.CTkFrame(mid)
        projf.pack(fill="x", padx=8, pady=8)
        ctk.CTkLabel(projf, text="Prosjekt:").grid(row=0, column=0, sticky="w", padx=8, pady=8)
        self.project_var = ctk.StringVar()
        self.project_combo = ctk.CTkComboBox(projf, values=[], variable=self.project_var, width=700)
        self.project_combo.grid(row=0, column=1, sticky="we", padx=(0, 8), pady=8)
        self.locs_btn = ctk.CTkButton(projf, text="Hent lokasjoner", state="disabled", command=self._on_fetch_locations)
        self.locs_btn.grid(row=0, column=2, sticky="w", padx=8, pady=8)
        projf.grid_columnconfigure(1, weight=1)

        listf = ctk.CTkFrame(mid)
        listf.pack(fill="both", expand=True, padx=8, pady=8)
        head = ctk.CTkFrame(listf)
        head.pack(fill="x", padx=8, pady=(8, 0))
        self.sel_count = ctk.StringVar(value="0 valgt")
        ctk.CTkLabel(head, textvariable=self.sel_count).pack(side="left")
        ctk.CTkButton(head, text="Velg alle", command=self._select_all).pack(side="right", padx=4)
        ctk.CTkButton(head, text="Fjern alle", command=self._deselect_all).pack(side="right", padx=4)

        self.scroll = ctk.CTkScrollableFrame(listf, height=260)
        self.scroll.pack(fill="both", expand=True, padx=8, pady=8)

        # Innstillinger / destinasjon
        opts = ctk.CTkFrame(mid)
        opts.pack(fill="x", padx=8, pady=8)
        self.swap_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(opts, text="Bytt X/Y (swap_x_y)", variable=self.swap_var).grid(row=0, column=0, sticky="w", padx=8, pady=8)
        ctk.CTkLabel(opts, text="Lagre i mappe:").grid(row=0, column=1, sticky="e", padx=8, pady=8)
        self.dir_var = ctk.StringVar()
        ctk.CTkEntry(opts, textvariable=self.dir_var, width=420).grid(row=0, column=2, sticky="we", padx=(0, 8), pady=8)
        ctk.CTkButton(opts, text="Velg…", command=self._choose_dir).grid(row=0, column=3, sticky="w", padx=8, pady=8)
        opts.grid_columnconfigure(2, weight=1)

        # Handlinger
        act = ctk.CTkFrame(mid)
        act.pack(fill="x", padx=8, pady=(6, 8))
        self.start_btn = ctk.CTkButton(act, text="Start nedlasting (metoder → .SND)", state="disabled", command=self._start_downloads)
        self.start_btn.pack(side="left", padx=8)
        self.stop_btn = ctk.CTkButton(act, text="Stopp", state="disabled", command=self._stop_downloads)
        self.stop_btn.pack(side="left", padx=8)

        # Progresjon + logg
        bot = ctk.CTkFrame(self)
        bot.pack(fill="both", expand=False, padx=10, pady=(4, 10))
        self.progress = ctk.CTkProgressBar(bot)
        self.progress.set(0.0)
        self.progress.pack(fill="x", padx=8, pady=(10, 6))
        self.log = ctk.CTkTextbox(bot, height=160)
        self.log.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        # Internt
        self.client: Optional[ApiClient] = None
        self.projects: List[dict] = []
        self.project_index: Dict[str, str] = {}
        self.location_checks: List[Tuple[dict, ctk.BooleanVar]] = []
        self.stopflag = threading.Event()

    # --- småhjelpere ---
    def _log(self, lvl: str, msg: str):
        prefixes = {"INFO": "[INFO] ", "OK": "[OK]   ", "ERR": "[FEIL] ", "WARN": "[ADVARSEL] "}
        self.log.insert("end", prefixes.get(lvl, "") + msg + "\n")
        self.log.see("end")

    def _toggle_token(self):
        self.token_entry.configure(show="" if self.show_token.get() else "•")

    def _choose_dir(self):
        p = filedialog.askdirectory(title="Velg mappe")
        if p:
            self.dir_var.set(p)
            self.shared["download_dir"] = p

    def _update_selected(self):
        n = sum(1 for _, v in self.location_checks if v.get())
        self.sel_count.set(f"{n} valgt")

    def _select_all(self):
        for _, v in self.location_checks:
            v.set(True)
        self._update_selected()

    def _deselect_all(self):
        for _, v in self.location_checks:
            v.set(False)
        self._update_selected()

    # --- nett ---
    def _on_fetch_projects(self):
        tok = self.token_var.get().strip()
        if not tok:
            messagebox.showwarning("Mangler token", "Lim inn Bearer‑token først.")
            return
        base = self.base_var.get().strip() or DEFAULT_BASE_URL
        self.client = ApiClient(base, tok)
        self.fetch_btn.configure(state="disabled")
        threading.Thread(target=self._t_fetch_projects, daemon=True).start()

    def _t_fetch_projects(self):
        try:
            projs = self.client.list_projects()
            projs.sort(key=lambda p: (p.get("name") or "").lower())
            self.projects = projs
            values = []
            self.project_index.clear()
            for p in projs:
                name = p.get("name") or "(uten navn)"
                ext = p.get("external_id") or ""
                pid = p.get("project_id") or ""
                disp = f"{name} — {ext} ({pid[:8]}…)" if ext else f"{name} ({pid[:8]}…)"
                values.append(disp)
                self.project_index[disp] = pid
            self.project_combo.configure(values=values)
            if values:
                self.project_combo.set(values[0])
                self.locs_btn.configure(state="normal")
            self._log("OK", f"Fant {len(projs)} prosjekt.")
        except Exception as e:
            self._log("ERR", f"Kunne ikke hente prosjekter: {e}")
        finally:
            self.fetch_btn.configure(state="normal")

    def _on_fetch_locations(self):
        if not self.client:
            return
        disp = self.project_var.get().strip()
        if not disp or disp not in self.project_index:
            messagebox.showwarning("Velg prosjekt", "Velg et prosjekt fra listen.")
            return
        pid = self.project_index[disp]
        self.locs_btn.configure(state="disabled")
        threading.Thread(target=self._t_fetch_locations, args=(pid,), daemon=True).start()

    def _t_fetch_locations(self, project_id: str):
        try:
            locs = self.client.list_locations(project_id)
            # vis
            for ch in self.scroll.winfo_children():
                ch.destroy()
            self.location_checks.clear()
            for i, loc in enumerate(locs, 1):
                txt = f"{i:03d}  {loc.get('name') or '(uten navn)'}  ({loc.get('location_id','')[:8]}…)"
                var = ctk.BooleanVar(value=True)
                ctk.CTkCheckBox(self.scroll, text=txt, variable=var, command=self._update_selected).pack(anchor="w", padx=8, pady=3)
                self.location_checks.append((loc, var))
            self._update_selected()
            self.start_btn.configure(state="normal")
            self._log("OK", f"Fant {len(locs)} lokasjoner.")
        except Exception as e:
            self._log("ERR", f"Kunne ikke hente lokasjoner: {e}")
        finally:
            self.locs_btn.configure(state="normal")

    def _start_downloads(self):
        if not self.client:
            return
        out_dir = self.dir_var.get().strip()
        if not out_dir:
            messagebox.showinfo("Ingen mappe", "Velg en mappe å lagre i.")
            return
        sel = [(loc) for (loc, v) in self.location_checks if v.get()]
        if not sel:
            messagebox.showinfo("Ingen valgt", "Velg minst én lokasjon.")
            return
        self.stopflag.clear()
        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        self.progress.set(0.0)
        self.shared["download_dir"] = out_dir
        threading.Thread(target=self._t_downloads, args=(sel,), daemon=True).start()

    def _stop_downloads(self):
        self.stopflag.set()
        self._log("WARN", "Avbryter etter pågående nedlasting…")

    def _t_downloads(self, locations: List[dict]):
        try:
            disp = self.project_var.get().strip()
            pid = self.project_index.get(disp, "")
            # tell opp metoder
            pairs = []
            for loc in locations:
                if self.stopflag.is_set():
                    break
                lid = loc.get("location_id", "")
                try:
                    methods = self.client.list_methods(pid, lid)
                except Exception as e:
                    self._log("ERR", f"Metoder feilet for {lid[:8]}…: {e}")
                    continue
                for m in methods:
                    pairs.append((loc, m))

            total = max(1, len(pairs))
            done = 0
            for loc, m in pairs:
                if self.stopflag.is_set():
                    break
                lid = loc.get("location_id", "")
                lname = loc.get("name") or "lokasjon"
                mid = m.get("method_id", "")
                mname = m.get("name") or m.get("type") or mid[:8]
                try:
                    text, suggested = self.client.export_method_snd(pid, lid, mid, swap_x_y=self.swap_var.get())
                    base = suggested or f"{lname}_{mname}_{mid[:8]}.snd"
                    fname = sanitize_filename(base)
                    path = os.path.join(self.dir_var.get().strip(), fname)
                    with open(path, "w", encoding="utf-8") as f:
                        f.write(text)
                    # forsøk å parse for å validere
                    try:
                        parse_snd_text(text)
                        self._log("OK", f"Lagret (validerte data): {path}")
                    except Exception:
                        self._log("WARN", f"Lagret (kunne ikke parse – sjekk format): {path}")
                except Exception as e:
                    self._log("ERR", f"Eksport feilet {lname}/{mname}: {e}")
                finally:
                    done += 1
                    self.progress.set(done/total)

            if not self.stopflag.is_set():
                self._log("OK", "Ferdig. Gå til fanen ‘SND‑graf’ og trykk ‘Oppdater fra mappe’.")
            else:
                self._log("WARN", "Avbrutt.")
        finally:
            self.start_btn.configure(state="normal")
            self.stop_btn.configure(state="disabled")
