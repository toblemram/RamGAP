# api_client.py
# -*- coding: utf-8 -*-
"""
API-klient for Fieldmanager som bruker **metode-eksport** og henter **SND-filer (ikke ZIP)**.

Brukte endepunkt:
  GET /projects
  GET /projects/{project_id}/locations
  GET /projects/{project_id}/locations/{location_id}/methods
  GET /projects/{project_id}/locations/{location_id}/methods/{method_id}/export?export_type=SND&swap_x_y=false

Merk:
- Noen installasjoner returnerer JSON (presignert URL) når du spør om SND. Vi følger URL-en og
  henter selve .SND-innholdet som **tekst**.
- Hvis serveren returnerer ren tekst direkte (Content-Type: text/plain e.l.), bruker vi den direkte.
- Funksjonen `export_method_snd` returnerer `(text, foreslått_filnavn)` der `text` er SND-innholdet.
"""
from __future__ import annotations

from typing import List, Optional, Tuple
import json
import requests

DEFAULT_BASE_URL = "https://api.fieldmanager.io/fieldmanager"
PROJECTS_PATH = "/projects"
LOCATIONS_PATH_TMPL = "/projects/{project_id}/locations"
METHODS_PATH_TMPL = "/projects/{project_id}/locations/{location_id}/methods"
METHOD_EXPORT_PATH_TMPL = "/projects/{project_id}/locations/{location_id}/methods/{method_id}/export"
DEFAULT_LIMIT = 100


def join_url(base: str, path: str) -> str:
    return base.rstrip("/") + "/" + path.lstrip("/")


class ApiClient:
    def __init__(self, base_url: str, token: str, timeout: int = 60):
        self.base_url = base_url or DEFAULT_BASE_URL
        self.timeout = timeout
        self.session = requests.Session()
        # Sett bare auth her; Accept settes per-kall (eksport trenger "*/*")
        self.session.headers.update({"Authorization": f"Bearer {token}"})

    # --- interne ---
    def _get(self, path: str, params: Optional[dict] = None, headers: Optional[dict] = None) -> requests.Response:
        url = join_url(self.base_url, path)
        hdrs = {**self.session.headers}
        if headers:
            hdrs.update(headers)
        return self.session.get(url, params=params, timeout=self.timeout, headers=hdrs)

    # --- lister ---
    def list_projects(self) -> List[dict]:
        items: List[dict] = []
        skip = 0
        while True:
            r = self._get(PROJECTS_PATH, params={"skip": skip, "limit": DEFAULT_LIMIT}, headers={"accept": "application/json"})
            if r.status_code == 401:
                raise PermissionError("Ugyldig eller utløpt token (401).")
            r.raise_for_status()
            chunk = r.json() or []
            if not chunk:
                break
            items += chunk
            if len(chunk) < DEFAULT_LIMIT:
                break
            skip += DEFAULT_LIMIT
        return items

    def list_locations(self, project_id: str) -> List[dict]:
        path = LOCATIONS_PATH_TMPL.format(project_id=project_id)
        items: List[dict] = []
        skip = 0
        while True:
            r = self._get(path, params={"skip": skip, "limit": DEFAULT_LIMIT}, headers={"accept": "application/json"})
            if r.status_code == 401:
                raise PermissionError("Ugyldig eller utløpt token (401).")
            r.raise_for_status()
            chunk = r.json() or []
            if not chunk:
                break
            items += chunk
            if len(chunk) < DEFAULT_LIMIT:
                break
            skip += DEFAULT_LIMIT
        return items

    def list_methods(self, project_id: str, location_id: str) -> List[dict]:
        path = METHODS_PATH_TMPL.format(project_id=project_id, location_id=location_id)
        items: List[dict] = []
        skip = 0
        while True:
            r = self._get(path, params={"skip": skip, "limit": DEFAULT_LIMIT}, headers={"accept": "application/json"})
            if r.status_code == 401:
                raise PermissionError("Ugyldig eller utløpt token (401).")
            r.raise_for_status()
            chunk = r.json() or []
            if not chunk:
                break
            items += chunk
            if len(chunk) < DEFAULT_LIMIT:
                break
            skip += DEFAULT_LIMIT
        return items

    # --- eksport (metode → SND som tekst) ---
    def export_method_snd(self, project_id: str, location_id: str, method_id: str, swap_x_y: bool = False) -> Tuple[str, Optional[str]]:
        """
        Hent SND-innhold for **metode** som tekst. Returnerer (text, foreslått_filnavn).

        Håndterer:
        - Direkte tekst-respons fra API (text/plain e.l.)
        - JSON-respons som inneholder presignert URL (enten ren streng eller dict med "url")
        - 401/422-feil med forståelige meldinger
        """
        path = METHOD_EXPORT_PATH_TMPL.format(project_id=project_id, location_id=location_id, method_id=method_id)
        params = {"export_type": "SND", "swap_x_y": str(bool(swap_x_y)).lower()}

        # Viktig: ikke tving Accept til application/json – vi ønsker ren tekst hvis mulig
        r = self._get(path, params=params, headers={"accept": "*/*"})
        if r.status_code == 401:
            raise PermissionError("Ugyldig eller utløpt token (401) ved metode-eksport.")
        if r.status_code == 422:
            # prøv å vise valideringsfeil fra backend
            try:
                detail = r.json()
                raise ValueError(f"Valideringsfeil (422): {detail}")
            except Exception:
                r.raise_for_status()
        r.raise_for_status()

        ctype = (r.headers.get("Content-Type") or "").lower()
        disp = r.headers.get("Content-Disposition", "")

        # JSON – sannsynligvis presignert URL
        if "application/json" in ctype:
            data = r.json()
            url = data if isinstance(data, str) else data.get("url") if isinstance(data, dict) else None
            if not url:
                # Noen spesifikasjoner sier "Controls Accept header" og eksempelverdi er "string".
                # Dersom vi får noe annet, logg det i feilmeldingen.
                raise RuntimeError(f"Uventet JSON-response fra eksport: {json.dumps(data)[:300]}")
            dl = requests.get(url, timeout=self.timeout)
            dl.raise_for_status()
            text = dl.text
            # filnavn fra URL dersom mulig
            try:
                suggested = url.split("?")[0].rstrip("/").split("/")[-1]
                if suggested and not suggested.lower().endswith(".snd"):
                    suggested += ".snd"
            except Exception:
                suggested = None
            return text, suggested

        # Direkte tekst (ønsket)
        text = r.text
        suggested = None
        if "filename=" in disp:
            suggested = disp.split("filename=")[-1].strip('"')
            if suggested and not suggested.lower().endswith(".snd"):
                suggested += ".snd"
        return text, suggested
