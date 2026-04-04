"""
Polyline Utilities
==================
Functions for computing section heights from a pair of 3-D polylines
(wall top and wall bottom) at regular intervals.
"""
from __future__ import annotations

import math
from typing import List, Tuple

Point3D = Tuple[float, float, float]  # (x, y, z)


def _polyline_length(pts: list[Point3D]) -> float:
    """Total 2-D (plan) length of a polyline."""
    total = 0.0
    for i in range(1, len(pts)):
        dx = pts[i][0] - pts[i - 1][0]
        dy = pts[i][1] - pts[i - 1][1]
        total += math.hypot(dx, dy)
    return total


def _point_at_distance(pts: list[Point3D], dist: float) -> Point3D:
    """Interpolate a point along a polyline at a given 2-D arc-length distance."""
    accum = 0.0
    for i in range(1, len(pts)):
        dx = pts[i][0] - pts[i - 1][0]
        dy = pts[i][1] - pts[i - 1][1]
        seg_len = math.hypot(dx, dy)
        if seg_len == 0:
            continue
        if accum + seg_len >= dist - 1e-9:
            t = (dist - accum) / seg_len
            t = max(0.0, min(1.0, t))
            return (
                pts[i - 1][0] + t * dx,
                pts[i - 1][1] + t * dy,
                pts[i - 1][2] + t * (pts[i][2] - pts[i - 1][2]),
            )
        accum += seg_len
    return pts[-1]


def _closest_z_on_polyline(pts: list[Point3D], x: float, y: float) -> float:
    """Find z at the closest point on a polyline to (x, y) in plan view.

    Projects the query point onto each segment and picks the nearest.
    """
    best_dist = float("inf")
    best_z = pts[0][2]

    for i in range(1, len(pts)):
        ax, ay, az = pts[i - 1]
        bx, by, bz = pts[i]
        dx, dy = bx - ax, by - ay
        seg_len_sq = dx * dx + dy * dy
        if seg_len_sq == 0:
            d = math.hypot(x - ax, y - ay)
            if d < best_dist:
                best_dist = d
                best_z = az
            continue
        t = ((x - ax) * dx + (y - ay) * dy) / seg_len_sq
        t = max(0.0, min(1.0, t))
        px = ax + t * dx
        py = ay + t * dy
        pz = az + t * (bz - az)
        d = math.hypot(x - px, y - py)
        if d < best_dist:
            best_dist = d
            best_z = pz

    return best_z


def sections_from_polylines(
    top_pts: list[Point3D],
    bottom_pts: list[Point3D],
    interval: float,
) -> list[dict]:
    """Sample wall sections at *interval* spacing along the top polyline.

    For each sample point on the top polyline the height is computed as the
    vertical difference to the nearest point on the bottom polyline.

    Parameters
    ----------
    top_pts : list of (x, y, z)
        Wall-top polyline vertices.
    bottom_pts : list of (x, y, z)
        Wall-bottom (foundation) polyline vertices.
    interval : float
        Spacing between sections along the top polyline (metres).

    Returns
    -------
    list[dict]
        ``[{"station": 0.0, "height": 3.5, "top_z": 103.5, "bot_z": 100.0}, ...]``
    """
    total = _polyline_length(top_pts)
    if total <= 0 or interval <= 0:
        return []

    n_sections = int(total / interval) + 1
    results = []

    for i in range(n_sections):
        dist = min(i * interval, total)
        tx, ty, tz = _point_at_distance(top_pts, dist)
        bz = _closest_z_on_polyline(bottom_pts, tx, ty)
        height = max(0.0, tz - bz)
        results.append({
            "station": round(dist, 3),
            "height": round(height, 3),
            "top_z": round(tz, 3),
            "bot_z": round(bz, 3),
            "top_point": [round(tx, 4), round(ty, 4), round(tz, 4)],
            "bot_point": [round(tx, 4), round(ty, 4), round(bz, 4)],
        })

    return results
