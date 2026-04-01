# -*- coding: utf-8 -*-
"""
Parametric Spunt Runner
=======================
Executes a single iteration of a parametric sheet-pile study:

1. Locate the KS soil material and modify its undrained shear strength (Su).
2. Optionally adjust the sheet-pile (plate) embedment depth.
3. Run Plaxis calculations.
4. Connect to Plaxis Output and extract:
   - MSF (safety factor) from the FoS phase
   - Max Ux (displacement) from the displacement phase
   - Max M (bending moment) from the capacity phase

Public API:
    run_single_parametric(g_i, s_i, ...) -> dict
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

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _find_material_by_name(g_i, name: str):
    """Return the Plaxis material object matching *name*."""
    for mat in g_i.Materials:
        try:
            if mat.Identification.value == name:
                return mat
        except Exception:
            continue
    raise ValueError(f"Material '{name}' not found in model.")


def _find_phase_by_name(g_i, name: str):
    """Return the Plaxis phase object matching *name*."""
    for phase in g_i.Phases:
        try:
            if phase.Identification.value == name:
                return phase
        except Exception:
            continue
    raise ValueError(f"Phase '{name}' not found in model.")


def _find_plate_by_name(g_i, name: str):
    """Return the Plaxis plate object matching *name*."""
    for plate in g_i.Plates:
        try:
            if plate.Name.value == name:
                return plate
        except Exception:
            continue
    raise ValueError(f"Plate '{name}' not found in model.")


def _set_su(g_i, material, su_value: float) -> None:
    """Set the undrained shear strength reference (SuRef) on a soil material.

    Handles multiple Plaxis material model layouts:
    - material.SuRef (direct attribute)
    - material.MohrCoulombPlasticity.SuRef
    - material.NGI_ADP.SuRef / material.NGI_ADP.SuA_ref
    """
    # Try direct attribute — Plaxis uses lowercase 'sURef' in 2D
    for attr in ('sURef', 'SuRef', 'su_ref', 'suref'):
        if hasattr(material, attr):
            getattr(material, attr).set(su_value)
            log.info("Set %s.%s = %s", material.Identification.value, attr, su_value)
            return

    # Fallback: use setproperties
    try:
        material.setproperties("sURef", su_value)
        log.info("Set sURef via setproperties = %s", su_value)
        return
    except Exception:
        pass

    raise RuntimeError(
        f"Could not set Su on material '{material.Identification.value}'. "
        "No known Su attribute found (tried sURef, SuRef)."
    )


def _adjust_plate_depth(g_i, plate, new_bottom_y: float) -> None:
    """Move the bottom point of a plate to *new_bottom_y*.

    In Plaxis 2D, a Plate sits on a Line which has First/Second points.
    We find the lower point and move its y coordinate.
    """
    try:
        line = plate.Parent.value
        p1 = line.First.value
        p2 = line.Second.value
        y1 = p1.y.value
        y2 = p2.y.value

        if y1 < y2:
            bottom_pt = p1
        else:
            bottom_pt = p2

        bottom_pt.y.set(new_bottom_y)
        log.info("Moved plate '%s' bottom to y=%s", plate.Name.value, new_bottom_y)
    except Exception as exc:
        raise RuntimeError(
            f"Could not adjust plate depth for '{plate.Name.value}': {exc}"
        ) from exc


def _extract_msf(g_o, phase) -> Optional[float]:
    """Extract the MSF (safety factor) from an Output phase."""
    # Try multiple accessor patterns (version-dependent)
    for accessor in (
        lambda p: p.Reached.SumMsf.value,
        lambda p: p.Reached.MsfReached.value,
        lambda p: p.Reached.Msf.value,
        lambda p: p.DeformCalcSafety.MsfReached.value,
        lambda p: p.SafetyCalculation.MsfReached.value,
    ):
        try:
            return accessor(phase)
        except Exception:
            continue
    return None


def _extract_max_ux(g_o, plate, phase) -> Optional[float]:
    """Extract maximum absolute Ux displacement on *plate* in *phase*."""
    result_type = None
    if hasattr(g_o.ResultTypes, 'Plate'):
        pt = g_o.ResultTypes.Plate
        for name in ('Ux', 'Ux2D'):
            if hasattr(pt, name):
                result_type = getattr(pt, name)
                break

    if result_type is None:
        return None

    for call_fn in (
        lambda: g_o.getresults(plate, phase, result_type, 'node'),
        lambda: g_o.getresults(phase, result_type, 'node', plate),
    ):
        try:
            vals = call_fn()
            if vals:
                return max(abs(v) for v in vals)
        except Exception:
            continue
    return None


def _extract_max_moment(g_o, plate, phase) -> Optional[float]:
    """Extract maximum absolute bending moment M on *plate* in *phase*."""
    result_type = None
    if hasattr(g_o.ResultTypes, 'Plate'):
        pt = g_o.ResultTypes.Plate
        for name in ('M2D', 'M', 'Mx'):
            if hasattr(pt, name):
                result_type = getattr(pt, name)
                break

    if result_type is None:
        return None

    for call_fn in (
        lambda: g_o.getresults(plate, phase, result_type, 'node'),
        lambda: g_o.getresults(phase, result_type, 'node', plate),
    ):
        try:
            vals = call_fn()
            if vals:
                return max(abs(v) for v in vals)
        except Exception:
            continue
    return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def run_single_parametric(
    g_i,
    s_i,
    ks_soil_name: str,
    plate_name: str,
    su: float,
    depth: Optional[float] = None,
    fos_phase: Optional[str] = None,
    disp_phase: Optional[str] = None,
    cap_phase: Optional[str] = None,
    output_port: Optional[int] = None,
    output_password: Optional[str] = None,
) -> Dict[str, Any]:
    """Execute one parametric iteration.

    1. Modify KS soil Su
    2. Optionally change spunt depth
    3. Run calculation
    4. Extract MSF / Ux / M from output
    5. Return results dict
    """
    result: Dict[str, Any] = {'success': False, 'msf': None, 'ux_max': None, 'm_max': None}

    # --- 1. Modify material --------------------------------------------------
    material = _find_material_by_name(g_i, ks_soil_name)
    _set_su(g_i, material, su)

    # --- 2. Optionally adjust plate depth ------------------------------------
    plate_obj = _find_plate_by_name(g_i, plate_name) if plate_name else None
    if depth is not None and plate_obj is not None:
        _adjust_plate_depth(g_i, plate_obj, depth)

    # --- 3. Run calculation --------------------------------------------------
    try:
        g_i.calculate()
    except Exception as exc:
        result['error'] = f"Calculation failed: {exc}"
        return result

    # --- 4. Connect to Output and extract results ----------------------------
    g_o = None
    try:
        if output_port and PLAXIS_AVAILABLE:
            pwd = output_password or ''
            _s_o, g_o = new_server('localhost', int(output_port), password=pwd)
    except Exception as exc:
        log.warning("Could not connect to Output server: %s", exc)

    if g_o is None:
        # Still report success from the calculation itself
        result['success'] = True
        result['error'] = 'Calculation ran but could not connect to Output for result extraction.'
        return result

    # Resolve output phases
    try:
        if fos_phase:
            o_fos = _find_phase_by_name(g_o, fos_phase)
            result['msf'] = _extract_msf(g_o, o_fos)

        if plate_obj and disp_phase:
            o_disp = _find_phase_by_name(g_o, disp_phase)
            # Find the plate in the Output model by name
            o_plate = _find_plate_by_name(g_o, plate_name)
            result['ux_max'] = _extract_max_ux(g_o, o_plate, o_disp)

        if plate_obj and cap_phase:
            o_cap = _find_phase_by_name(g_o, cap_phase)
            o_plate = o_plate if 'o_plate' in dir() else _find_plate_by_name(g_o, plate_name)
            result['m_max'] = _extract_max_moment(g_o, o_plate, o_cap)

        result['success'] = True
    except Exception as exc:
        result['error'] = f"Result extraction failed: {exc}"
        result['success'] = True  # calc succeeded, extraction partially failed

    return result
