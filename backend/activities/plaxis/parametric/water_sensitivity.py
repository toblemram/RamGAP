# -*- coding: utf-8 -*-
"""
Water Level Sensitivity Runner
===============================
Executes a single iteration of a water-level sensitivity study:

1. Set the borehole water head to the requested level.
2. Run Plaxis calculations.
3. Connect to Plaxis Output and extract:
   - MSF (safety factor) from the FoS phase
   - Max Ux (horizontal displacement) on the selected plate
   - Max M (bending moment) on the selected plate

Public API:
    run_single_water_level(g_i, s_i, ...) -> dict
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

try:
    from plxscripting.easy import new_server
    PLAXIS_AVAILABLE = True
except ImportError:
    new_server = None  # type: ignore[assignment]
    PLAXIS_AVAILABLE = False

from activities.plaxis.parametric.runner import (
    _extract_max_moment,
    _extract_max_ux,
    _extract_msf,
    _find_phase_by_name,
    _find_plate_by_name,
)

log = logging.getLogger(__name__)


def _set_water_head(g_i, water_level: float) -> None:
    """Set the water head on all boreholes in the model."""
    g_i.gotosoil()
    for bh in g_i.Boreholes:
        bh.Head.set(water_level)
        log.info("Set %s.Head = %s", bh.Name.value, water_level)


def run_single_water_level(
    g_i,
    s_i,
    water_level: float,
    plate_name: Optional[str] = None,
    fos_phase: Optional[str] = None,
    disp_phase: Optional[str] = None,
    cap_phase: Optional[str] = None,
    output_port: Optional[int] = None,
    output_password: Optional[str] = None,
) -> Dict[str, Any]:
    """Execute one water-level sensitivity iteration.

    1. Set borehole water head
    2. Run calculation
    3. Extract MSF / Ux / M from output
    4. Return results dict
    """
    result: Dict[str, Any] = {
        "success": False,
        "water_level": water_level,
        "msf": None,
        "ux_max": None,
        "m_max": None,
    }

    # --- 1. Modify water head ------------------------------------------------
    _set_water_head(g_i, water_level)

    # --- 2. Run calculation --------------------------------------------------
    try:
        g_i.calculate()
    except Exception as exc:
        result["error"] = f"Calculation failed: {exc}"
        return result

    # --- 3. Connect to Output and extract results ----------------------------
    g_o = None
    try:
        if output_port and PLAXIS_AVAILABLE:
            pwd = output_password or ""
            _s_o, g_o = new_server("localhost", int(output_port), password=pwd)
    except Exception as exc:
        log.warning("Could not connect to Output server: %s", exc)

    if g_o is None:
        result["success"] = True
        result["error"] = (
            "Calculation ran but could not connect to Output for result extraction."
        )
        return result

    # Resolve output phases and extract results
    try:
        if fos_phase:
            o_fos = _find_phase_by_name(g_o, fos_phase)
            result["msf"] = _extract_msf(g_o, o_fos)

        o_plate = None
        if plate_name:
            o_plate = _find_plate_by_name(g_o, plate_name)

        if o_plate and disp_phase:
            o_disp = _find_phase_by_name(g_o, disp_phase)
            result["ux_max"] = _extract_max_ux(g_o, o_plate, o_disp)

        if o_plate and cap_phase:
            o_cap = _find_phase_by_name(g_o, cap_phase)
            result["m_max"] = _extract_max_moment(g_o, o_plate, o_cap)

        result["success"] = True
    except Exception as exc:
        result["error"] = f"Result extraction failed: {exc}"
        result["success"] = True  # calc succeeded, extraction partially failed

    return result
