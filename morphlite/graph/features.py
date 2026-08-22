"""Graph-derived per-node features (relational + anchor), deterministic.

Pure functions of the slide graph produced by morphlite.graph.builder.
No ground-truth/oracle information is used here.
"""
from __future__ import annotations

RELATIONAL_FEATURE_SCHEMA_VERSION = "1.0.0"

RELATIONAL_FEATURE_NAMES = [
    "rel_neighbor_count",
    "left_aligned_cnt",
    "right_aligned_cnt",
    "top_aligned_cnt",
    "bottom_aligned_cnt",
    "nn_h_gap",
    "nn_v_gap",
    "same_group_size",
    "container_child_count",
    "overlap_cnt",
    "same_font_frac",
    "similar_size_frac",
    "same_color_frac",
    "text_neighbor_frac",
]

ANCHOR_FEATURE_NAMES = [
    "is_anchor",
    "anchor_neighbors",
    "anchor_frac_band",
    "anchor_group_frac",
    "neighbor_anchor_restyle",
    "neighbor_anchor_resize",
    "neighbor_anchor_recolor",
    "neighbor_anchor_remove",
]

# Deterministic rules-engine ops -> canonical anchor operation classes.
RULE_OP_TO_ANCHOR_OP = {
    "set_font_family": "RESTYLE",
    "set_font_size": "RESIZE",
    "set_run_color": "RECOLOR",
    "remove_node": "REMOVE",
}

DEFAULT_NN_GAP = 9.9
SIMILAR_SIZE_TOL_PT = 1.0

_ANCHOR_OP_KEYS = {
    "RESTYLE": "neighbor_anchor_restyle",
    "RESIZE": "neighbor_anchor_resize",
    "RECOLOR": "neighbor_anchor_recolor",
    "REMOVE": "neighbor_anchor_remove",
}


def _adjacency(graph: dict):
    """Symmetric adjacency, incident edge-type counts, NN gaps, CONTAINS out-degree."""
    nodes = graph.get("nodes") or []
    n = len(nodes)
    idx = {g.get("id"): i for i, g in enumerate(nodes) if g.get("id") is not None}
    adj: list[set] = [set() for _ in range(n)]
    type_counts: list[dict] = [{} for _ in range(n)]
    nn_h: list[list] = [[] for _ in range(n)]
    nn_v: list[list] = [[] for _ in range(n)]
    contains_out = [0] * n
    for e in graph.get("edges") or []:
        s = idx.get(e.get("src"))
        d = idx.get(e.get("dst"))
        if s is None or d is None or s == d:
            continue
        etype = e.get("type")
        adj[s].add(d)
        adj[d].add(s)
        tc_s = type_counts[s]
        tc_d = type_counts[d]
        tc_s[etype] = tc_s.get(etype, 0) + 1
        tc_d[etype] = tc_d.get(etype, 0) + 1
        w = e.get("w")
        if etype == "NEAREST_HORIZONTAL" and isinstance(w, (int, float)):
            nn_h[s].append(float(w))
            nn_h[d].append(float(w))
        elif etype == "NEAREST_VERTICAL" and isinstance(w, (int, float)):
            nn_v[s].append(float(w))
            nn_v[d].append(float(w))
        elif etype == "CONTAINS":
            contains_out[s] += 1
    return nodes, idx, adj, type_counts, nn_h, nn_v, contains_out


def relational_features(graph: dict) -> list[dict]:
    """Pure graph-derived per-node aggregates aligned to graph["nodes"] order."""
    nodes, _idx, adj, type_counts, nn_h, nn_v, contains_out = _adjacency(graph)

    # Group membership by shared non-null parent container id.
    groups: dict = {}
    for i, g in enumerate(nodes):
        pid = g.get("parent_container_id")
        if pid is not None:
            groups.setdefault(pid, []).append(i)
    group_of: dict = {}
    for members in groups.values():
        for m in members:
            group_of[m] = members

    out = []
    for i, g in enumerate(nodes):
        nbrs = sorted(adj[i])
        deg = len(nbrs)

        eff_i = g.get("eff") or {}
        fam_i = eff_i.get("font_family")
        size_i = eff_i.get("font_size_pt")
        col_i = eff_i.get("color")

        same_font = same_size = same_color = text_nbrs = 0
        denom_font = denom_size = denom_color = 0
        for j in nbrs:
            gj = nodes[j]
            eff_j = gj.get("eff") or {}
            fam_j = eff_j.get("font_family")
            size_j = eff_j.get("font_size_pt")
            col_j = eff_j.get("color")
            if fam_i is not None and fam_j is not None:
                denom_font += 1
                if fam_j == fam_i:
                    same_font += 1
            if size_i is not None and size_j is not None:
                denom_size += 1
                try:
                    if abs(float(size_j) - float(size_i)) <= SIMILAR_SIZE_TOL_PT:
                        same_size += 1
                except (TypeError, ValueError):
                    pass
            if col_i is not None and col_j is not None:
                denom_color += 1
                if col_j == col_i:
                    same_color += 1
            if (gj.get("text_len") or 0) > 0:
                text_nbrs += 1

        grp = group_of.get(i)
        out.append(
            {
                "rel_neighbor_count": deg,
                "left_aligned_cnt": type_counts[i].get("LEFT_ALIGNED", 0),
                "right_aligned_cnt": type_counts[i].get("RIGHT_ALIGNED", 0),
                "top_aligned_cnt": type_counts[i].get("TOP_ALIGNED", 0),
                "bottom_aligned_cnt": type_counts[i].get("BOTTOM_ALIGNED", 0),
                "nn_h_gap": round(min(nn_h[i]), 4) if nn_h[i] else DEFAULT_NN_GAP,
                "nn_v_gap": round(min(nn_v[i]), 4) if nn_v[i] else DEFAULT_NN_GAP,
                "same_group_size": len(grp) if grp else 0,
                "container_child_count": contains_out[i],
                "overlap_cnt": type_counts[i].get("OVERLAPS", 0),
                "same_font_frac": round(same_font / denom_font, 4) if denom_font else 0.0,
                "similar_size_frac": round(same_size / denom_size, 4) if denom_size else 0.0,
                "same_color_frac": round(same_color / denom_color, 4) if denom_color else 0.0,
                "text_neighbor_frac": round(text_nbrs / deg, 4) if deg else 0.0,
            }
        )
    return out


def _normalize_anchors(anchors) -> dict:
    """node_id -> canonical op string; unknown ops map to None (still anchors)."""
    norm: dict = {}
    for nid, spec in (anchors or {}).items():
        if isinstance(spec, str):
            op, conf = spec, None
        elif isinstance(spec, dict):
            op, conf = spec.get("op"), spec.get("confidence")
        else:
            continue
        norm[nid] = {"op": RULE_OP_TO_ANCHOR_OP.get(op), "confidence": conf}
    return norm


def anchor_features(graph: dict, anchors: dict | None) -> list[dict]:
    """Anchor-context features per node; all zeros when `anchors` is empty.

    `anchors` maps node_id -> {"op", "confidence"} where op is a deterministic
    rules-engine operation name (see RULE_OP_TO_ANCHOR_OP).
    """
    nodes, idx, adj, _tc, _nh, _nv, _co = _adjacency(graph)
    norm = _normalize_anchors(anchors)
    anchored = {idx[nid] for nid in norm if nid in idx}

    # Group membership by shared non-null parent container id.
    groups: dict = {}
    for i, g in enumerate(nodes):
        pid = g.get("parent_container_id")
        if pid is not None:
            groups.setdefault(pid, []).append(i)
    group_of: dict = {}
    for members in groups.values():
        for m in members:
            group_of[m] = members

    zeros = {k: 0 for k in ANCHOR_FEATURE_NAMES}
    out = []
    for i, g in enumerate(nodes):
        if not norm:
            out.append(dict(zeros))
            continue
        nbrs = sorted(adj[i])
        deg = len(nbrs)
        anc_nbrs = [j for j in nbrs if j in anchored]
        typed = {k: 0 for k in _ANCHOR_OP_KEYS.values()}
        for j in anc_nbrs:
            nid_j = nodes[j].get("id")
            canon = (norm.get(nid_j) or {}).get("op")
            key = _ANCHOR_OP_KEYS.get(canon)
            if key:
                typed[key] += 1

        grp = group_of.get(i)
        grp_excl = [m for m in grp if m != i] if grp else []
        grp_anchor = sum(1 for m in grp_excl if m in anchored)
        group_frac = grp_anchor / len(grp_excl) if grp_excl else 0.0

        out.append(
            {
                "is_anchor": 1 if i in anchored else 0,
                "anchor_neighbors": len(anc_nbrs),
                "anchor_frac_band": round(len(anc_nbrs) / deg, 4) if deg else 0.0,
                "anchor_group_frac": round(group_frac, 4),
                "neighbor_anchor_restyle": typed["neighbor_anchor_restyle"],
                "neighbor_anchor_resize": typed["neighbor_anchor_resize"],
                "neighbor_anchor_recolor": typed["neighbor_anchor_recolor"],
                "neighbor_anchor_remove": typed["neighbor_anchor_remove"],
            }
        )
    return out
