# -*- coding: utf-8 -*-
"""
Level 1 — Model Info Extraction
================================
Reads phase names and all structural element names from a connected
Plaxis Input model. Returns structured data used by the frontend to
populate selection dropdowns.

Requires an active g_i (Plaxis Input geometry) object.
"""

from typing import Dict, Any


def extract_model_info(g_i) -> Dict[str, Any]:
    """
    Extract all structures and phases from the open Plaxis model.

    Args:
        g_i: Plaxis Input geometry object from new_server().

    Returns:
        dict with 'structures' and 'phases' keys, ready for JSON serialisation.
    """
    structures = {
        'plates': [],
        'embedded_beams': [],
        'node_to_node_anchors': [],
        'fixed_end_anchors': [],
        'geogrids': [],
    }

    g_i.gotostructures()

    # Plates (sheet piles, walls)
    if hasattr(g_i, 'Plates'):
        for plate in g_i.Plates:
            structures['plates'].append({
                'name':         plate.Name.value,
                'display_name': f"Name: {plate.Name.value}, x = {plate.Parent.First.x.value}",
                'x':            plate.Parent.First.x.value,
                'type':         'plate',
            })

    # Embedded Beam Rows (piles, columns)
    if hasattr(g_i, 'EmbeddedBeamRows'):
        for ebr in g_i.EmbeddedBeamRows:
            structures['embedded_beams'].append({
                'name':         ebr.Name.value,
                'display_name': f"Name: {ebr.Name.value}, x = {ebr.Parent.First.x.value}",
                'x':            ebr.Parent.First.x.value,
                'type':         'embedded_beam',
            })

    # Node-to-Node Anchors
    if hasattr(g_i, 'NodeToNodeAnchors'):
        for n2n in g_i.NodeToNodeAnchors:
            x1 = n2n.Parent.First.x.value
            y1 = n2n.Parent.First.y.value
            x2 = n2n.Parent.Second.x.value
            y2 = n2n.Parent.Second.y.value
            structures['node_to_node_anchors'].append({
                'name':         n2n.Name.value,
                'display_name': f"Name: {n2n.Name.value}, ({x1},{y1}) \u2192 ({x2},{y2})",
                'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2,
                'type': 'node_to_node_anchor',
            })

    # Fixed-End Anchors
    if hasattr(g_i, 'FixedEndAnchors'):
        for fea in g_i.FixedEndAnchors:
            x = fea.Parent.x.value
            y = fea.Parent.y.value
            structures['fixed_end_anchors'].append({
                'name':         fea.Name.value,
                'display_name': f"Name: {fea.Name.value}, ({x},{y})",
                'x': x, 'y': y,
                'type': 'fixed_end_anchor',
            })

    # Geogrids
    if hasattr(g_i, 'Geogrids'):
        for geo in g_i.Geogrids:
            x1 = geo.Parent.First.x.value
            y1 = geo.Parent.First.y.value
            x2 = geo.Parent.Second.x.value
            y2 = geo.Parent.Second.y.value
            structures['geogrids'].append({
                'name':         geo.Name.value,
                'display_name': f"Name: {geo.Name.value}, ({x1},{y1}) \u2192 ({x2},{y2})",
                'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2,
                'type': 'geogrid',
            })

    # Phases
    g_i.gotostages()
    phase_names = g_i.Phases.Identification.value

    phases = [
        {'id': i, 'name': name, 'msf_enabled': False, 'ux_enabled': False, 'capacity_enabled': False}
        for i, name in enumerate(phase_names)
    ]

    return {'structures': structures, 'phases': phases}

