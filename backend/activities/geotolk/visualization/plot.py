# -*- coding: utf-8 -*-
"""
GeoTolk Plotting
================
Creates depth-profile plots from parsed SND/TOT data.
Returns Plotly Figure objects suitable for rendering in Streamlit
or exporting as images.
"""

from typing import List


def depth_profile_figure(records: List[dict]):
    """
    Build a Plotly depth-vs-resistance figure.

    Args:
        records: List of dicts with at least 'depth' and 'resistance' keys.

    Returns:
        plotly.graph_objects.Figure
    """
    # TODO: implement
    raise NotImplementedError
