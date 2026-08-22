"""Slide-graph relation primitives: edge taxonomy and geometry helpers.

Dependency-light: stdlib only. All coordinates are normalized slide units
(node["bbox_norm"] = {"x","y","w","h"} with origin at top-left).
"""
from __future__ import annotations

EDGE_TYPES = [
    "LEFT_ALIGNED",
    "RIGHT_ALIGNED",
    "TOP_ALIGNED",
    "BOTTOM_ALIGNED",
    "NEAREST_HORIZONTAL",
    "NEAREST_VERTICAL",
    "SAME_GROUP",
    "CONTAINS",
    "OVERLAPS",
]

# Tolerance (normalized units) for alignment edges.
ALIGN_EPS = 0.005
# Minimum IoU for an OVERLAPS edge.
OVERLAP_IOU_MIN = 0.15
# Tolerance (normalized units) for geometric containment tests.
CONTAIN_TOL = 0.002


def bbox_of(node: dict | None):
    """Return (x, y, w, h) from node["bbox_norm"], or None if missing/incomplete."""
    if not isinstance(node, dict):
        return None
    b = node.get("bbox_norm")
    if not isinstance(b, dict):
        return None
    x, y, w, h = b.get("x"), b.get("y"), b.get("w"), b.get("h")
    if any(v is None for v in (x, y, w, h)):
        return None
    try:
        return (float(x), float(y), float(w), float(h))
    except (TypeError, ValueError):
        return None


def iou(a, b) -> float:
    """Intersection-over-union of two (x, y, w, h) boxes; 0.0 if either is None."""
    if a is None or b is None:
        return 0.0
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    ix = max(0.0, min(ax + aw, bx + bw) - max(ax, bx))
    iy = max(0.0, min(ay + ah, by + bh) - max(ay, by))
    inter = ix * iy
    union = aw * ah + bw * bh - inter
    return inter / union if union > 0 else 0.0


def contains_box(outer, inner, tol: float = CONTAIN_TOL) -> bool:
    """True when box `inner` lies inside box `outer` within tolerance `tol`."""
    if outer is None or inner is None:
        return False
    ox, oy, ow, oh = outer
    ix, iy, iw, ih = inner
    return (
        ix >= ox - tol
        and iy >= oy - tol
        and ix + iw <= ox + ow + tol
        and iy + ih <= oy + oh + tol
    )


def gap_between(a, b) -> float:
    """Axis-aligned bounding gap between two boxes: max(0, max(mins) - min(maxes))."""
    if a is None or b is None:
        return 0.0
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    gx = max(ax, bx) - min(ax + aw, bx + bw)
    gy = max(ay, by) - min(ay + ah, by + bh)
    return max(gx, gy)
