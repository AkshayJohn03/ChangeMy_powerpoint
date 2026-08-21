"""Node features v2: V1 base + effective typography + relational context."""
from __future__ import annotations

import math

from ..ast import extractor
from .node_features import (
    FEATURE_NAMES as V1_NAMES,
    _bbox,
    _dominant_size,
    extract_slide_node_features,
)

FEATURE_SCHEMA_VERSION = "2.0.0"

RELATIONAL_NAMES = [
    "nn3_mean",
    "align_x_resid",
    "align_y_resid",
    "overlap_frac_max",
    "same_type_frac",
    "grid_occupancy",
]

EFFECTIVE_NAMES = [
    "eff_size_pt",
    "eff_rel_max",
    "eff_rel_median",
    "eff_is_largest",
    "eff_conf_mean",
    "eff_family_theme",
    "eff_family_run",
    "eff_color_present",
]

FEATURE_NAMES_V2 = V1_NAMES + RELATIONAL_NAMES + EFFECTIVE_NAMES


def _centroid(node: dict):
    b = node.get("bbox_norm") or {}
    if any(b.get(k) is None for k in ("x", "y", "w", "h")):
        return None
    return (b["x"] + b["w"] / 2, b["y"] + b["h"] / 2)


def _iou(a, b) -> float:
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    if None in (ax, ay, aw, ah, bx, by, bw, bh):
        return 0.0
    ix = max(0.0, min(ax + aw, bx + bw) - max(ax, bx))
    iy = max(0.0, min(ay + ah, by + bh) - max(ay, by))
    inter = ix * iy
    union = aw * ah + bw * bh - inter
    return inter / union if union > 0 else 0.0


def extract_slide_node_features_v2(slide: dict) -> list[dict]:
    nodes = slide.get("nodes") or []
    feats_v1 = extract_slide_node_features(nodes)
    flat = extractor.flatten_nodes(nodes)
    n = len(flat)
    if n != len(feats_v1):
        return feats_v1

    cents = [_centroid(nd) for nd in flat]
    boxes = []
    for nd in flat:
        b = nd.get("bbox_norm") or {}
        boxes.append((b.get("x"), b.get("y"), b.get("w"), b.get("h")))

    eff_max = ((slide.get("eff_context") or {}).get("eff_max_size")) or None
    eff_med = ((slide.get("eff_context") or {}).get("eff_median_size")) or None

    out = []
    for i in range(n):
        f = dict(feats_v1[i])
        ci = cents[i]

        dists = sorted(
            (math.hypot(ci[0] - cj[0], ci[1] - cj[1]), j)
            for j, cj in enumerate(cents) if j != i and cj is not None and ci is not None
        )
        f["nn3_mean"] = round(sum(d for d, _ in dists[:3]) / min(len(dists), 3), 4) if dists else 9.9

        ax = ay = 1.0
        for j, cj in enumerate(cents):
            if j == i or cj is None or ci is None:
                continue
            dx = abs(ci[0] - cj[0])
            dy = abs(ci[1] - cj[1])
            if dx > 0.05:
                ay = min(ay, dy)
            if dy > 0.03:
                ax = min(ax, dx)
        f["align_x_resid"] = round(min(ax, 1.0), 4)
        f["align_y_resid"] = round(min(ay, 1.0), 4)

        ov = 0.0
        neigh_types_same = neigh_total = 0
        for j, cj in enumerate(cents):
            if j == i:
                continue
            ov = max(ov, _iou(boxes[i], boxes[j]))
            if ci is not None and cj is not None and math.hypot(ci[0] - cj[0], ci[1] - cj[1]) <= 0.15:
                neigh_total += 1
                if flat[j]["type"] == flat[i]["type"]:
                    neigh_types_same += 1
        f["overlap_frac_max"] = round(ov, 4)
        f["same_type_frac"] = round(neigh_types_same / neigh_total, 4) if neigh_total else 0.0

        gx = gy = -1
        if None not in boxes[i]:
            gx = min(int((boxes[i][0] or 0) * 8), 7)
            gy = min(int((boxes[i][1] or 0) * 8), 7)
        occ = sum(
            1
            for k, b in enumerate(boxes)
            if k != i and b[0] is not None and min(int((b[0] or 0) * 8), 7) == gx and min(int((b[1] or 0) * 8), 7) == gy
        )
        f["grid_occupancy"] = round(min(occ, 10) / 10.0, 4)

        eff = nd.get("effective") or {}
        size = (eff.get("font_size_pt") or {}).get("value")
        fam = (eff.get("font_family") or {})
        confs = [
            v.get("confidence")
            for k, v in eff.items()
            if isinstance(v, dict) and isinstance(v.get("confidence"), (int, float))
        ]
        f["eff_size_pt"] = float(size) if isinstance(size, (int, float)) else 0.0
        f["eff_rel_max"] = round(size / eff_max, 4) if size and eff_max else 0.0
        f["eff_rel_median"] = round(size / eff_med, 4) if size and eff_med else 0.0
        f["eff_is_largest"] = int(bool(size and eff_max and size >= eff_max))
        f["eff_conf_mean"] = round(sum(confs) / len(confs), 4) if confs else 0.0
        f["eff_family_theme"] = int(fam.get("origin") == "theme")
        f["eff_family_run"] = int(fam.get("origin") == "run")
        f["eff_color_present"] = int(bool((eff.get("color") or {}).get("value")))

        out.append(f)
    return out


def node_ids_of_slide(nodes: list[dict]) -> list[str]:
    return [nd["id"] for nd in extractor.flatten_nodes(nodes)]
