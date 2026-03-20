# -*- coding: utf-8 -*-
"""
Level 5 — Structure and Phase Resolution
==========================================
Converts names from a job configuration dict into actual Plaxis Output
objects that can be passed to the extraction functions in level5_results.py.

These helpers are kept separate from level5_results.py so they can be
unit-tested without a live Plaxis connection (inject mock g_o).
"""

from typing import Any, Dict, List


# Map from job-config keys to Plaxis Output attribute names
_STRUCTURE_MAP: Dict[str, str] = {
    'plates':                'Plates',
    'embedded_beams':        'EmbeddedBeamRows',
    'node_to_node_anchors':  'NodeToNodeAnchors',
    'fixed_end_anchors':     'FixedEndAnchors',
    'geogrids':              'Geogrids',
}


def resolve_structures(g_o, job: Dict[str, Any]) -> dict:
    """
    Resolve structure names from a job config into live Plaxis Output objects.

    Args:
        g_o:  Plaxis Output geometry object.
        job:  Job configuration dict (must contain a 'structures' key).

    Returns:
        Dict mapping job structure keys to lists of Plaxis objects.
    """
    selected: dict = {}

    for job_key, plaxis_attr in _STRUCTURE_MAP.items():
        selected[job_key] = []
        selected_names: List[str] = job.get('structures', {}).get(job_key, [])

        if not selected_names:
            continue
        if not hasattr(g_o, plaxis_attr):
            continue

        plaxis_objects = getattr(g_o, plaxis_attr)
        for obj in plaxis_objects:
            if obj.Name.value in selected_names:
                selected[job_key].append(obj)

    return selected


def resolve_phases(g_o, phase_names: List[str]) -> list:
    """
    Resolve phase names to Plaxis Output phase objects.

    Matches by checking whether the Plaxis Identification string *starts with*
    the requested name, which handles the ``[Phase_N]`` suffix that Plaxis
    appends automatically.

    Example:
        Input:  'SLS Excavation'
        Output: phase with Identification 'SLS Excavation [Phase_3]'

    Args:
        g_o:          Plaxis Output geometry object.
        phase_names:  List of (partial) phase name strings.

    Returns:
        List of Plaxis phase objects in the order they were matched.
    """
    resolved = []
    for phase in g_o.Phases:
        phase_id = phase.Identification.value
        for target in phase_names:
            if phase_id.startswith(target):
                resolved.append(phase)
                break  # avoid duplicates per phase
    return resolved

