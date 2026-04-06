# -*- coding: utf-8 -*-
"""
Auth Utilities
==============
Provides require_username() som fungerer lokalt og på Azure App Service.

Prioritet:
  1. Azure EasyAuth header (X-Ms-Client-Principal-Name)
  2. os.getlogin() / USERNAME env var (Windows desktop)
  3. URL query param  ?user=TBLM  — huskes via bokmerke
  4. Prompt én gang, oppdater URL så nettleseren husker det
"""

import os
import streamlit as st


def _clean(name: str) -> str:
    s = name.strip()
    return s if s.lower() not in ("nobody", "root", "appuser", "") else ""


def get_username() -> str:
    """Returnerer brukernavn hvis tilgjengelig uten brukerinteraksjon, ellers ''."""

    # 1. Azure App Service EasyAuth
    try:
        azure_user = st.context.headers.get("X-Ms-Client-Principal-Name", "")
        if azure_user:
            name = _clean(azure_user.split("@")[0] if "@" in azure_user else azure_user)
            if name:
                return name
    except Exception:
        pass

    # 2. Lokal Windows
    try:
        name = _clean(os.getlogin())
        if name:
            return name
    except OSError:
        pass
    env_user = _clean(os.environ.get("USERNAME", os.environ.get("USER", "")))
    if env_user:
        return env_user

    # 3. URL query param (?user=TBLM) — settes etter første innlogging
    qp = _clean(st.query_params.get("user", ""))
    if qp:
        st.session_state["_username"] = qp
        return qp

    # 4. Allerede satt i sesjonen
    return st.session_state.get("_username", "")


def require_username() -> str:
    """
    Returnerer brukernavn. Hvis ukjent, viser prompt og oppdaterer URL
    med ?user=navn så bokmerket husker det til neste gang.
    """
    name = get_username()
    if name:
        return name

    st.markdown("## Velkommen til RamGAP! 👋")
    st.markdown(
        "RamGAP er et internt verktøy for geotekniske analyser, tolking og modellering.\n\n"
        "**Har du spørsmål?** Ta kontakt med:\n"
        "- **Tobias Lemming**\n"
        "- **Kristoffer Aamodt**\n\n"
        "Vil du gi tilbakemeldinger, forslag eller melde inn en feil? "
        "Bruk **knappen til venstre** i sidemenyen."
    )
    st.divider()
    col1, col2 = st.columns([3, 1])
    entered = col1.text_input("Navn / brukernavn", key="_username_input",
                              placeholder="f.eks. TBLM",
                              label_visibility="collapsed")
    col1.caption("Bokmerke URL-en etterpå for å slippe å skrive inn neste gang.")
    if col2.button("Logg inn", type="primary") and entered.strip():
        clean = _clean(entered)
        if clean:
            st.session_state["_username"] = clean
            st.query_params["user"] = clean  # URL: ...azurewebsites.net/?user=TBLM
            st.rerun()

    st.stop()
    return ""  # unreachable
