# -*- coding: utf-8 -*-
"""
Fieldmanager – prosjekt-/lokasjons‑eksportør (GUI)

Funksjoner:
- Lim inn Bearer-token og (valgfritt) API-base-URL
- Hent prosjekter (GET /projects)
- Velg prosjekt fra nedtrekksliste
- Hent lokasjoner i valgt prosjekt (GET /projects/{project_id}/locations)
- Velg hvilke lokasjoner som skal lastes ned (standard: alle)
- Last ned eksport for hver valgt lokasjon (GET /projects/{project_id}/locations/{location_id}/export?export_type=SND&swap_x_y=...)
- Lagrer som .zip-filer i valgt mappe. Håndterer både direkte binærrespons og presignert-URL (JSON string)

Avhengigheter:
    pip install customtkinter requests

Kjøring:
    python fieldmanager_downloader.py

NB: Token lagres ikke på disk og vises ikke i loggen.
"""
from __future__ import annotations

import os
import re
import sys
import json
import queue
import threading
from typing import Dict, List, Tuple, Optional

import requests

try:
    import customtkinter as ctk
    from tkinter import messagebox, filedialog
except Exception as e:  # pragma: no cover
    print("Klarte ikke å importere customtkinter / tkinter. Installer med: pip install customtkinter", file=sys.stderr)
    raise

# ---------------------------
# Konfig
# ---------------------------
DEFAULT_BASE_URL = "https://api.fieldmanager.io/fieldmanager"
PROJECTS_PATH = "/projects"
LOCATIONS_PATH_TMPL = "/projects/{project_id}/locations"
EXPORT_PATH_TMPL = "/projects/{project_id}/locations/{location_id}/export"
DEFAULT_LIMIT = 100

# ---------------------------
# Hjelpefunksjoner
# ---------------------------

def sanitize_filename(name: str, max_len: int = 150) -> str:
    """Gjør filnavn trygt for filsystemet."""
    safe = re.sub(r"[^A-Za-z0-9._\-]+", "_", name).strip("._")
    return safe[:max_len] if safe else "fil"


def ensure_dir(path: str) -> None:
    if not os.path.isdir(path):
        os.makedirs(path, exist_ok=True)


def join_url(base: str, path: str) -> str:
    return base.rstrip("/") + "/" + path.lstrip("/")


class ApiClient:
    def __init__(self, base_url: str, token: str, timeout: int = 60):
        self.base_url = base_url
        self.token = token
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.token}",
            "accept": "application/json",
        })

    def _get(self, path: str, params: Optional[dict] = None, stream: bool = False) -> requests.Response:
        url = join_url(self.base_url, path)
        resp = self.session.get(url, params=params, timeout=self.timeout, stream=stream)
        return resp

    def list_projects(self) -> List[dict]:
        results: List[dict] = []
        skip = 0
        while True:
            resp = self._get(PROJECTS_PATH, params={"skip": skip, "limit": DEFAULT_LIMIT})
            if resp.status_code == 401:
                raise PermissionError("Ugyldig eller utløpt token (401).")
            resp.raise_for_status()
            chunk = resp.json() or []
            if not chunk:
                break
            results.extend(chunk)
            if len(chunk) < DEFAULT_LIMIT:
                break
            skip += DEFAULT_LIMIT
        return results

    def list_locations(self, project_id: str) -> List[dict]:
        path = LOCATIONS_PATH_TMPL.format(project_id=project_id)
        results: List[dict] = []
        skip = 0
        while True:
            resp = self._get(path, params={"skip": skip, "limit": DEFAULT_LIMIT})
            if resp.status_code == 401:
                raise PermissionError("Ugyldig eller utløpt token (401).")
            resp.raise_for_status()
            chunk = resp.json() or []
            if not chunk:
                break
            results.extend(chunk)
            if len(chunk) < DEFAULT_LIMIT:
                break
            skip += DEFAULT_LIMIT
        return results

    def export_location(self, project_id: str, location_id: str, export_type: str = "SND", swap_x_y: bool = False) -> Tuple[bytes, Optional[str]]:
        """
        Returnerer (data, filnavn_suggesjon) hvis API svarer med binær ZIP.
        Hvis API svarer med JSON string (presignert URL), lastes den ned og returneres som binær ZIP.
        """
        path = EXPORT_PATH_TMPL.format(project_id=project_id, location_id=location_id)
        params = {"export_type": export_type, "swap_x_y": str(bool(swap_x_y)).lower()}
        resp = self._get(path, params=params, stream=True)

        # 401 mm.
        if resp.status_code == 401:
            raise PermissionError("Ugyldig eller utløpt token (401) ved eksport.")
        if resp.status_code == 422:
            # Typisk valideringsfeil – prøv å vise meldingen
            try:
                detail = resp.json()
                raise ValueError(f"Valideringsfeil (422): {detail}")
            except Exception:
                resp.raise_for_status()
        if resp.status_code != 200:
            resp.raise_for_status()

        ctype = resp.headers.get("Content-Type", "").lower()
        disp = resp.headers.get("Content-Disposition", "")

        # Hvis JSON -> trolig presignert URL i streng
        if "application/json" in ctype:
            # Les hele responsen først (ikke stream)
            resp2 = self._get(path, params=params, stream=False)
            data = resp2.json()
            if isinstance(data, str):
                # Last ned fra presignert URL uten auth-header
                dl = requests.get(data, timeout=self.timeout, stream=True)
                dl.raise_for_status()
                content = dl.content
                # Forsøk å plukke et filnavn fra URLen
                suggested = None
                try:
                    suggested = data.split("?")[0].rstrip("/").split("/")[-1]
                except Exception:
                    suggested = None
                return content, suggested
            elif isinstance(data, dict) and "url" in data:
                link = data["url"]
                dl = requests.get(link, timeout=self.timeout, stream=True)
                dl.raise_for_status()
                content = dl.content
                suggested = link.split("?")[0].rstrip("/").split("/")[-1]
                return content, suggested
            else:
                # Uventet – prøv å tolke som tekst og gi feilmelding
                raise RuntimeError(f"Uventet JSON-respons fra eksport-endepunktet: {json.dumps(data)[:500]}")

        # Hvis binært innhold (zip)
        content = resp.content
        suggested = None
        if "filename=" in disp:
            suggested = disp.split("filename=")[-1].strip('"')
        return content, suggested


# ---------------------------
# GUI
# ---------------------------
class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("System")  # eller "Dark" / "Light"
        ctk.set_default_color_theme("blue")
        self.title("Fieldmanager – Eksport av lokasjoner (SND)")
        self.geometry("980x700")

        # State
        self.client: Optional[ApiClient] = None
        self.projects: List[dict] = []
        self.locations: List[dict] = []
        self.project_index: Dict[str, str] = {}  # visningsstreng -> id
        self.location_checks: List[Tuple[dict, ctk.BooleanVar]] = []
        self.stop_flag = threading.Event()
        self.msg_queue: "queue.Queue[str]" = queue.Queue()

        # Top – token & base URL
        top = ctk.CTkFrame(self)
        top.pack(fill="x", padx=14, pady=(14, 8))

        ctk.CTkLabel(top, text="Bearer-token:").grid(row=0, column=0, sticky="w", padx=(8, 6), pady=6)
        self.token_var = ctk.StringVar()
        self.token_entry = ctk.CTkEntry(top, textvariable=self.token_var, show="•", width=500)
        self.token_entry.grid(row=0, column=1, sticky="we", padx=(0, 8), pady=6)

        self.show_token = ctk.CTkCheckBox(top, text="Vis token", command=self.toggle_token)
        self.show_token.grid(row=0, column=2, sticky="w", padx=6, pady=6)

        ctk.CTkLabel(top, text="Base-URL:").grid(row=1, column=0, sticky="w", padx=(8, 6), pady=6)
        self.base_url_var = ctk.StringVar(value=DEFAULT_BASE_URL)
        self.base_entry = ctk.CTkEntry(top, textvariable=self.base_url_var, width=500)
        self.base_entry.grid(row=1, column=1, sticky="we", padx=(0, 8), pady=6)

        self.fetch_projects_btn = ctk.CTkButton(top, text="Hent prosjekter", command=self.on_fetch_projects)
        self.fetch_projects_btn.grid(row=1, column=2, sticky="w", padx=6, pady=6)

        top.grid_columnconfigure(1, weight=1)

        # Mid – prosjektvalg & lokasjoner
        mid = ctk.CTkFrame(self)
        mid.pack(fill="both", expand=True, padx=14, pady=8)

        # Prosjektvalg
        proj_frame = ctk.CTkFrame(mid)
        proj_frame.pack(fill="x", padx=8, pady=8)
        ctk.CTkLabel(proj_frame, text="Prosjekt:").grid(row=0, column=0, sticky="w", padx=8, pady=8)
        self.project_var = ctk.StringVar()
        self.project_combo = ctk.CTkComboBox(proj_frame, values=[], variable=self.project_var, width=650)
        self.project_combo.grid(row=0, column=1, sticky="we", padx=(0, 8), pady=8)
        self.load_locations_btn = ctk.CTkButton(proj_frame, text="Hent lokasjoner", command=self.on_fetch_locations, state="disabled")
        self.load_locations_btn.grid(row=0, column=2, sticky="w", padx=8, pady=8)
        proj_frame.grid_columnconfigure(1, weight=1)

        # Lokasjonsliste
        list_frame = ctk.CTkFrame(mid)
        list_frame.pack(fill="both", expand=True, padx=8, pady=8)
        head = ctk.CTkFrame(list_frame)
        head.pack(fill="x", padx=8, pady=(8, 0))
        self.sel_count_var = ctk.StringVar(value="0 valgt")
        ctk.CTkLabel(head, textvariable=self.sel_count_var).pack(side="left")
        ctk.CTkButton(head, text="Velg alle", command=self.select_all).pack(side="right", padx=4)
        ctk.CTkButton(head, text="Fjern alle", command=self.deselect_all).pack(side="right", padx=4)

        self.scroll = ctk.CTkScrollableFrame(list_frame, height=280)
        self.scroll.pack(fill="both", expand=True, padx=8, pady=8)

        # Innstillinger og destinasjonsmappe
        settings = ctk.CTkFrame(mid)
        settings.pack(fill="x", padx=8, pady=8)

        self.swap_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(settings, text="Bytt X/Y (swap_x_y)", variable=self.swap_var).grid(row=0, column=0, sticky="w", padx=8, pady=8)

        ctk.CTkLabel(settings, text="Lagre til mappe:").grid(row=0, column=1, sticky="e", padx=8, pady=8)
        self.dir_var = ctk.StringVar()
        self.dir_entry = ctk.CTkEntry(settings, textvariable=self.dir_var, width=420)
        self.dir_entry.grid(row=0, column=2, sticky="we", padx=(0, 8), pady=8)
        ctk.CTkButton(settings, text="Velg…", command=self.choose_dir).grid(row=0, column=3, sticky="w", padx=8, pady=8)

        settings.grid_columnconfigure(2, weight=1)

        # Kontrollknapper
        actions = ctk.CTkFrame(mid)
        actions.pack(fill="x", padx=8, pady=8)
        self.start_btn = ctk.CTkButton(actions, text="Start nedlasting", command=self.start_downloads, state="disabled")
        self.start_btn.pack(side="left", padx=8, pady=8)
        self.stop_btn = ctk.CTkButton(actions, text="Stopp", command=self.stop_downloads, state="disabled")
        self.stop_btn.pack(side="left", padx=8, pady=8)

        # Logg & progresjon
        bottom = ctk.CTkFrame(self)
        bottom.pack(fill="both", expand=False, padx=14, pady=(8, 14))

        self.progress = ctk.CTkProgressBar(bottom)
        self.progress.set(0.0)
        self.progress.pack(fill="x", padx=8, pady=(10, 6))

        self.log = ctk.CTkTextbox(bottom, height=180)
        self.log.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        self.after(200, self._drain_log_queue)

    # ----------------------- UI handlers -----------------------
    def toggle_token(self):
        self.token_entry.configure(show="" if self.show_token.get() else "•")

    def on_fetch_projects(self):
        token = self.token_var.get().strip()
        base = self.base_url_var.get().strip() or DEFAULT_BASE_URL
        if not token:
            messagebox.showwarning("Mangler token", "Lim inn Bearer-token først.")
            return
        self.log_info("Henter prosjekter…")
        self.fetch_projects_btn.configure(state="disabled")
        t = threading.Thread(target=self._fetch_projects_thread, args=(base, token), daemon=True)
        t.start()

    def _fetch_projects_thread(self, base: str, token: str):
        try:
            self.client = ApiClient(base, token)
            projects = self.client.list_projects()
            # Sorter etter navn
            projects.sort(key=lambda p: (p.get("name") or "").lower())
            self.projects = projects
            # Bygg visningsverdier
            display_values = []
            self.project_index.clear()
            for p in projects:
                name = p.get("name") or "(uten navn)"
                external_id = p.get("external_id") or ""
                pid = p.get("project_id") or ""
                disp = f"{name} — {external_id} ({pid[:8]}…)" if external_id else f"{name} ({pid[:8]}…)"
                display_values.append(disp)
                self.project_index[disp] = pid
            self._set_projects_ui(display_values)
            self.log_info(f"Fant {len(projects)} prosjekt(er). Velg ett og trykk ‘Hent lokasjoner’.")
        except PermissionError as e:
            self.log_error(str(e))
            messagebox.showerror("Feil ved henting av prosjekter", str(e))
        except Exception as e:
            self.log_exception("Kunne ikke hente prosjekter", e)
        finally:
            self.fetch_projects_btn.configure(state="normal")

    def _set_projects_ui(self, values: List[str]):
        self.project_combo.configure(values=values)
        if values:
            self.project_combo.set(values[0])
            self.load_locations_btn.configure(state="normal")
        else:
            self.project_combo.set("")
            self.load_locations_btn.configure(state="disabled")

    def on_fetch_locations(self):
        if not self.client:
            messagebox.showwarning("Ingen klient", "Hent prosjekter først.")
            return
        disp = self.project_var.get().strip()
        if not disp or disp not in self.project_index:
            messagebox.showwarning("Velg prosjekt", "Velg et prosjekt fra listen.")
            return
        pid = self.project_index[disp]
        self.log_info(f"Henter lokasjoner for prosjekt {disp}…")
        self.load_locations_btn.configure(state="disabled")
        t = threading.Thread(target=self._fetch_locations_thread, args=(pid,), daemon=True)
        t.start()

    def _fetch_locations_thread(self, project_id: str):
        try:
            locs = self.client.list_locations(project_id)
            self.locations = locs
            self._populate_locations_ui(locs)
            self.log_info(f"Fant {len(locs)} lokasjon(er).")
            self.start_btn.configure(state="normal")
        except PermissionError as e:
            self.log_error(str(e))
            messagebox.showerror("Feil ved henting av lokasjoner", str(e))
        except Exception as e:
            self.log_exception("Kunne ikke hente lokasjoner", e)
        finally:
            self.load_locations_btn.configure(state="normal")

    def _populate_locations_ui(self, locs: List[dict]):
        # Tøm scroll-frame
        for child in self.scroll.winfo_children():
            child.destroy()
        self.location_checks.clear()
        # Lag checkbokser
        for i, loc in enumerate(locs, start=1):
            name = loc.get("name") or "(uten navn)"
            lid = loc.get("location_id", "")
            srid = loc.get("srid", "")
            text = f"{i:03d}  {name}  ({lid[:8]}…)  SRID:{srid}"
            var = ctk.BooleanVar(value=True)
            cb = ctk.CTkCheckBox(self.scroll, text=text, variable=var, command=self._update_selected_count)
            cb.pack(anchor="w", padx=8, pady=4)
            self.location_checks.append((loc, var))
        self._update_selected_count()

    def _update_selected_count(self):
        n = sum(1 for _, v in self.location_checks if v.get())
        self.sel_count_var.set(f"{n} valgt")

    def select_all(self):
        for _, v in self.location_checks:
            v.set(True)
        self._update_selected_count()

    def deselect_all(self):
        for _, v in self.location_checks:
            v.set(False)
        self._update_selected_count()

    def choose_dir(self):
        path = filedialog.askdirectory(title="Velg mappe for lagring")
        if path:
            self.dir_var.set(path)

    def start_downloads(self):
        if not self.client:
            messagebox.showwarning("Ingen klient", "Hent prosjekter og lokasjoner først.")
            return
        out_dir = self.dir_var.get().strip()
        if not out_dir:
            messagebox.showwarning("Mangler mappe", "Velg en mappe å lagre i.")
            return
        ensure_dir(out_dir)

        selected = [(i, loc) for i, (loc, v) in enumerate(self.location_checks, start=1) if v.get()]
        if not selected:
            messagebox.showinfo("Ingen valgt", "Velg minst én lokasjon.")
            return

        self.stop_flag.clear()
        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        self.progress.set(0.0)

        # Finn prosjektnavn for å bruke i filnavn
        proj_disp = self.project_var.get().strip()
        proj_name = proj_disp.split(" — ")[0].split(" (")[0] if proj_disp else "prosjekt"

        t = threading.Thread(target=self._download_thread, args=(selected, proj_name, out_dir), daemon=True)
        t.start()

    def stop_downloads(self):
        self.stop_flag.set()
        self.log_warn("Stopp forespurt. Avslutter etter pågående nedlasting…")

    def _download_thread(self, selected: List[Tuple[int, dict]], project_name: str, out_dir: str):
        total = len(selected)
        done = 0
        for seq, loc in selected:
            if self.stop_flag.is_set():
                break
            name = loc.get("name") or "lokasjon"
            lid = loc.get("location_id", "")
            self.log_info(f"Eksporterer {seq:03d}/{total}: {name} ({lid[:8]}…) …")
            try:
                content, suggested = self.client.export_location(
                    project_id=self.project_index[self.project_var.get().strip()],
                    location_id=lid,
                    export_type="SND",
                    swap_x_y=self.swap_var.get(),
                )
                # Filnavn
                base_name = suggested or f"{project_name}_{name}_{lid[:8]}" + ".zip"
                base_name = sanitize_filename(base_name)
                dest = os.path.join(out_dir, base_name)
                # Skriv fil
                with open(dest, "wb") as f:
                    f.write(content)
                self.log_ok(f"Lagret: {dest}")
            except PermissionError as e:
                self.log_error(str(e))
                messagebox.showerror("Autoriseringsfeil", str(e))
                break
            except Exception as e:
                self.log_exception(f"Feil ved eksport av {name}", e)
            finally:
                done += 1
                self.progress.set(done / total)
        self.stop_btn.configure(state="disabled")
        self.start_btn.configure(state="normal")
        if not self.stop_flag.is_set():
            self.log_ok("Ferdig!")
        else:
            self.log_warn("Avbrutt.")

    # ----------------------- Logging -----------------------
    def _drain_log_queue(self):
        try:
            while True:
                lvl, msg = self.msg_queue.get_nowait()
                self._append_log(lvl, msg)
        except queue.Empty:
            pass
        finally:
            self.after(250, self._drain_log_queue)

    def _append_log(self, level: str, text: str):
        prefixes = {
            "INFO": "[INFO] ",
            "OK": "[OK]   ",
            "WARN": "[ADVARSEL] ",
            "ERR": "[FEIL] ",
        }
        self.log.insert("end", prefixes.get(level, "") + text + "\n")
        self.log.see("end")

    def log_info(self, text: str):
        self.msg_queue.put(("INFO", text))

    def log_ok(self, text: str):
        self.msg_queue.put(("OK", text))

    def log_warn(self, text: str):
        self.msg_queue.put(("WARN", text))

    def log_error(self, text: str):
        self.msg_queue.put(("ERR", text))

    def log_exception(self, context: str, ex: Exception):
        self.msg_queue.put(("ERR", f"{context}: {ex}"))


if __name__ == "__main__":
    app = App()
    app.mainloop()
