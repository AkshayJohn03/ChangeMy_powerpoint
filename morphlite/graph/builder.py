"""Slide dependency-graph builder: AST-v2 slide -> graph dict.

Pure and deterministic: no I/O, no randomness. Groups are flattened in order
via morphlite.ast.extractor.flatten_nodes so graph node order matches AST
document order.
"""
from __future__ import annotations

from ..ast import extractor
from .relations import (
    ALIGN_EPS,
    OVERLAP_IOU_MIN,
    bbox_of,
    contains_box,
    iou,
)

# Alignment edges require both boxes valid with area >= this (normalized units).
MIN_AREA_ALIGNED = 0.001
# Neighbor candidates need overlap > 50% of the smaller extent on the cross-axis.
NEIGHBOR_OVERLAP_MIN_FRAC = 0.5
# Geometric CONTAINS requires area(outer) >= 4 * area(inner).
CONTAIN_AREA_RATIO_MIN = 4.0

EFF_KEYS = ("font_family", "font_size_pt", "color")


def _eff_subset(node: dict) -> dict:
    src = node.get("effective") or {}
    out = {}
    for k in EFF_KEYS:
        v = src.get(k)
        out[k] = v.get("value") if isinstance(v, dict) else None
    return out


def _graph_node(node: dict) -> dict:
    paragraphs = node.get("paragraphs") or []
    text_len = sum(len(p.get("text") or "") for p in paragraphs)
    return {
        "id": node.get("id"),
        "shape_id": node.get("shape_id"),
        "type": node.get("type"),
        "bbox_norm": node.get("bbox_norm"),
        "container_depth": int(node.get("container_depth") or 0),
        "parent_container_id": node.get("parent_container_id"),
        "text_len": int(text_len),
        "name_lower": str(node.get("name") or "").lower(),
        "eff": _eff_subset(node),
        "fill_color": node.get("fill_color"),
    }


class _EdgeSink:
    """Dedup + ordering for edges (no self edges, no duplicate (src, dst, type))."""

    def __init__(self) -> None:
        self.edges: list[dict] = []
        self._seen: set[tuple] = set()

    def add(self, src, dst, etype, w=None) -> None:
        if src is None or dst is None or src == dst:
            return
        key = (src, dst, etype)
        if key in self._seen:
            return
        self._seen.add(key)
        e = {"src": src, "dst": dst, "type": etype}
        if w is not None:
            e["w"] = round(float(w), 6)
        self.edges.append(e)

    def sorted(self) -> list[dict]:
        return sorted(self.edges, key=lambda e: (e["type"], e["src"], e["dst"]))


def build_slide_graph(slide: dict, deck_id: str = "") -> dict:
    """Build {"slide_id","nodes","edges","graph_metadata"} from an AST-v2 slide."""
    slide = slide or {}
    ast_nodes = extractor.flatten_nodes(slide.get("nodes") or [])
    gnodes = [_graph_node(n) for n in ast_nodes]
    n = len(gnodes)
    ids = [g["id"] for g in gnodes]
    boxes = [bbox_of(nd) for nd in ast_nodes]

    def usable(i: int) -> bool:
        b = boxes[i]
        return b is not None and (b[2] * b[3]) >= MIN_AREA_ALIGNED

    sink = _EdgeSink()

    # --- hierarchy map for CONTAINS (parent container -> child), cycle-guarded ---
    idx_by_id: dict = {}
    for i, nid in enumerate(ids):
        if nid is not None and nid not in idx_by_id:
            idx_by_id[nid] = i

    # --- pairwise geometric relations ---
    for i in range(n):
        bi = boxes[i]
        gi = gnodes[i]
        for j in range(i + 1, n):
            bj = boxes[j]
            gj = gnodes[j]

            # SAME_GROUP: shared non-null parent container
            pid_i, pid_j = gi["parent_container_id"], gj["parent_container_id"]
            if pid_i is not None and pid_j is not None and pid_i == pid_j:
                sink.add(ids[i], ids[j], "SAME_GROUP")
                sink.add(ids[j], ids[i], "SAME_GROUP")

            if bi is None or bj is None:
                continue

            # Alignment edges (both boxes valid, area >= MIN_AREA_ALIGNED)
            if usable(i) and usable(j):
                xi, yi, wi, hi = bi
                xj, yj, wj, hj = bj
                if abs(xi - xj) < ALIGN_EPS:
                    sink.add(ids[i], ids[j], "LEFT_ALIGNED")
                    sink.add(ids[j], ids[i], "LEFT_ALIGNED")
                if abs((xi + wi) - (xj + wj)) < ALIGN_EPS:
                    sink.add(ids[i], ids[j], "RIGHT_ALIGNED")
                    sink.add(ids[j], ids[i], "RIGHT_ALIGNED")
                if abs(yi - yj) < ALIGN_EPS:
                    sink.add(ids[i], ids[j], "TOP_ALIGNED")
                    sink.add(ids[j], ids[i], "TOP_ALIGNED")
                if abs((yi + hi) - (yj + hj)) < ALIGN_EPS:
                    sink.add(ids[i], ids[j], "BOTTOM_ALIGNED")
                    sink.add(ids[j], ids[i], "BOTTOM_ALIGNED")

            # Geometric CONTAINS (directed big -> small)
            a_i, a_j = bi[2] * bi[3], bj[2] * bj[3]
            if contains_box(bj, bi) and a_j >= CONTAIN_AREA_RATIO_MIN * max(a_i, 1e-12):
                sink.add(ids[j], ids[i], "CONTAINS")
            elif contains_box(bi, bj) and a_i >= CONTAIN_AREA_RATIO_MIN * max(a_j, 1e-12):
                sink.add(ids[i], ids[j], "CONTAINS")

            # OVERLAPS: high IoU pair that is not already a CONTAINS pair
            if iou(bi, bj) >= OVERLAP_IOU_MIN and not (
                contains_box(bi, bj) or contains_box(bj, bi)
            ):
                sink.add(ids[i], ids[j], "OVERLAPS")
                sink.add(ids[j], ids[i], "OVERLAPS")

    # --- nearest-neighbor relations (per node argmin gap, both directions) ---
    for i in range(n):
        bi = boxes[i]
        if bi is None:
            continue
        best_h = (-1, None)
        best_v = (-1, None)
        for j in range(n):
            if j == i:
                continue
            bj = boxes[j]
            if bj is None:
                continue
            xi, yi, wi, hi = bi
            xj, yj, wj, hj = bj
            v_ov = min(yi + hi, yj + hj) - max(yi, yj)
            h_ov = min(xi + wi, xj + wj) - max(xi, xj)
            min_hi, min_wi = min(hi, hj), min(wi, wj)
            gap_h = max(0.0, max(xi, xj) - min(xi + wi, xj + wj))
            gap_v = max(0.0, max(yi, yj) - min(yi + hi, yj + hj))
            if v_ov > NEIGHBOR_OVERLAP_MIN_FRAC * min_hi and (
                best_h[1] is None or gap_h < best_h[1]
            ):
                best_h = (j, gap_h)
            if h_ov > NEIGHBOR_OVERLAP_MIN_FRAC * min_wi and (
                best_v[1] is None or gap_v < best_v[1]
            ):
                best_v = (j, gap_v)
        if best_h[0] >= 0:
            j, gap = best_h
            sink.add(ids[i], ids[j], "NEAREST_HORIZONTAL", w=gap)
            sink.add(ids[j], ids[i], "NEAREST_HORIZONTAL", w=gap)
        if best_v[0] >= 0:
            j, gap = best_v
            sink.add(ids[i], ids[j], "NEAREST_VERTICAL", w=gap)
            sink.add(ids[j], ids[i], "NEAREST_VERTICAL", w=gap)

    # --- hierarchy CONTAINS edges (parent container -> direct child) ---
    child_ids: set = set()
    stack = list(ast_nodes)
    seen_ast: set[int] = set()
    while stack:  # visited guard terminates even on cyclic parent references
        nd = stack.pop()
        marker = id(nd)
        if marker in seen_ast:
            continue
        seen_ast.add(marker)
        pid = nd.get("parent_container_id")
        nid = nd.get("id")
        if pid is not None and nid is not None and pid in idx_by_id and pid != nid:
            sink.add(pid, nid, "CONTAINS")
            child_ids.add(nid)
        for ch in nd.get("children") or []:
            stack.append(ch)

    edges = sink.sorted()
    by_type: dict[str, int] = {}
    for e in edges:
        by_type[e["type"]] = by_type.get(e["type"], 0) + 1

    return {
        "slide_id": slide.get("slide_id"),
        "nodes": gnodes,
        "edges": edges,
        "graph_metadata": {
            "n_nodes": n,
            "n_edges_by_type": {t: by_type[t] for t in sorted(by_type)},
            "deck_id": deck_id,
        },
    }
