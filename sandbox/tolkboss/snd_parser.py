# snd_parser.py
# -*- coding: utf-8 -*-
"""
Parser for SND-tekstfiler med støtte for spyling- og slag-segmenter.

Funksjoner:
- find_snd_data_start(lines)
- parse_snd_text(text)
- parse_snd_with_events(text) → inkluderer spyling/slag
- parse_snd_file(path)
"""
from __future__ import annotations

from typing import List, Dict, Tuple
import re
import math

__all__ = ["find_snd_data_start", "parse_snd_text", "parse_snd_file", "parse_snd_with_events"]


def find_snd_data_start(lines: List[str]) -> int:
    star = 0
    for i, ln in enumerate(lines):
        if ln.strip().startswith('*'):
            star += 1
            if star == 4:
                j = i + 3
                return j if j < len(lines) else -1
    return -1


def _extract_floats(line: str) -> List[float]:
    flt = re.compile(r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?")
    return [float(x) for x in flt.findall(line)]


def parse_snd_text(text: str) -> Dict[str, List[float]]:
    lines = text.splitlines()
    start = find_snd_data_start(lines)
    if start < 0:
        raise ValueError("Fant ikke datastart i SND-fil (fjerde '*' mangler?)")

    depth: List[float] = []
    c2: List[float] = []
    c3: List[float] = []
    c4: List[float] = []

    for ln in lines[start:]:
        if not ln.strip():
            continue
        nums = _extract_floats(ln)
        if len(nums) >= 2:
            depth.append(nums[0])
            c2.append(nums[1])
            c3.append(nums[2] if len(nums) >= 3 else math.nan)
            c4.append(nums[3] if len(nums) >= 4 else math.nan)

    if not depth:
        raise ValueError("Fant ingen datalinjer i SND-fil.")

    return {
        "depth": depth,
        "c2": c2,
        "c3": c3,
        "c4": c4,
        "max_depth": max(depth),
    }


def parse_snd_with_events(text: str) -> Dict:
    lines = text.splitlines()
    start = find_snd_data_start(lines)
    if start < 0:
        raise ValueError("Fant ikke datastart i SND-fil.")

    depth, c2, c3, c4 = [], [], [], []
    events: List[Tuple[float, int]] = []

    for ln in lines[start:]:
        if not ln.strip():
            continue
        parts = ln.split()
        try:
            d = float(parts[0]); r = float(parts[1])
        except Exception:
            continue

        depth.append(d); c2.append(r)
        c3.append(float(parts[2]) if len(parts) >= 3 else math.nan)
        c4.append(float(parts[3]) if len(parts) >= 4 else math.nan)

        for tok in parts[2:]:
            t = tok.strip().rstrip(",.;")
            if not t:
                continue
            if t.isdigit():
                n = int(t)
                if n in (72, 73, 74, 75):
                    events.append((d, n))
            else:
                u = t.upper()
                if u == "Y1": events.append((d, 72))
                elif u == "Y2": events.append((d, 73))
                elif u == "S1": events.append((d, 74))
                elif u == "S2": events.append((d, 75))

    max_depth = max(depth) if depth else 0.0

    spyling, slag = [], []
    spy_on, slag_on = False, False
    spy_start, slag_start = 0.0, 0.0

    for d, code in sorted(events, key=lambda x: x[0]):
        if code == 72 and not spy_on:
            spy_on, spy_start = True, d
        elif code == 73 and spy_on:
            if d > spy_start: spyling.append((spy_start, d))
            spy_on = False
        elif code == 74 and not slag_on:
            slag_on, slag_start = True, d
        elif code == 75 and slag_on:
            if d > slag_start: slag.append((slag_start, d))
            slag_on = False

    if spy_on and max_depth > spy_start:
        spyling.append((spy_start, max_depth))
    if slag_on and max_depth > slag_start:
        slag.append((slag_start, max_depth))

    return {
        "depth": depth,
        "c2": c2,
        "c3": c3,
        "c4": c4,
        "max_depth": max_depth,
        "spyling": spyling,
        "slag": slag,
    }


def parse_snd_file(path: str) -> Dict[str, List[float]]:
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        text = f.read()
    return parse_snd_text(text)
