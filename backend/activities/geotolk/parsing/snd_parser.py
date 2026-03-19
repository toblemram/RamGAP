# -*- coding: utf-8 -*-
"""
SND Parser for GeoTolk
Parser for SND-tekstfiler med støtte for spyling- og slag-segmenter.
Kopiert fra TolkBoss.
"""
from __future__ import annotations

from typing import List, Dict, Tuple
import re
import math

__all__ = ["find_snd_data_start", "parse_snd_text", "parse_snd_file", "parse_snd_with_events"]


def _looks_like_data_line(line: str) -> bool:
    """
    Check if a line looks like SND measurement data.
    
    SND data lines typically:
    - Start with whitespace followed by a depth value (small decimal)
    - OR start directly with a small decimal depth value (0.xxx)
    - Have at least 2-3 numeric columns
    """
    stripped = line.strip()
    if not stripped:
        return False
    
    # Extract numbers from the line
    flt = re.compile(r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?")
    nums = flt.findall(stripped)
    
    if len(nums) < 2:
        return False
    
    # Check if first number looks like a depth value
    # Depth values are typically small decimals (0.0 to ~100.0)
    try:
        first_num = float(nums[0])
        # Depth should be positive and reasonable (up to ~200m)
        if first_num < 0 or first_num > 500:
            return False
        
        # Data lines typically start with whitespace or a small decimal
        # Header/metadata lines often start with larger integers like dates (25, 1.000000)
        # If line starts with whitespace, it's likely data
        if line[0].isspace():
            return True
        
        # If first number is a small decimal (like 0.025), it's likely depth
        if first_num < 1.0 and '.' in nums[0]:
            return True
        
        # If line starts directly with a number > 1, check if it could be metadata
        # Metadata often has patterns like "25 11.11.2015" or "1.000000 94 0 5 0"
        # Data has patterns like "0.025 2846 55 79"
        if first_num >= 1.0:
            # Check second number - in data it's usually a larger measurement value
            if len(nums) >= 2:
                second_num = float(nums[1])
                # If second number is much larger than first, might be metadata date
                # In actual data, depths increase gradually
                if first_num < 10 and second_num > 1000:
                    return False  # Looks like "depth resistance" pattern but might be metadata
            return first_num < 50  # Allow reasonable depth values up to 50m for direct start
            
    except (ValueError, IndexError):
        return False
    
    return False


def find_snd_data_start(lines: List[str]) -> int:
    """
    Find the start of data in SND file.
    
    Strategy:
    1. Try standard format: After 4th '*' line + 3 lines (only in header area)
    2. Try alternative: After line containing specific markers
    3. Fallback: Find first line that looks like data after header
    
    Returns line index or -1 if not found.
    """
    # First pass: Find all asterisk positions
    asterisk_positions = []
    for i, ln in enumerate(lines):
        if ln.strip() == '*':  # Exact match, not just startswith
            asterisk_positions.append(i)
    
    # Strategy 1: Standard format with 4 asterisk header lines
    # But only consider asterisks in the first part of the file (header area)
    # Header area is typically first 30 lines or before line 50
    header_asterisks = [pos for pos in asterisk_positions if pos < 50]
    
    if len(header_asterisks) >= 4:
        # Use 4th asterisk in header area
        fourth_star = header_asterisks[3]
        j = fourth_star + 3
        if j < len(lines):
            return j
    
    # Strategy 2: For files with 3 asterisks in header, data starts after metadata lines
    # Typically: 3rd asterisk, date line, info line, then data
    if len(header_asterisks) >= 3:
        third_star = header_asterisks[2]
        # Look for first data line after 3rd asterisk
        for i in range(third_star + 1, min(third_star + 10, len(lines))):
            if _looks_like_data_line(lines[i]):
                # Verify it's actually data by checking indentation
                if lines[i][0].isspace():
                    return i
    
    # Strategy 3: Look for common SND header end markers
    for i, ln in enumerate(lines):
        lower = ln.strip().lower()
        if lower in ('data', 'data:', 'måledata', 'måledata:'):
            if i + 1 < len(lines):
                return i + 1
    
    # Strategy 4: Find first indented data line after header area
    search_start = header_asterisks[-1] + 1 if header_asterisks else 0
    for i in range(search_start, len(lines)):
        ln = lines[i]
        if ln and ln[0].isspace() and _looks_like_data_line(ln):
            return i
    
    return -1


def _extract_floats(line: str) -> List[float]:
    """Extract all float numbers from a line"""
    flt = re.compile(r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?")
    return [float(x) for x in flt.findall(line)]


def parse_snd_text(text: str) -> Dict[str, any]:
    """
    Parse SND text and return depth/resistance/other columns.
    
    Returns:
        Dict with keys: depth, c2, c3, c4, max_depth
    """
    lines = text.splitlines()
    
    if not lines:
        raise ValueError("SND-filen er tom.")
    
    start = find_snd_data_start(lines)
    if start < 0:
        # Count asterisks for better error message
        star_count = sum(1 for ln in lines if ln.strip().startswith('*'))
        preview = '\n'.join(lines[:min(10, len(lines))])
        raise ValueError(
            f"Fant ikke datastart i SND-fil. "
            f"Fant {star_count} asterisk-linjer (forventer 4). "
            f"Første linjer:\n{preview}"
        )

    depth: List[float] = []
    c2: List[float] = []
    c3: List[float] = []
    c4: List[float] = []

    for ln in lines[start:]:
        if not ln.strip():
            continue
        nums = _extract_floats(ln)
        if len(nums) >= 2:
            depth.append(nums[0])
            c2.append(nums[1])
            c3.append(nums[2] if len(nums) >= 3 else math.nan)
            c4.append(nums[3] if len(nums) >= 4 else math.nan)

    if not depth:
        raise ValueError("Fant ingen datalinjer i SND-fil.")

    return {
        "depth": depth,
        "c2": c2,
        "c3": c3,
        "c4": c4,
        "max_depth": max(depth),
    }


def parse_snd_with_events(text: str) -> Dict:
    """
    Parse SND text including spyling/slag events.
    
    Event codes:
    - 72/Y1: Spyling start
    - 73/Y2: Spyling end
    - 74/S1: Slag start
    - 75/S2: Slag end
    
    Returns:
        Dict with keys: depth, c2, c3, c4, max_depth, spyling, slag
    """
    lines = text.splitlines()
    
    if not lines:
        raise ValueError("SND-filen er tom.")
    
    start = find_snd_data_start(lines)
    if start < 0:
        # Count asterisks for better error message
        star_count = sum(1 for ln in lines if ln.strip().startswith('*'))
        preview = '\n'.join(lines[:min(10, len(lines))])
        raise ValueError(
            f"Fant ikke datastart i SND-fil. "
            f"Fant {star_count} asterisk-linjer (forventer 4). "
            f"Første linjer:\n{preview}"
        )

    depth, c2, c3, c4 = [], [], [], []
    events: List[Tuple[float, int]] = []

    for ln in lines[start:]:
        if not ln.strip():
            continue
        parts = ln.split()
        try:
            d = float(parts[0])
            r = float(parts[1])
        except Exception:
            continue

        depth.append(d)
        c2.append(r)
        c3.append(float(parts[2]) if len(parts) >= 3 else math.nan)
        c4.append(float(parts[3]) if len(parts) >= 4 else math.nan)

        # Check for event codes
        for tok in parts[2:]:
            t = tok.strip().rstrip(",.;")
            if not t:
                continue
            if t.isdigit():
                n = int(t)
                if n in (72, 73, 74, 75):
                    events.append((d, n))
            else:
                u = t.upper()
                if u == "Y1":
                    events.append((d, 72))
                elif u == "Y2":
                    events.append((d, 73))
                elif u == "S1":
                    events.append((d, 74))
                elif u == "S2":
                    events.append((d, 75))

    if not depth:
        raise ValueError("Fant ingen datalinjer i SND-fil.")

    max_depth = max(depth) if depth else 0.0

    # Build spyling and slag intervals
    spyling, slag = [], []
    spy_on, slag_on = False, False
    spy_start, slag_start = 0.0, 0.0

    for d, code in sorted(events, key=lambda x: x[0]):
        if code == 72 and not spy_on:
            spy_on, spy_start = True, d
        elif code == 73 and spy_on:
            if d > spy_start:
                spyling.append((spy_start, d))
            spy_on = False
        elif code == 74 and not slag_on:
            slag_on, slag_start = True, d
        elif code == 75 and slag_on:
            if d > slag_start:
                slag.append((slag_start, d))
            slag_on = False

    # Close any open intervals
    if spy_on and max_depth > spy_start:
        spyling.append((spy_start, max_depth))
    if slag_on and max_depth > slag_start:
        slag.append((slag_start, max_depth))

    return {
        "depth": depth,
        "c2": c2,
        "c3": c3,
        "c4": c4,
        "max_depth": max_depth,
        "spyling": spyling,
        "slag": slag,
    }


def parse_snd_file(path: str) -> Dict[str, any]:
    """Parse SND file from path"""
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        text = f.read()
    return parse_snd_text(text)
