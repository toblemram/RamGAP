# -*- coding: utf-8 -*-
"""
GeoTolk Data Models
===================
Dataclass schemas for request/response bodies specific to the GeoTolk activity.

ORM models (SQLAlchemy) live in core/models.py.
"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class SndRecord:
    """Represents a single depth measurement from an SND file."""
    depth: float
    resistance: float
    flush: Optional[float] = None
    blow_count: Optional[float] = None


@dataclass
class ParsedFile:
    """The result of parsing a geotechnical field file."""
    filename: str
    format: str
    records: List[SndRecord] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
