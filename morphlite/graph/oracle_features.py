# ORACLE_ONLY: ground-truth-derived features. FORBIDDEN in production inference paths.
"""Oracle context features derived from TRUE diff labels (training/eval only).

These features encode ground-truth label information about neighbors and must
never be imported by production inference code. Importing this module outside
of training/evaluation pipelines is a policy violation enforced by tests.
"""
from __future__ import annotations

ORACLE_ONLY = True

ORACLE_CONTEXT_FEATURES = [
    "nbr_restyle",
    "nbr_resize",
    "nbr_move",
    "nbr_remove",
    "nbr_recolor",
    "nbr_unchanged",
    "nbr_weak_frac",
]

_LABEL_CLASSES = (
    "RESTYLE",
    "RESIZE",
    "MOVE",
    "REMOVE",
    "RECOLOR",
    "UNCHANGED",
)
_WEAK_CLASSES = ("RESTYLE", "RESIZE", "REMOVE", "MOVE")
_COUNT_FEATURES = ORACLE_CONTEXT_FEATURES[:-1]


def oracle_context_features(graph: dict, labels_by_node: dict | None) -> list[dict]:
    """TRUE-label neighbor context per node, aligned to graph["nodes"] order.

    `labels_by_node` maps node_id -> canonical label string, e.g.
    {"RESTYLE","RESIZE","MOVE","REMOVE","RECOLOR","UNCHANGED"}; unrecognized
    label values still count toward a neighbor's degree but no class counter.
    nbr_weak_frac = (RESTYLE+RESIZE+REMOVE+MOVE)/labeled_degree, 0.0 when the
    node has no labeled neighbors. All zeros when `labels_by_node` is empty.
    """
    nodes = graph.get("nodes") or []
    n = len(nodes)
    zeros = {k: 0 for k in _COUNT_FEATURES}
    zeros["nbr_weak_frac"] = 0.0
    labels = labels_by_node or {}
    if not labels:
        return [dict(zeros) for _ in range(n)]

    idx = {g.get("id"): i for i, g in enumerate(nodes) if g.get("id") is not None}
    adj: list[set] = [set() for _ in range(n)]
    for e in graph.get("edges") or []:
        s = idx.get(e.get("src"))
        d = idx.get(e.get("dst"))
        if s is None or d is None or s == d:
            continue
        adj[s].add(d)
        adj[d].add(s)

    out = []
    for i in range(n):
        counts = {k: 0 for k in _COUNT_FEATURES}
        nbrs = sorted(adj[i])
        labeled_deg = 0
        for j in nbrs:
            lab = labels.get(nodes[j].get("id"))
            if lab is None:
                continue
            labeled_deg += 1
            u = str(lab).upper()
            if u in _LABEL_CLASSES:
                counts["nbr_" + u.lower()] += 1
        weak = sum(counts["nbr_" + c.lower()] for c in _WEAK_CLASSES)
        row = dict(counts)
        row["nbr_weak_frac"] = round(weak / labeled_deg, 4) if labeled_deg else 0.0
        out.append(row)
    return out
