# -*- coding: utf-8 -*-
"""
Plaxis Data Models
==================
Pydantic / dataclass schemas used for validating API request/response bodies
specific to the Plaxis activity.

ORM models (SQLAlchemy) live in core/models.py.
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class StructureSelection:
    """Specifies which structural elements to include in an extraction job."""
    plates: List[str] = field(default_factory=list)
    fixed_end_anchors: List[str] = field(default_factory=list)
    node_to_node_anchors: List[str] = field(default_factory=list)
    embedded_beams: List[str] = field(default_factory=list)
    geogrids: List[str] = field(default_factory=list)


@dataclass
class ExtractionJob:
    """Full specification for a Plaxis result extraction job."""
    structures: StructureSelection = field(default_factory=StructureSelection)
    phases: List[str] = field(default_factory=list)
    output_path: str = ""
