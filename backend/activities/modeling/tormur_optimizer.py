"""
Tørmur Optimizer
================
Per-section brute-force optimizer: for each section height, find the
minimum-volume (bt, bb) pair such that all V220 checks pass, with
the constraint bb >= bt.
"""
from __future__ import annotations

import copy
import math
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import List

from activities.modeling.tormur_engine import (
    TorrmurInput,
    calculate,
    volume_per_meter,
)


@dataclass
class OptimizationRange:
    """Search grid for top-width (bt) and bottom-width (bb)."""
    bt_min: float = 0.4
    bt_max: float = 3.0
    bt_step: float = 0.1
    bb_min: float = 0.4
    bb_max: float = 5.0
    bb_step: float = 0.1


@dataclass
class SectionResult:
    """Result for a single optimised cross-section."""
    station: float
    height: float
    bt: float
    bb: float
    volume_per_m: float
    sliding_factor: float   # rb / rb_krav (lower is better)
    bearing_ok: bool
    foundation_ok: bool
    all_ok: bool
    face_angle_deg: float = 0.0
    top_point: list | None = None
    bot_point: list | None = None


def _safety_factors(res) -> dict:
    """Extract safety-factor-style numbers from a TorrmurResult.

    The engine doesn't compute explicit "sliding factor" / "overturning factor"
    ratios; instead it does pass/fail checks. We synthesise indicative ratios
    from the raw output so they fit the existing run-report schema.
    """
    def _f(key, default):
        v = res.get(key, default)
        try:
            return float(v) if v not in (None, "") else default
        except (TypeError, ValueError):
            return default

    rb = _f("H42", 0)
    rb_krav = _f("H43", 1)
    sigma_V = _f("M44", 0)
    qV = _f("H41", 1)

    sliding_factor = rb_krav / rb if rb > 0 else 99.0
    bearing_factor = sigma_V / qV if qV > 0 else 99.0

    # Overturning proxy: eccentricity margin relative to b0
    b0 = _f("H44", 1)
    e = _f("H40", 0)
    overturning_factor = (b0 / 2) / (abs(e) + 0.001)

    return {
        "SlidingFactor": round(sliding_factor, 3),
        "OverturningFactor": round(overturning_factor, 3),
        "BearingFactor": round(bearing_factor, 3),
        "SlidingOk": res.get("H45") == "OK",
        "OverturningOk": res.get("H45") == "OK",
        "BearingOk": res.get("M45") == "OK",
        "AllOk": res.is_ok(),
    }


def _optimize_section(
    base_params: dict,
    height: float,
    opt_range: OptimizationRange,
) -> tuple[float, float, float, dict] | None:
    """Find the minimum-volume (bt, bb) for a given section height.

    Returns ``(bt, bb, volume, safety_factors_dict)`` or ``None`` if no
    valid solution is found.
    """
    best = None  # (volume, bt, bb, safety_dict)

    bt = opt_range.bt_min
    while bt <= opt_range.bt_max + 1e-9:
        bb = max(bt, opt_range.bb_min)  # constraint: bb >= bt
        while bb <= opt_range.bb_max + 1e-9:
            inp_dict = {**base_params, "H": height, "bt": bt, "bb": bb}
            inp = TorrmurInput(**{
                k: v for k, v in inp_dict.items()
                if k in TorrmurInput.__dataclass_fields__
            })
            res = calculate(inp)

            if res.is_ok():
                vol = volume_per_meter(bt, bb, height)
                sf = _safety_factors(res)
                if best is None or vol < best[0]:
                    best = (vol, bt, bb, sf)
                break  # bb found for this bt — increasing bb won't reduce volume
            bb = round(bb + opt_range.bb_step, 6)
        bt = round(bt + opt_range.bt_step, 6)

    if best is None:
        return None
    return (best[1], best[2], best[0], best[3])


def optimize_wall(
    base_params: dict,
    sections: list[dict],
    opt_range: OptimizationRange | None = None,
    smooth_window: int = 3,
) -> list[SectionResult]:
    """Optimise all wall sections.

    Parameters
    ----------
    base_params : dict
        V220 parameters **excluding** H, bt, bb (those are set per section).
    sections : list[dict]
        Each dict must have ``station`` (float) and ``height`` (float).
    opt_range : OptimizationRange, optional
        Search grid bounds.  Defaults to sensible range.
    smooth_window : int
        Rolling-average window for smoothing bt/bb across adjacent sections.

    Returns
    -------
    list[SectionResult]
        One entry per input section, sorted by station.
    """
    if opt_range is None:
        opt_range = OptimizationRange()

    # Coerce all param values to float (guards against JSON-loaded strings)
    base_params = {
        k: (float(v) if isinstance(v, str) else v)
        for k, v in base_params.items()
    }

    results: list[SectionResult] = []

    for sec in sorted(sections, key=lambda s: s["station"]):
        h = sec["height"]
        if h <= 0:
            results.append(SectionResult(
                station=sec["station"], height=h,
                bt=0, bb=0, volume_per_m=0,
                sliding_factor=0, bearing_ok=True,
                foundation_ok=True, all_ok=True,
                top_point=sec.get("top_point"),
                bot_point=sec.get("bot_point"),
            ))
            continue

        opt = _optimize_section(base_params, h, opt_range)
        if opt is None:
            # No valid solution — use largest dimensions
            results.append(SectionResult(
                station=sec["station"], height=h,
                bt=opt_range.bt_max, bb=opt_range.bb_max,
                volume_per_m=volume_per_meter(opt_range.bt_max, opt_range.bb_max, h),
                sliding_factor=0, bearing_ok=False,
                foundation_ok=False, all_ok=False,
                top_point=sec.get("top_point"),
                bot_point=sec.get("bot_point"),
            ))
        else:
            bt_opt, bb_opt, vol, sf = opt
            results.append(SectionResult(
                station=sec["station"], height=h,
                bt=bt_opt, bb=bb_opt, volume_per_m=vol,
                sliding_factor=sf.get("SlidingFactor", 0),
                bearing_ok=sf.get("BearingOk", False),
                foundation_ok=sf.get("SlidingOk", False),
                all_ok=sf.get("AllOk", False),
                top_point=sec.get("top_point"),
                bot_point=sec.get("bot_point"),
            ))

    # --- Smoothing ---
    if smooth_window > 1 and len(results) >= smooth_window:
        bt_vals = [r.bt for r in results]
        bb_vals = [r.bb for r in results]
        bt_smooth = _smooth(bt_vals, smooth_window)
        bb_smooth = _smooth(bb_vals, smooth_window)

        for i, r in enumerate(results):
            r.bt = round(bt_smooth[i], 3)
            r.bb = max(round(bb_smooth[i], 3), r.bt)  # maintain bb >= bt
            r.volume_per_m = volume_per_meter(r.bt, r.bb, r.height)

        # Re-verify after smoothing
        for r in results:
            if r.height <= 0:
                continue
            inp_dict = {**base_params, "H": r.height, "bt": r.bt, "bb": r.bb}
            inp = TorrmurInput(**{
                k: v for k, v in inp_dict.items()
                if k in TorrmurInput.__dataclass_fields__
            })
            res = calculate(inp)
            sf = _safety_factors(res)
            r.all_ok = sf["AllOk"]
            r.bearing_ok = sf["BearingOk"]
            r.foundation_ok = sf["SlidingOk"]
            r.sliding_factor = sf["SlidingFactor"]

    # Compute face angle
    for r in results:
        if r.height > 0 and (r.bb - r.bt) > 0:
            r.face_angle_deg = round(
                math.degrees(math.atan2(r.bb - r.bt, r.height)), 2
            )

    return results


def _smooth(values: list[float], window: int) -> list[float]:
    """Simple centered moving average with edge padding."""
    n = len(values)
    half = window // 2
    out = []
    for i in range(n):
        lo = max(0, i - half)
        hi = min(n, i + half + 1)
        out.append(sum(values[lo:hi]) / (hi - lo))
    return out
