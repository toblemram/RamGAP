# main.py
# -*- coding: utf-8 -*-
"""
Oppstart for CustomTkinter-app: Fieldmanager SND – nedlasting & graf.

Utvidet: bruker parse_snd_with_events slik at spyling- og slagsegmenter vises i grafen.
"""
from __future__ import annotations

import os
import sys
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk

# Lokale moduler
from gui_download import DownloadTab
from gui_plot import PlotTab


APP_TITLE = "Fieldmanager SND – Nedlasting & Graf"


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Tema/utseende
        ctk.set_appearance_mode("system")
        ctk.set_default_color_theme("blue")

        # Vindu
        self.title(APP_TITLE)
        self.geometry("1100x720")
        self.minsize(980, 640)

        # Delt state mellom faner
        self.shared = {"download_dir": os.getcwd()}

        # Topp-linje med tema-velger
        top = ctk.CTkFrame(self)
        top.pack(fill="x", padx=10, pady=(10, 0))
        ctk.CTkLabel(top, text=APP_TITLE, font=("", 16, "bold")).pack(side="left", padx=8)
        ctk.CTkLabel(top, text="Tema:").pack(side="right", padx=(8, 4))
        self.theme_var = ctk.StringVar(value="system")
        theme = ctk.CTkOptionMenu(top, values=["system", "light", "dark"], variable=self.theme_var, command=self._on_theme)
        theme.pack(side="right")

        # Tabview
        tabs = ctk.CTkTabview(self)
        tabs.pack(fill="both", expand=True, padx=10, pady=10)
        t1 = tabs.add("Nedlasting")
        t2 = tabs.add("SND-graf")

        # Faneinnhold
        self.download_tab = DownloadTab(t1, self.shared)
        self.download_tab.pack(fill="both", expand=True)

        self.plot_tab = PlotTab(t2, self.shared)
        self.plot_tab.pack(fill="both", expand=True)

        # Meny
        self._build_menu()

        # Snarvei: F5 oppdater graf-fanen fra mappe
        self.bind("<F5>", lambda e: self.plot_tab.scan_dir())

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _on_theme(self, value: str):
        try:
            ctk.set_appearance_mode(value)
        except Exception:
            pass

    def _on_close(self):
        self.destroy()

    def _build_menu(self):
        try:
            m = tk.Menu(self)
            filem = tk.Menu(m, tearoff=False)
            filem.add_command(label="Avslutt", command=self._on_close)
            m.add_cascade(label="Fil", menu=filem)

            helpm = tk.Menu(m, tearoff=False)
            helpm.add_command(label="Om", command=self._on_about)
            m.add_cascade(label="Hjelp", menu=helpm)

            self.configure(menu=m)
        except Exception:
            pass

    def _on_about(self):
        messagebox.showinfo("Om", "Fieldmanager SND – CustomTkinter UI\n\nFaner: Nedlasting (metode→SND) og SND-graf med materialsoner + spyling/slag.")


def main() -> int:
    app = App()
    app.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
