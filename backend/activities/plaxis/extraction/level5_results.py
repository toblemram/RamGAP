# -*- coding: utf-8 -*-
"""
Level 5 — Result Extraction Functions
======================================
Extracts structural forces, MSF safety factors, and displacements from
a connected Plaxis Output model. Handles differences between Plaxis
versions by probing the API at runtime.

Public API:
    run_capacity(g_o, selected_structures, phases)  -> dict
    run_msf(g_o, phases)                            -> dict
    run_displacement(g_o, selected_structures, phases, component) -> dict
"""

from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Version-safe helpers
# ---------------------------------------------------------------------------

def _get_first_existing(obj, candidates):
    """Return the first attribute from *candidates* that exists on *obj*."""
    for name in candidates:
        if hasattr(obj, name):
            return getattr(obj, name)
    return None


def _get_embedded_beam_group(g_o):
    """Return the correct EmbeddedBeam result-type group for this Plaxis version."""
    if hasattr(g_o.ResultTypes, 'EmbeddedBeamRow'):
        return g_o.ResultTypes.EmbeddedBeamRow
    if hasattr(g_o.ResultTypes, 'EmbeddedBeam'):
        return g_o.ResultTypes.EmbeddedBeam
    return None


def build_result_config(g_o) -> dict:
    """
    Build a mapping of structure-type → {location, result_types}
    that is compatible with the running Plaxis version.

    Tip: ``print(dir(g_o.ResultTypes))`` is useful when adding a new version.
    """
    config: Dict[str, Any] = {}

    if hasattr(g_o.ResultTypes, 'Plate'):
        plate = g_o.ResultTypes.Plate
        config['plates'] = {
            'location': 'node',
            'results': {
                'Nx':     _get_first_existing(plate, ['Nx2D', 'N',   'Nx']),
                'Q':      _get_first_existing(plate, ['Q2D',  'Q',   'Qx']),
                'M':      _get_first_existing(plate, ['M2D',  'M',   'Mx']),
                'Ux':     _get_first_existing(plate, ['Ux',   'Ux2D']),
                'Uy':     _get_first_existing(plate, ['Uy',   'Uy2D']),
                'Utotal': _get_first_existing(plate, ['Utot', 'Utotal', 'Utot2D']),
            },
        }

    embedded = _get_embedded_beam_group(g_o)
    if embedded:
        config['embedded_beams'] = {
            'location': 'node',
            'results': {
                'Nx':     _get_first_existing(embedded, ['Nx2D', 'N',   'Nx']),
                'Q':      _get_first_existing(embedded, ['Q2D',  'Q',   'Qx']),
                'M':      _get_first_existing(embedded, ['M2D',  'M',   'Mx']),
                'Ux':     _get_first_existing(embedded, ['Ux',   'Ux2D']),
                'Uy':     _get_first_existing(embedded, ['Uy',   'Uy2D']),
                'Utotal': _get_first_existing(embedded, ['Utot', 'Utotal', 'Utot2D']),
            },
        }

    if hasattr(g_o.ResultTypes, 'Geogrid'):
        geo = g_o.ResultTypes.Geogrid
        config['geogrids'] = {
            'location': 'node',
            'results': {
                'N':      _get_first_existing(geo, ['Nx2D', 'N', 'Nx']),
                'Nmax':   _get_first_existing(geo, ['NEnvelopeMax', 'NEnvelopeMax2D', 'NxEnvelopeMax2D']),
                'Ux':     _get_first_existing(geo, ['Ux', 'Ux2D']),
                'Uy':     _get_first_existing(geo, ['Uy', 'Uy2D']),
                'Utotal': _get_first_existing(geo, ['Utot', 'Utotal', 'Utot2D']),
            },
        }

    if hasattr(g_o.ResultTypes, 'NodeToNodeAnchor'):
        anc = g_o.ResultTypes.NodeToNodeAnchor
        config['node_to_node_anchors'] = {
            'location': 'node',
            'results': {
                'N':      _get_first_existing(anc, ['N', 'Nx', 'Nx2D']),
                'Nmax':   _get_first_existing(anc, ['NEnvelopeMax', 'NEnvelopeMax2D', 'NxEnvelopeMax2D']),
                'Ux':     _get_first_existing(anc, ['Ux', 'Ux2D']),
                'Uy':     _get_first_existing(anc, ['Uy', 'Uy2D']),
                'Utotal': _get_first_existing(anc, ['Utot', 'Utotal', 'Utot2D']),
            },
        }

    if hasattr(g_o.ResultTypes, 'FixedEndAnchor'):
        fea = g_o.ResultTypes.FixedEndAnchor
        config['fixed_end_anchors'] = {
            'location': 'node',
            'results': {
                'N':      _get_first_existing(fea, ['N', 'Nx', 'Nx2D']),
                'Nmax':   _get_first_existing(fea, ['NEnvelopeMax', 'NEnvelopeMax2D', 'NxEnvelopeMax2D']),
                'Ux':     _get_first_existing(fea, ['Ux', 'Ux2D']),
                'Uy':     _get_first_existing(fea, ['Uy', 'Uy2D']),
                'Utotal': _get_first_existing(fea, ['Utot', 'Utotal', 'Utot2D']),
            },
        }

    return config


# ---------------------------------------------------------------------------
# getresults() signature detection
# ---------------------------------------------------------------------------

def detect_getresults_signature(g_o, sample_obj, sample_phase, sample_result, location: str) -> str:
    """
    Detect which argument order g_o.getresults() expects in this Plaxis version.

    Returns one of: 'object_first' | 'object_last' | 'no_object'
    """
    for order in ('object_first', 'object_last', 'no_object'):
        try:
            _call_getresults(g_o, order, sample_obj, sample_phase, sample_result, location)
            return order
        except Exception:
            continue
    raise RuntimeError('Unsupported getresults() signature.')


def _call_getresults(g_o, signature: str, obj, phase, result_type, location):
    """Dispatch a single getresults() call using the detected signature."""
    if result_type is None:
        return None
    if signature == 'object_first':
        return g_o.getresults(obj, phase, result_type, location)
    if signature == 'object_last':
        return g_o.getresults(phase, result_type, location, obj)
    if signature == 'no_object':
        return g_o.getresults(phase, result_type, location)
    raise RuntimeError(f'Invalid getresults signature: {signature}')


# ---------------------------------------------------------------------------
# Public extraction functions
# ---------------------------------------------------------------------------

def run_capacity(g_o, selected_structures: dict, phases: list) -> dict:
    """
    Extract maximum absolute structural forces for each selected structure
    and phase.

    Returns:
        Nested dict: {struct_type: {obj_name: {phase_name: {force: value}}}}
    """
    results: dict = {}
    result_config = build_result_config(g_o)

    # Detect getresults() signature once using the first valid sample
    signature = None
    for struct_type, objects in selected_structures.items():
        if objects and struct_type in result_config:
            sample_result = next(
                (r for r in result_config[struct_type]['results'].values() if r), None
            )
            if sample_result:
                signature = detect_getresults_signature(
                    g_o, objects[0], phases[0], sample_result,
                    result_config[struct_type]['location']
                )
                break

    if signature is None:
        raise RuntimeError('Could not detect getresults() signature.')

    for struct_type, objects in selected_structures.items():
        if not objects or struct_type not in result_config:
            continue

        results[struct_type] = {}
        location     = result_config[struct_type]['location']
        result_types = result_config[struct_type]['results']

        for obj in objects:
            obj_name = obj.Name.value
            results[struct_type][obj_name] = {}

            for phase in phases:
                phase_name = phase.Identification.value
                results[struct_type][obj_name][phase_name] = {}

                for force_name, result_type in result_types.items():
                    try:
                        values = _call_getresults(g_o, signature, obj, phase, result_type, location)
                        max_force = max(abs(v) for v in values) if values else None
                    except Exception:
                        max_force = None
                    results[struct_type][obj_name][phase_name][force_name] = max_force

    return results


def _detect_msf_accessor(sample_phase):
    """
    Return a lambda that reads the final SumMsf value from a phase object,
    handling differences between Plaxis versions.
    """
    if hasattr(sample_phase, 'Reached'):
        reached = sample_phase.Reached
        if hasattr(reached, 'SumMsf'):
            return lambda p: p.Reached.SumMsf.value
        if hasattr(reached, 'MsfReached'):
            return lambda p: p.Reached.MsfReached.value
        if hasattr(reached, 'Msf'):
            return lambda p: p.Reached.Msf.value

    if hasattr(sample_phase, 'DeformCalcSafety'):
        safety = sample_phase.DeformCalcSafety
        if hasattr(safety, 'MsfReached'):
            return lambda p: p.DeformCalcSafety.MsfReached.value

    if hasattr(sample_phase, 'SafetyCalculation'):
        safety = sample_phase.SafetyCalculation
        if hasattr(safety, 'MsfReached'):
            return lambda p: p.SafetyCalculation.MsfReached.value

    raise RuntimeError('Could not locate MSF property in this PLAXIS version.')


def run_msf(g_o, phases: list) -> dict:
    """
    Extract the final SumMsf value for each safety-factor phase.

    Returns:
        {phase_name: msf_value}
    """
    if not phases:
        return {}

    msf_accessor = _detect_msf_accessor(phases[0])
    results = {}
    for phase in phases:
        try:
            results[phase.Identification.value] = msf_accessor(phase)
        except Exception:
            results[phase.Identification.value] = None
    return results


def run_displacement(g_o, selected_structures: dict, phases: list, component: str) -> dict:
    """
    Extract maximum absolute displacement for the given component
    (e.g. 'Ux', 'Uy', 'Utotal') per structure and phase.

    Returns:
        Nested dict: {struct_type: {obj_name: {phase_name: max_displacement}}}
    """
    results: dict = {}
    result_config = build_result_config(g_o)

    if not phases:
        return results

    # Detect signature
    signature = None
    for struct_type, objects in selected_structures.items():
        if objects and struct_type in result_config:
            result_type = result_config[struct_type]['results'].get(component)
            if result_type:
                signature = detect_getresults_signature(
                    g_o, objects[0], phases[0], result_type,
                    result_config[struct_type]['location']
                )
                break

    if signature is None:
        return results

    for struct_type, objects in selected_structures.items():
        if not objects or struct_type not in result_config:
            continue

        result_type = result_config[struct_type]['results'].get(component)
        if not result_type:
            continue

        location  = result_config[struct_type]['location']
        results[struct_type] = {}

        for obj in objects:
            obj_name = obj.Name.value
            results[struct_type][obj_name] = {}

            for phase in phases:
                phase_name = phase.Identification.value
                try:
                    values   = _call_getresults(g_o, signature, obj, phase, result_type, location)
                    max_disp = max(abs(v) for v in values) if values else None
                except Exception:
                    max_disp = None
                results[struct_type][obj_name][phase_name] = max_disp

    return results
