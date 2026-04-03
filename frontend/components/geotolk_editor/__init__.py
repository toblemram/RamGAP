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
    elevation: float | None = None,
    elev_range: list | None = None,
    show_y_axis: bool = True,
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
        Available material types.
    colors : dict[str, str]
        Hex colour per material type.
    elevation : float | None
        Terrain elevation (kvote) of this borehole. When set, switches
        the Y-axis to elevation mode so boreholes at different heights
        are visually offset.
    elev_range : list | None
        Shared ``[min_elev, max_elev]`` for the entire profile.
        All editors on the same profile should receive the same range.
    show_y_axis : bool
        Whether to draw the Y-axis labels (set False for non-leftmost
        editors in a multi-column layout).
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
        elevation=elevation,
        elev_range=elev_range,
        show_y_axis=show_y_axis,
        key=key,
        default=layers,
    )
    return result
