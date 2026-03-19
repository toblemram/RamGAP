# -*- coding: utf-8 -*-
"""
Shared Utilities
================
General-purpose helper functions used across multiple activities.
Add only truly reusable helpers here — activity-specific logic belongs
in the activity's own module.
"""

from datetime import datetime


def utcnow_iso() -> str:
    """Return the current UTC time as an ISO 8601 string."""
    return datetime.utcnow().isoformat()


def safe_int(value, default: int = 0) -> int:
    """Convert a value to int, returning a default on failure."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return default
