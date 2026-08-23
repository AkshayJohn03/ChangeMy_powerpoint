"""Phase 9A slide-context representation layer (frozen contract implementation).

Source-side only: computes the 45-feature SlideContext vector from propagation
cache `base` dicts and `nbrs` edge lists. Never touches labels, transformation
records, or any target-deck data.

Groups: G1 global-slide (11) | G2 relative-node (11) | G3 spatial-distribution (13)
        | G4 structural (10). Integrator reconciliations documented in
        research/PHASE_9_EXPERIMENT_CONTRACT.md: `centrality_score` dropped
        (exact complement of dist_centroid_norm); G3 marginals flattened to 13.
"""
from __future__ import annotations

import math
import statistics

import numpy as np

SCHEMA_VERSION = "slide_ctx_v1"
TOL_BAND = 0.02
COLOC_R = 0.15
NN_CAP = 5.0
IOU_MIN = 0.05

G1 = [
    "n_xbands_log1p", "n_ybands_log1p", "band_size_entropy_x", "band_size_entropy_y",
    "grid_regularity_score", "quad_occupied_count", "content_quad_balance",
    "coloc_text_image", "title_zone_frac", "margin_symmetry_h",
    "contain_depth_weighted_mean_slide",
]
G2 = [
    "rel_x_med", "rel_y_med", "width_ratio_content", "height_ratio_content",
    "st_rank_x", "st_rank_y", "dist_nearest_text", "dist_nearest_image",
    "dist_centroid_norm", "isolation_index", "edge_margin_min",
]
G3 = [
    "occ_row_frac_0", "occ_row_frac_1", "occ_row_frac_2", "occ_row_frac_3",
    "occ_col_frac_0", "occ_col_frac_1", "occ_col_frac_2", "occ_col_frac_3",
    "corner_mass", "radial_mean", "radial_gini", "ring_inner_frac",
    "edge_margin_mean_slide",
]
G4 = [
    "overlap_deg_mean_slide", "overlap_deg_max_node",
    "contain_depth_d0_frac", "contain_depth_d1_frac", "contain_depth_deep_frac",
    "band_member_frac", "largest_band_frac", "group_edge_frac",
    "align_degree", "nn_same_type_ratio",
]
FEATURE_NAMES = G1 + G2 + G3 + G4
MUST_HAVE = {
    "rel_x_med", "rel_y_med", "st_rank_y", "dist_nearest_text", "isolation_index",
    "n_xbands_log1p", "n_ybands_log1p", "grid_regularity_score",
    "quad_occupied_count", "overlap_deg_mean_slide", "contain_depth_d0_frac",
}


def _type_key(b: dict) -> str:
    for k, name in (("is_text", "TEXT"), ("is_image", "IMAGE"), ("is_table", "TABLE"),
                    ("is_chart", "CHART"), ("is_line", "LINE"), ("is_group", "GROUP"),
                    ("is_arrow", "ARROW"), ("is_shape", "SHAPE")):
        if b.get(k):
            return name
    return "OTHER"


def _mean(v):
    v = list(v)
    return float(np.mean(v)) if v else 0.0


def _median(v):
    return float(statistics.median(v)) if v else 0.0


def _bands(vals):
    s = sorted(vals)
    bands = [[s[0]]]
    for v in s[1:]:
        if v - bands[-1][-1] <= TOL_BAND:
            bands[-1].append(v)
        else:
            bands.append([v])
    return bands


def _entropy_norm(sizes):
    n = sum(sizes)
    if n <= 1:
        return 0.0
    h = -sum((c / n) * math.log2(c / n) for c in sizes if c)
    return round(h / math.log2(n), 6)


def _gini(vals):
    vals = np.asarray(vals, dtype=float)
    if len(vals) == 0 or vals.sum() <= 0:
        return 0.0
    sv = np.sort(vals)
    cum = np.cumsum(sv)
    return round(float((len(sv) + 1 - 2 * (cum / cum[-1]).sum()) / len(sv)), 6)


def _box(b):
    x, y, w, h = (float(b.get(k) or 0.0) for k in ("x", "y", "w", "h"))
    return (x, y, max(w, 0.0), max(h, 0.0))


def _iou(a, b):
    ix = max(0.0, min(a[0] + a[2], b[0] + b[2]) - max(a[0], b[0]))
    iy = max(0.0, min(a[1] + a[3], b[1] + b[3]) - max(a[1], b[1]))
    inter = ix * iy
    union = a[2] * a[3] + b[2] * b[3] - inter
    return inter / union if union > 1e-9 else 0.0


def compute_slide_broadcast(members):
    """members: list[(row_index, row_dict)]. Returns (broadcast_dict, per_node_list)."""
    idxs = [i for i, _r in members]
    bases = [r["base"] for _i, r in members]
    nbr_sets = [r.get("nbrs") or {} for _i, r in members]
    n = len(bases)

    cxs = [float(b.get("cx") or 0.0) for b in bases]
    cys = [float(b.get("cy") or 0.0) for b in bases]
    boxes = [_box(b) for b in bases]
    depths = [int(float(b.get("container_depth") or 0)) for b in bases]
    xs = [b[0] for b in boxes]
    ys = [b[1] for b in boxes]
    xr = [b[0] + b[2] for b in boxes]
    yr = [b[1] + b[3] for b in boxes]
    type_keys = [_type_key(b) for b in bases]
    is_text = [bool(b.get("is_text")) for b in bases]
    is_image = [bool(b.get("is_image")) for b in bases]

    bx = _bands(cxs)
    by = _bands(cys)
    lines_x = [sum(bd) / len(bd) for bd in bx]
    lines_y = [sum(bd) / len(bd) for bd in by]
    on_rail = sum(
        1
        for i in range(n)
        if any(abs(cxs[i] - lx) <= TOL_BAND for lx in lines_x)
        or any(abs(cys[i] - ly) <= TOL_BAND for ly in lines_y)
    )

    text_pts = [(cxs[i], cys[i]) for i in range(n) if is_text[i]]
    img_pts = [(cxs[i], cys[i]) for i in range(n) if is_image[i]]
    coloc = sum(
        1
        for icx, icy in img_pts
        if any(math.hypot(icx - tx, icy - ty) <= COLOC_R for tx, ty in text_pts)
    )
    title_zone = sum(
        1 for i in range(n) if is_text[i] and ys[i] < 0.2 and boxes[i][2] > 0.3
    )

    content_w = max(max(xr), 1e-6) - min(min(xs), 1e-6)
    content_h = max(max(yr), 1e-6) - min(min(ys), 1e-6)
    denom_x = max(max(xr) - min(xs), 1e-6)
    margin_sym_h = max(0.0, min(1.0 - abs(min(xs) - (1 - max(xr))) / denom_x, 1.0))

    cent = (_mean(cxs), _mean(cys))
    rads = [math.hypot(c - cent[0], d - cent[1]) for c, d in zip(cxs, cys)]
    max_rad = max(rads) if rads else 0.0

    row_counts = [0, 0, 0, 0]
    col_counts = [0, 0, 0, 0]
    corner = 0
    quad_cells = set()
    for i in range(n):
        ri = min(int(cys[i] * 4), 3)
        ci4 = min(int(cxs[i] * 4), 3)
        row_counts[ri] += 1
        col_counts[ci4] += 1
        qx, qy = min(int(cxs[i] * 2), 1), min(int(cys[i] * 2), 1)
        quad_cells.add((qx, qy))
        if (cxs[i] < 0.25 or cxs[i] > 0.75) and (cys[i] < 0.25 or cys[i] > 0.75):
            corner += 1
    qbal = []
    for rr in (0, 1):
        for cc in (0, 1):
            cnt = sum(
                1
                for i in range(n)
                if min(int(cxs[i] * 2), 1) == cc and min(int(cys[i] * 2), 1) == rr
            )
            qbal.append(abs(cnt / max(n, 1) - 0.25))

    margins = [max(0.0, min(xs[i], 1 - xr[i], ys[i], 1 - yr[i])) for i in range(n)]

    g1 = {
        "n_xbands_log1p": round(math.log1p(len(bx)), 6),
        "n_ybands_log1p": round(math.log1p(len(by)), 6),
        "band_size_entropy_x": _entropy_norm([len(b) for b in bx]),
        "band_size_entropy_y": _entropy_norm([len(b) for b in by]),
        "grid_regularity_score": round(min(on_rail / max(n, 1), 1.0), 6),
        "quad_occupied_count": len(quad_cells),
        "content_quad_balance": round(sum(qbal) / 2, 6),
        "coloc_text_image": round(coloc / max(len(img_pts), 1), 6),
        "title_zone_frac": round(title_zone / max(sum(is_text), 1), 6),
        "margin_symmetry_h": margin_sym_h,
        "contain_depth_weighted_mean_slide": round(_mean([d + 1 for d in depths]), 6),
    }
    g3 = {}
    for k in range(4):
        g3[f"occ_row_frac_{k}"] = round(row_counts[k] / max(n, 1), 6)
        g3[f"occ_col_frac_{k}"] = round(col_counts[k] / max(n, 1), 6)
    g3["corner_mass"] = round(corner / max(n, 1), 6)
    g3["radial_mean"] = round(_mean(rads), 6)
    g3["radial_gini"] = _gini(rads)
    g3["ring_inner_frac"] = round(sum(1 for rr in rads if max_rad and rr <= max_rad / 2) / max(n, 1), 6)
    g3["edge_margin_mean_slide"] = round(_mean(margins), 6)

    # alignment-band membership (either axis, band size >= 2)
    x_member = [[] for _ in range(n)]
    y_member = [[] for _ in range(n)]
    for bd in bx:
        lo, hi = min(bd) - TOL_BAND, max(bd) + TOL_BAND
        mset = {i for i in range(n) if lo <= cxs[i] <= hi}
        if len(mset) >= 2:
            for i in mset:
                x_member[i].append(len(mset))
    for bd in by:
        lo, hi = min(bd) - TOL_BAND, max(bd) + TOL_BAND
        mset = {i for i in range(n) if lo <= cys[i] <= hi}
        if len(mset) >= 2:
            for i in mset:
                y_member[i].append(len(mset))
    largest_band = max(
        [len(b) for b in bx if len(b) >= 2] + [len(b) for b in by if len(b) >= 2],
        default=0,
    )

    depth_counts = Counter_(depths)

    per_node = []
    ov_degs = []
    pair_means = []
    for i in range(n):
        ci = (cxs[i], cys[i])
        others = [j for j in range(n) if j != i]
        med_x = _median([cxs[j] for j in others])
        med_y = _median([cys[j] for j in others])

        tk = type_keys[i]
        sib_x = [cxs[j] for j in others if type_keys[j] == tk]
        sib_y = [cys[j] for j in others if type_keys[j] == tk]
        rank_x = ((sorted(sib_x + [ci[0]]).index(ci[0]) + 1) / (len(sib_x) + 1)) if sib_x else 0.5
        rank_y = ((sorted(sib_y + [ci[1]]).index(ci[1]) + 1) / (len(sib_y) + 1)) if sib_y else 0.5

        d_text = NN_CAP
        d_img = NN_CAP
        nn_d = NN_CAP
        nn_same = None
        pair_d = []
        ov_deg = 0
        for j in others:
            dd = math.hypot(ci[0] - cxs[j], ci[1] - cys[j])
            pair_d.append(dd)
            nn_d = min(nn_d, dd)
            if type_keys[j] == tk:
                nn_same = dd if nn_same is None else min(nn_same, dd)
            if text_pts and is_text[j]:
                d_text = min(d_text, math.hypot(ci[0] - cxs[j], ci[1] - cys[j]))
            if img_pts and is_image[j]:
                d_img = min(d_img, math.hypot(ci[0] - cxs[j], ci[1] - cys[j]))
            if _iou(boxes[i], boxes[j]) > IOU_MIN:
                ov_deg += 1
        if not text_pts:
            d_text = 0.0
        if not img_pts:
            d_img = 0.0
        pm = _mean(pair_d)
        pair_means.append(pm)

        gn = nbr_sets[i].get("GROUP", [])
        local_set = set(idxs)
        group_in_slide = [j for j, _w in gn if j in local_set]
        al = nbr_sets[i].get("ALIGNMENT", [])
        align_deg = sum(1 for j, _w in al if j in local_set)
        group_edge_frac = round(len(group_in_slide) / max(len(gn), 1), 6) if gn else 0.0

        pn = {
            "rel_x_med": round(ci[0] - med_x, 6),
            "rel_y_med": round(ci[1] - med_y, 6),
            "width_ratio_content": round(boxes[i][2] / max(content_w, 1e-6), 6),
            "height_ratio_content": round(boxes[i][3] / max(content_h, 1e-6), 6),
            "st_rank_x": round(rank_x, 6),
            "st_rank_y": round(rank_y, 6),
            "dist_nearest_text": round(min(d_text, NN_CAP), 6),
            "dist_nearest_image": round(min(d_img, NN_CAP), 6),
            "dist_centroid_norm": round(math.hypot(ci[0] - cent[0], ci[1] - cent[1]) / max(max_rad, 1e-6), 6),
            "edge_margin_min": round(margins[i], 6),
            "band_member_frac": 0.0,
            "largest_band_frac": round(largest_band / max(n, 1), 6),
            "group_edge_frac": group_edge_frac,
            "align_degree": float(align_deg),
            "nn_same_type_ratio": round((min(nn_same, NN_CAP) / max(nn_d, 1e-6)) if nn_same is not None else NN_CAP, 6),
            "_ov_deg": ov_deg,
            "_pm": pm,
            "_iso_pending": nn_d,
        }
        del d_img
        per_node.append(pn)

    slide_pair_mean = _mean(pair_means) if pair_means else 0.0
    degs = [pn["_ov_deg"] for pn in per_node]
    bm_fracs = []
    iso_vals = []
    for k, pn in enumerate(per_node):
        in_any = (1 if x_member[k] else 0) + (1 if y_member[k] else 0)
        bm_fracs.append(round(min(in_any / max(len(bx) + len(by), 1) * 2, 1.0), 6))
        iso_vals.append(round(pn["_iso_pending"] / max(slide_pair_mean, 1e-6), 6))

    for k, pn in enumerate(per_node):
        pn["isolation_index"] = iso_vals[k]
        pn["band_member_frac"] = bm_fracs[k]
        pn["overlap_deg_mean_slide"] = round(_mean(degs), 6)
        pn["overlap_deg_max_node"] = float(max(degs)) if degs else 0.0
        pn.pop("_ov_deg")
        pn.pop("_pm")
        pn.pop("_iso_pending")

    broadcast = {}
    broadcast.update({k: g1[k] for k in G1})
    broadcast.update(g3)
    broadcast.update({
        "contain_depth_d0_frac": round(depth_counts.get(0, 0) / max(n, 1), 6),
        "contain_depth_d1_frac": round(depth_counts.get(1, 0) / max(n, 1), 6),
        "contain_depth_deep_frac": round(sum(v for kk, v in depth_counts.items() if kk >= 2) / max(n, 1), 6),
        "overlap_deg_mean_slide": round(_mean(degs), 6),
    })
    return broadcast, per_node


class Counter_(dict):
    def __init__(self, it=()):
        super().__init__()
        for x in it:
            self[x] = self.get(x, 0) + 1


def extract(rows: list[dict]):
    """Deterministic (feature_names, X); raises on non-finite output."""
    by_slide: dict[str, list[tuple[int, dict]]] = {}
    for i, r in enumerate(rows):
        by_slide.setdefault(r["slide_key"], []).append((i, r))

    cols = {name: np.zeros(len(rows)) for name in FEATURE_NAMES}
    for sk, members in by_slide.items():
        broadcast, per_node = compute_slide_broadcast(members)
        for (gi, _r), pn in zip(members, per_node):
            for name in FEATURE_NAMES:
                cols[name][gi] = float(pn.get(name, broadcast.get(name, 0.0)))

    X = np.column_stack([cols[nm] for nm in FEATURE_NAMES])
    if not np.isfinite(X).all():
        raise ValueError("non-finite context features produced")
    return FEATURE_NAMES, X
