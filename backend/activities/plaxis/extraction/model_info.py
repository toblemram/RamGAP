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

# Map Plaxis DeformCalcType integer values to human-readable strings.
_CALC_TYPE_MAP = {
    0: 'Deformasjon',
    1: 'K0-prosedyre',
    2: 'Feltspenning',
    3: 'Gravitasjonslast',
    4: 'Plastisk',
    5: 'Konsolidering',
    6: 'Oppdatert mesh',
    7: 'Sikkerhet (phi/c-reduksjon)',
    8: 'Dynamisk',
    9: 'Fullt koblet strømning-deformasjon',
    10: 'Dynamisk med konsolidering',
}


def _safe(fn, default=None):
    """Call *fn* and return its result, or *default* on any exception."""
    try:
        return fn()
    except Exception:
        return default


def _extract_plate_material(plate) -> Dict[str, Any] | None:
    """Return material properties for a plate, or None."""
    try:
        m = plate.Material
        info: Dict[str, Any] = {'name': m.Identification.value}
        for prop in ('EA1', 'EA2', 'EI', 'd', 'w', 'nu', 'Mp', 'Np',
                     'MaterialType', 'PreventPunching'):
            val = _safe(lambda p=prop: getattr(m, p).value)
            if val is not None:
                info[prop] = val
        return info
    except Exception:
        return None


def _extract_anchor_material(anchor) -> Dict[str, Any] | None:
    """Return material properties for an anchor, or None."""
    try:
        m = anchor.Material
        info: Dict[str, Any] = {'name': m.Identification.value}
        for prop in ('EA', 'Lspacing', 'MaterialType'):
            val = _safe(lambda p=prop: getattr(m, p).value)
            if val is not None:
                info[prop] = val
        return info
    except Exception:
        return None


def extract_model_info(g_i) -> Dict[str, Any]:
    """
    Extract all structures and phases from the open Plaxis model.

    Args:
        g_i: Plaxis Input geometry object from new_server().

    Returns:
        dict with 'structures', 'phases' and 'geometry' keys,
        ready for JSON serialisation.
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
            x1 = plate.Parent.First.x.value
            y1 = plate.Parent.First.y.value
            x2 = plate.Parent.Second.x.value
            y2 = plate.Parent.Second.y.value
            length = ((x2 - x1)**2 + (y2 - y1)**2)**0.5
            entry: Dict[str, Any] = {
                'name':         plate.Name.value,
                'display_name': f"Name: {plate.Name.value}, x = {x1}",
                'x':            x1,
                'type':         'plate',
                'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2,
                'length':       round(length, 2),
            }
            mat = _extract_plate_material(plate)
            if mat:
                entry['material'] = mat
            structures['plates'].append(entry)

    # Embedded Beam Rows (piles, columns)
    if hasattr(g_i, 'EmbeddedBeamRows'):
        for ebr in g_i.EmbeddedBeamRows:
            x1 = ebr.Parent.First.x.value
            y1 = ebr.Parent.First.y.value
            x2 = ebr.Parent.Second.x.value
            y2 = ebr.Parent.Second.y.value
            length = ((x2 - x1)**2 + (y2 - y1)**2)**0.5
            entry = {
                'name':         ebr.Name.value,
                'display_name': f"Name: {ebr.Name.value}, x = {x1}",
                'x':            x1,
                'type':         'embedded_beam',
                'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2,
                'length':       round(length, 2),
            }
            structures['embedded_beams'].append(entry)

    # Node-to-Node Anchors
    if hasattr(g_i, 'NodeToNodeAnchors'):
        for n2n in g_i.NodeToNodeAnchors:
            x1 = n2n.Parent.First.x.value
            y1 = n2n.Parent.First.y.value
            x2 = n2n.Parent.Second.x.value
            y2 = n2n.Parent.Second.y.value
            length = ((x2 - x1)**2 + (y2 - y1)**2)**0.5
            entry = {
                'name':         n2n.Name.value,
                'display_name': f"Name: {n2n.Name.value}, ({x1},{y1}) \u2192 ({x2},{y2})",
                'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2,
                'type': 'node_to_node_anchor',
                'length': round(length, 2),
            }
            mat = _extract_anchor_material(n2n)
            if mat:
                entry['material'] = mat
            structures['node_to_node_anchors'].append(entry)

    # Fixed-End Anchors
    if hasattr(g_i, 'FixedEndAnchors'):
        for fea in g_i.FixedEndAnchors:
            x = fea.Parent.x.value
            y = fea.Parent.y.value
            entry = {
                'name':         fea.Name.value,
                'display_name': f"Name: {fea.Name.value}, ({x},{y})",
                'x': x, 'y': y,
                'type': 'fixed_end_anchor',
            }
            mat = _extract_anchor_material(fea)
            if mat:
                entry['material'] = mat
            structures['fixed_end_anchors'].append(entry)

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
    phases = []
    for i, phase in enumerate(g_i.Phases):
        calc_type_num = _safe(lambda: phase.DeformCalcType.value, 0)
        calc_type_str = _CALC_TYPE_MAP.get(calc_type_num, f'Ukjent ({calc_type_num})')

        prev_name = None
        try:
            if phase.PreviousPhase:
                prev_name = phase.PreviousPhase.Identification.value
        except Exception:
            pass

        phases.append({
            'id':           i,
            'number':       _safe(lambda: phase.Number.value, i),
            'name':         phase.Identification.value,
            'calc_type':    calc_type_str,
            'calc_type_id': calc_type_num,
            'previous':     prev_name,
            'msf_enabled':  False,
            'ux_enabled':   False,
            'capacity_enabled': False,
        })

    # Geometry overview  (soil layers, water, model extents)
    geometry: Dict[str, Any] = {}

    # --- Soil layers with material names ---
    try:
        g_i.gotosoil()
        layers = []
        for sl in g_i.SoilLayers:
            top_v = sl.Top.value
            bot_v = sl.Bottom.value
            top = top_v[0] if isinstance(top_v, list) else top_v
            bot = bot_v[0] if isinstance(bot_v, list) else bot_v
            layers.append({
                'name': sl.Name.value,
                'top': top,
                'bottom': bot,
            })
        geometry['soil_layers'] = layers

        # Assign material name to each layer from phase-0 material assignment.
        # g_i.Soils follows the naming Soil_<layer>_<polygon>; the first digit
        # after the underscore identifies the layer index (1-based).
        try:
            g_i.gotostages()
            soil_mat_by_layer: Dict[int, str] = {}
            init_phase = g_i.InitialPhase
            for soil in g_i.Soils:
                soil_name = soil.Name.value  # e.g. "Soil_3_2"
                parts = soil_name.split('_')
                if len(parts) >= 2:
                    try:
                        layer_idx = int(parts[1]) - 1  # 0-based
                    except ValueError:
                        continue
                    if layer_idx not in soil_mat_by_layer:
                        mat = soil.Material[init_phase]
                        soil_mat_by_layer[layer_idx] = mat.Identification.value
            for idx, mat_name in soil_mat_by_layer.items():
                if idx < len(layers):
                    layers[idx]['material'] = mat_name
        except Exception:
            pass

        # Boreholes
        g_i.gotosoil()
        bh_count = _safe(lambda: len(g_i.Boreholes), 0)
        geometry['boreholes'] = bh_count

        # Water head
        try:
            for bh in g_i.Boreholes:
                head = _safe(lambda: bh.Head.value)
                if head is not None:
                    geometry['water_head'] = head
                    break
        except Exception:
            pass
    except Exception:
        pass

    # --- Model extents ---
    try:
        g_i.gotostructures()
        pts = [(p.x.value, p.y.value) for p in g_i.Points]
        if pts:
            xs = [p[0] for p in pts]
            ys = [p[1] for p in pts]
            geometry['xmin'] = min(xs)
            geometry['xmax'] = max(xs)
            geometry['ymin'] = min(ys)
            geometry['ymax'] = max(ys)
    except Exception:
        pass

    # --- Lines (for cross-section drawing) ---
    try:
        g_i.gotostructures()
        lines = []
        for line in g_i.Lines:
            lines.append({
                'x1': line.First.x.value,
                'y1': line.First.y.value,
                'x2': line.Second.x.value,
                'y2': line.Second.y.value,
            })
        geometry['lines'] = lines
    except Exception:
        pass

    return {'structures': structures, 'phases': phases, 'geometry': geometry}

