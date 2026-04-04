"""Live slider Streamlit custom component."""

import math
import os

import streamlit.components.v1 as st_components

_LIVE_SLIDER_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "live_slider")
_live_slider_func = st_components.declare_component("live_slider", path=_LIVE_SLIDER_DIR)


def live_slider(
    label: str, min_value: float, max_value: float, value: float,
    step: float = 0.01, key: str | None = None,
) -> float:
    decimals = max(0, -int(math.floor(math.log10(abs(step))))) if step > 0 else 2
    val = _live_slider_func(
        label=label, min=float(min_value), max=float(max_value),
        value=float(value), step=float(step), decimals=decimals,
        key=key, default=float(value),
    )
    return float(val) if val is not None else value
