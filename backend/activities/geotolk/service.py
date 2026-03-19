# -*- coding: utf-8 -*-
"""
GeoTolk Service
===============
Business logic for geotechnical data operations: file parsing,
layer interpretation, and producing output for the frontend.

This is the single point of contact for the routes layer.
"""

from activities.geotolk.parsing.snd_parser import parse_snd_file, parse_snd_with_events  # noqa: F401


class GeoTolkService:
    """Coordinates parsing and interpretation of geotechnical files."""

    def parse_file(self, filename: str, content: str) -> dict:
        """
        Parse a geotechnical file and return structured data.

        Args:
            filename: Original file name (used to detect format).
            content:  Raw text content of the file.

        Returns:
            dict with 'format', 'records', and 'metadata' keys.
        """
        ext = filename.rsplit(".", 1)[-1].upper()
        if ext == "SND":
            records = parse_snd_file(content)
            return {"format": "SND", "records": records}
        raise ValueError(f"Unsupported file format: {ext}")
