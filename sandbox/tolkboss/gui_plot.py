# gui_plot.py
# -*- coding: utf-8 -*-
"""
GUI-fane: Visualisering av SND-filer.
- Viser motstand (kol. 2) vs. dybde
- Tegner spyling- og slag-segmenter som venstre barer
- Dynamisk lagliste (vilkårlig mange lag, valgfri rekkefølge: leire/sand/fjell/annet)
- Ingen legend i plottet
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import List, Dict

import customtkinter as ctk
from tkinter import messagebox

try:
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
except ImportError as e:
    import tkinter as tk
    root = tk.Tk(); root.withdraw()
    messagebox.showerror(
        "Manglende pakke",
        f"Matplotlib mangler i valgt miljø.\n\n{e}\n\nKjør i terminalen:\n  pip install matplotlib",
    )
    raise

from snd_parser import parse_snd_with_events


# Farger for materialtyper
MAT_COLORS = {
    "leire": (0.80, 0.40, 0.40),
    "sand":  (0.80, 0.80, 0.40),
    "fjell": (0.60, 0.80, 0.90),
    "annet": (0.85, 0.85, 0.85),
}
MAT_LIST = ["leire", "sand", "fjell", "annet"]


@dataclass
class SndFile:
    path: str
    depth: List[float]
    c2: List[float]
    c3: List[float]
    c4: List[float]
    max_depth: float
    spyling: List[tuple]
    slag: List[tuple]


class PlotTab(ctk.CTkFrame):
    def __init__(self, master, shared_state: Dict):
        super().__init__(master)
        self.shared = shared_state
        self.files: List[SndFile] = []
        self.idx: int = -1
        self.max_depth: float = 0.0
        self._suspend = False

        # --- Layout wrapper
        wrapper = ctk.CTkFrame(self)
        wrapper.pack(fill="both", expand=True, padx=8, pady=8)

        # --- Venstre: graf
        left = ctk.CTkFrame(wrapper)
        left.pack(side="left", fill="both", expand=True, padx=(8, 6), pady=8)
        self.fig = Figure(figsize=(6, 5), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_xlabel("Motstand (kol. 2)")
        self.ax.set_ylabel("Dybde (m)")
        self.ax.grid(True, which='both', linestyle=':')
        self.ax.invert_yaxis()
        self.canvas = FigureCanvasTkAgg(self.fig, master=left)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        nav = ctk.CTkFrame(left)
        nav.pack(fill="x", padx=4, pady=(6, 6))
        self.file_label = ctk.StringVar(value="—")
        ctk.CTkLabel(nav, textvariable=self.file_label).pack(side="left", padx=6)
        ctk.CTkButton(nav, text="◀ Forrige", command=self.prev_file).pack(side="right", padx=4)
        ctk.CTkButton(nav, text="Neste ▶", command=self.next_file).pack(side="right", padx=4)

        # --- Høyre: kontroller (mappe, info, lag)
        right = ctk.CTkFrame(wrapper)
        right.pack(side="left", fill="y", padx=(6, 8), pady=8)

        # Mappe / oppdater
        ctk.CTkButton(right, text="Oppdater fra mappe", command=self.scan_dir).pack(fill="x", padx=8, pady=(8, 6))
        self.depth_info = ctk.StringVar(value="Max dybde: –")
        ctk.CTkLabel(right, textvariable=self.depth_info).pack(anchor="w", padx=12, pady=(2, 8))

        # Forklaring for barer (kun UI-tekst – plottet har ingen legend)
        legendf = ctk.CTkFrame(right)
        legendf.pack(fill="x", padx=8, pady=(0, 8))
        ctk.CTkLabel(legendf, text="Forklaring:", font=("", 13, "bold")).pack(anchor="w", padx=4, pady=(2, 4))
        ctk.CTkLabel(legendf, text="▌ Spyling (blå venstrefelt)").pack(anchor="w", padx=12)
        ctk.CTkLabel(legendf, text="▌ Slag (rødt venstrefelt)").pack(anchor="w", padx=12)

        # --- Dynamisk lagliste
        lag_header = ctk.CTkFrame(right)
        lag_header.pack(fill="x", padx=8, pady=(6, 0))
        ctk.CTkLabel(lag_header, text="Lag (type / start / slutt)", font=("", 13, "bold")).pack(side="left", padx=4, pady=(0, 2))

        buttons = ctk.CTkFrame(right)
        buttons.pack(fill="x", padx=8, pady=(4, 8))
        ctk.CTkButton(buttons, text="Legg til lag", command=self._add_layer).pack(side="left", padx=(0, 6))
        ctk.CTkButton(buttons, text="Auto 3 lag", command=self._auto_three_layers).pack(side="left", padx=6)
        ctk.CTkButton(buttons, text="Sorter/Klem", command=self._normalize_layers).pack(side="left", padx=6)

        self.layers_frame = ctk.CTkScrollableFrame(right, height=260)
        self.layers_frame.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        # intern modell av lag (liste av dict: {"type": str, "start": float, "end": float})
        self.layers: List[Dict] = []
        self.layer_rows: List[Dict] = []  # holder på widgets/vars per rad

    # ---------- Filnavigasjon ----------
    def prev_file(self):
        if not self.files:
            return
        self.idx = (self.idx - 1) % len(self.files)
        self._load_index(self.idx, init_layers=True)

    def next_file(self):
        if not self.files:
            return
        self.idx = (self.idx + 1) % len(self.files)
        self._load_index(self.idx, init_layers=True)

    def scan_dir(self):
        d = self.shared.get("download_dir")
        if not d or not os.path.isdir(d):
            messagebox.showinfo("Ingen mappe", "Velg/bruk samme mappe som i Nedlasting-fanen.")
            return
        paths = []
        for root, _, fns in os.walk(d):
            for fn in fns:
                if fn.lower().endswith((".snd", ".txt")):
                    paths.append(os.path.join(root, fn))
        paths.sort()
        self.files.clear()
        for p in paths:
            try:
                with open(p, "r", encoding="utf-8", errors="ignore") as f:
                    text = f.read()
                parsed = parse_snd_with_events(text)
                self.files.append(SndFile(path=p, **parsed))
            except Exception:
                # hopp over filer som ikke kan parses
                pass
        if not self.files:
            self.file_label.set("Fant ingen SND i mappa")
            self.ax.clear()
            self.ax.set_xlabel("Motstand (kol. 2)")
            self.ax.set_ylabel("Dybde (m)")
            self.ax.grid(True, linestyle=':')
            self.ax.invert_yaxis()
            self.canvas.draw_idle()
            return
        self.idx = 0
        self._load_index(self.idx, init_layers=True)

    # ---------- Lag-UI ----------
    def _add_layer(self, preset: Dict | None = None):
        """Legg til ny lagrad i UI + modell."""
        if self.idx < 0:
            return
        # default forslag: fortsett fra siste slutt
        default_type = "leire"
        last_end = 0.0 if not self.layers else float(self.layers[-1]["end"])
        end_sug = min(last_end + max(0.1, self.max_depth * 0.1), self.max_depth)
        layer = {
            "type": default_type,
            "start": float(last_end),
            "end": float(end_sug),
        }
        if preset:
            layer.update(preset)
            # klem verdier
            layer["start"] = max(0.0, min(self.max_depth, float(layer["start"])))
            layer["end"]   = max(0.0, min(self.max_depth, float(layer["end"])))
        self.layers.append(layer)
        self._insert_layer_row(len(self.layers) - 1, layer)
        self._normalize_layers()
        self._redraw_plot()

    def _auto_three_layers(self):
        """Foreslå tre like dype lag (kan endres i etterkant)."""
        if self.idx < 0:
            return
        a = 0.0
        b = self.max_depth/3.0
        c = 2.0*self.max_depth/3.0
        d = self.max_depth
        presets = [
            {"type": "leire", "start": a, "end": b},
            {"type": "sand",  "start": b, "end": c},
            {"type": "fjell", "start": c, "end": d},
        ]
        self.layers = []
        for w in self.layers_frame.winfo_children():
            w.destroy()
        self.layer_rows.clear()
        for p in presets:
            self._add_layer(preset=p)

    def _insert_layer_row(self, index: int, layer: Dict):
        """Lag én rad med (type, start, slutt, ▲, ▼, ✖)."""
        rowf = ctk.CTkFrame(self.layers_frame)
        rowf.grid_columnconfigure(1, weight=1)
        rowf.pack(fill="x", padx=4, pady=3)

        tvar = ctk.StringVar(value=layer["type"])
        svar = ctk.StringVar(value=f"{layer['start']:.2f}")
        evar = ctk.StringVar(value=f"{layer['end']:.2f}")

        # Type
        typ = ctk.CTkOptionMenu(rowf, values=MAT_LIST, variable=tvar,
                                command=lambda *_: self._on_layer_changed())
        typ.configure(width=90)
        typ.pack(side="left", padx=(6, 6))

        # Start / Slutt
        st = ctk.CTkEntry(rowf, textvariable=svar, width=80)
        en = ctk.CTkEntry(rowf, textvariable=evar, width=80)
        ctk.CTkLabel(rowf, text="Start").pack(side="left", padx=(0, 4))
        st.pack(side="left")
        ctk.CTkLabel(rowf, text="Slutt").pack(side="left", padx=(8, 4))
        en.pack(side="left")

        st.bind("<FocusOut>", lambda _e: self._on_layer_changed())
        en.bind("<FocusOut>", lambda _e: self._on_layer_changed())
        st.bind("<Return>", lambda _e: self._on_layer_changed())
        en.bind("<Return>", lambda _e: self._on_layer_changed())

        # Flytt / Slett
        up   = ctk.CTkButton(rowf, text="▲", width=24, command=lambda: self._move_layer(rowf, -1))
        down = ctk.CTkButton(rowf, text="▼", width=24, command=lambda: self._move_layer(rowf, +1))
        rem  = ctk.CTkButton(rowf, text="✖", width=28, fg_color="#b33", hover_color="#922",
                             command=lambda: self._remove_layer(rowf))
        down.pack(side="right", padx=4)
        up.pack(side="right", padx=4)
        rem.pack(side="right", padx=(8,4))

        self.layer_rows.append({"frame": rowf, "tvar": tvar, "svar": svar, "evar": evar})

    def _row_index(self, frame: ctk.CTkFrame) -> int:
        for i, r in enumerate(self.layer_rows):
            if r["frame"] is frame:
                return i
        return -1

    def _move_layer(self, frame: ctk.CTkFrame, delta: int):
        i = self._row_index(frame)
        if i < 0:
            return
        j = i + delta
        if j < 0 or j >= len(self.layer_rows):
            return
        # bytt i UI-lista
        self.layer_rows[i], self.layer_rows[j] = self.layer_rows[j], self.layer_rows[i]
        # re-pack i ny rekkefølge
        for r in self.layers_frame.winfo_children():
            r.pack_forget()
        for r in self.layer_rows:
            r["frame"].pack(fill="x", padx=4, pady=3)
        self._on_layer_changed()

    def _remove_layer(self, frame: ctk.CTkFrame):
        i = self._row_index(frame)
        if i < 0:
            return
        frame.destroy()
        del self.layer_rows[i]
        self._on_layer_changed()

    def _on_layer_changed(self):
        """Les verdier fra radene, oppdater self.layers, normaliser og tegn."""
        layers: List[Dict] = []
        for r in self.layer_rows:
            try:
                t = r["tvar"].get().strip().lower()
                s = float(r["svar"].get().strip().replace(",", "."))
                e = float(r["evar"].get().strip().replace(",", "."))
            except Exception:
                # hopp over rader med ugyldig input
                continue
            layers.append({"type": t if t in MAT_LIST else "annet", "start": s, "end": e})
        self.layers = layers
        self._normalize_layers()
        self._redraw_plot()

    def _normalize_layers(self):
        """Sorter etter start, klem til [0, max_depth], og sørg for start<=slutt."""
        if self.idx < 0:
            return
        norm: List[Dict] = []
        for L in self.layers:
            s = max(0.0, min(self.max_depth, float(L["start"])))
            e = max(0.0, min(self.max_depth, float(L["end"])))
            if e < s:
                s, e = e, s
            norm.append({"type": (L["type"] if L["type"] in MAT_LIST else "annet"), "start": s, "end": e})
        norm.sort(key=lambda x: x["start"])
        self.layers = norm
        # push normaliserte verdier tilbake til UI
        for r, L in zip(self.layer_rows, self.layers):
            r["tvar"].set(L["type"])
            r["svar"].set(f"{L['start']:.2f}")
            r["evar"].set(f"{L['end']:.2f}")
        # oppdatere dybdeinfotekst også
        self.depth_info.set(f"Max dybde: {self.max_depth:.2f} m")

    # ---------- Internt ----------
    def _load_index(self, i: int, init_layers: bool):
        item = self.files[i]
        self.file_label.set(os.path.basename(item.path))
        self.max_depth = float(item.max_depth)

        if init_layers:
            # bygg 3 standardlag (kan fjernes/endres/utvides fritt)
            a = 0.0; b = self.max_depth/3.0; c = 2.0*self.max_depth/3.0; d = self.max_depth
            initial = [
                {"type": "leire", "start": a, "end": b},
                {"type": "sand",  "start": b, "end": c},
                {"type": "fjell", "start": c, "end": d},
            ]
            # tøm UI
            for w in self.layers_frame.winfo_children():
                w.destroy()
            self.layer_rows.clear()
            self.layers = []
            for p in initial:
                self._add_layer(preset=p)

        self._redraw_plot()

    # ---------- Tegning ----------
    def _redraw_plot(self):
        if self.idx < 0 or not self.files:
            return
        item = self.files[self.idx]
        self.ax.clear()

        # motstandslinje (ingen label)
        self.ax.plot(item.c2, item.depth, color="black")
        self.ax.set_xlabel("Motstand (kol. 2)")
        self.ax.set_ylabel("Dybde (m)")
        self.ax.grid(True, which='both', linestyle=':')
        self.ax.invert_yaxis()

        # lag (vilkårlig mange, rekkefølge allerede sortert)
        for L in self.layers:
            a = max(0.0, min(self.max_depth, float(L["start"])))
            b = max(0.0, min(self.max_depth, float(L["end"])))
            if b <= a:
                continue
            col = MAT_COLORS.get(L["type"], MAT_COLORS["annet"])
            self.ax.axhspan(a, b, alpha=0.25, color=col)

        # venstrefelt: spyling/slag (uten label/legend)
        for a, b in item.spyling:
            self.ax.axhspan(a, b, xmin=0.0, xmax=0.05, color="blue", alpha=0.5)
        for a, b in item.slag:
            self.ax.axhspan(a, b, xmin=0.05, xmax=0.1, color="red", alpha=0.5)

        self.canvas.draw_idle()
