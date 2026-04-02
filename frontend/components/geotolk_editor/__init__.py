# -*- coding: utf-8 -*-
"""
GeoTolk Layer Editor — Custom Streamlit Component
==================================================
Interactive Canvas-based editor for assigning soil layers
to SND sounding data. Boundaries are dragged with the mouse.
"""

from pathlib import Path
import streamlit.components.v1 as components

_COMPONENT_DIR = Path(__file__).parent
_component_func = components.declare_component("geotolk_editor", path=str(_COMPONENT_DIR))


def geotolk_editor(
    sounding_data: dict,
    layers: list,
    max_depth: float,
    materials: list,
    colors: dict,
    key: str | None = None,
) -> list:
    """Render an interactive layer editor and return updated layers.

    Parameters
    ----------
    sounding_data : dict
        Parsed SND data with keys: depth, c2, spyling, slag, max_depth.
    layers : list[dict]
        Current layers, each ``{"type": str, "start": float, "end": float}``.
    max_depth : float
        Maximum borehole depth in metres.
    materials : list[str]
        Available material types (e.g. ``["leire", "sand", "fjell", "annet"]``).
    colors : dict[str, str]
        Hex colour per material type.
    key : str | None
        Streamlit widget key.

    Returns
    -------
    list[dict]
        The (possibly updated) layer list.
    """
    result = _component_func(
        sounding_data=sounding_data,
        layers=layers,
        max_depth=max_depth,
        materials=materials,
        colors=colors,
        key=key,
        default=layers,
    )
    return result
