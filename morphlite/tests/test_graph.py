"""Verification gate: dependency-light slide graph + graph features.

Run: python -m morphlite.tests.test_graph
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from ..graph.builder import build_slide_graph
from ..graph.features import (
    ANCHOR_FEATURE_NAMES,
    RELATIONAL_FEATURE_NAMES,
    anchor_features,
    relational_features,
)
from ..graph.relations import EDGE_TYPES, bbox_of, iou
from ..graph import oracle_features as oracle_mod
from ..graph.oracle_features import oracle_context_features

MORPHLITE_ROOT = Path(__file__).resolve().parents[1]


def _node(nid, x, y, w, h, *, type="TEXT", parent=None, depth=0, name="", paragraphs=None, **extra):
    n = {
        "id": nid,
        "type": type,
        "shape_id": abs(hash(nid)) % 100000,
        "parent_container_id": parent,
        "container_depth": depth,
        "bbox_norm": {"x": x, "y": y, "w": w, "h": h} if x is not None else None,
        "name": name,
        "paragraphs": paragraphs if paragraphs is not None else [{"text": "abc", "runs": []}],
    }
    n.update(extra)
    return n


def _rich_slide() -> dict:
    """Synthetic slide (no real data): groups, alignments, containment, overlaps."""
    return {
        "slide_id": "synthetic__s001",
        "nodes": [
            _node("g1", 0.05, 0.05, 0.9, 0.4, type="GROUP", name="Group 1", children=[
                _node("a", 0.10, 0.08, 0.2, 0.1, parent="g1", depth=1),
                _node("b", 0.40, 0.08, 0.2, 0.1, parent="g1", depth=1),  # top-aligned with a
                _node("c", 0.70, 0.09, 0.15, 0.12, parent="g1", depth=1),  # overlaps b
            ]),
            _node("t1", 0.05, 0.60, 0.3, 0.1, name="Title 1"),
            _node("t2", 0.50, 0.60, 0.3, 0.1, name="Title 2"),  # top-aligned with t1
            _node("big", 0.02, 0.02, 0.96, 0.95, type="SHAPE", name="Backdrop"),
            _node("nobox", None, None, None, None, name="NoBox"),
        ],
    }


def test_determinism():
    s = _rich_slide()
    g1 = build_slide_graph(s, deck_id="deck_9999")
    g2 = build_slide_graph(s, deck_id="deck_9999")
    assert json.dumps(g1, sort_keys=True) == json.dumps(g2, sort_keys=True)
    print(f"determinism OK (nodes={g1['graph_metadata']['n_nodes']} edges={len(g1['edges'])})")


def test_empty_slide():
    g = build_slide_graph({"slide_id": "x__s001", "nodes": []})
    assert g["nodes"] == [] and g["edges"] == []
    assert g["graph_metadata"]["n_nodes"] == 0
    assert g["graph_metadata"]["n_edges_by_type"] == {}
    assert relational_features(g) == []
    assert anchor_features(g, {}) == []
    print("empty slide OK")


def test_single_node():
    g = build_slide_graph({"slide_id": "x__s001", "nodes": [_node("solo", 0.1, 0.1, 0.2, 0.2)]})
    assert g["graph_metadata"]["n_nodes"] == 1 and g["edges"] == []
    f = relational_features(g)[0]
    assert f["rel_neighbor_count"] == 0 and f["nn_h_gap"] == 9.9 and f["nn_v_gap"] == 9.9
    assert f["same_group_size"] == 0 and f["container_child_count"] == 0
    assert f["text_neighbor_frac"] == 0.0 and f["similar_size_frac"] == 0.0
    print("single node OK")


def test_missing_bbox():
    g = build_slide_graph(
        {
            "slide_id": "x__s001",
            "nodes": [
                _node("m", None, None, None, None),
                _node("ok", 0.1, 0.1, 0.2, 0.2),
            ],
        }
    )
    assert bbox_of({"bbox_norm": None}) is None
    assert bbox_of({}) is None
    types = {e["type"] for e in g["edges"]}
    assert not any(e["src"] == "m" or e["dst"] == "m" for e in g["edges"])
    assert "OVERLAPS" not in types
    print("missing bbox OK")


def test_cyclic_parents_terminate():
    slide = {
        "slide_id": "x__s001",
        "nodes": [
            _node("ca", 0.1, 0.1, 0.2, 0.2, parent="cb"),
            _node("cb", 0.4, 0.1, 0.2, 0.2, parent="ca"),
            _node("cc", 0.7, 0.1, 0.2, 0.2, parent="cc"),  # self-parent cycle
        ],
    }
    g = build_slide_graph(slide)  # must terminate
    assert g["graph_metadata"]["n_nodes"] == 3
    assert all(e["src"] != e["dst"] for e in g["edges"])
    contains_pairs = {(e["src"], e["dst"]) for e in g["edges"] if e["type"] == "CONTAINS"}
    assert ("ca", "cb") in contains_pairs and ("cb", "ca") in contains_pairs
    print("cyclic parents OK")


def test_no_self_edges_and_sorted():
    graphs = [build_slide_graph(_rich_slide(), deck_id="d")]
    for g in graphs:
        ids = {n["id"] for n in g["nodes"]}
        for e in g["edges"]:
            assert e["src"] != e["dst"], e
            assert e["src"] in ids and e["dst"] in ids, e
            assert e["type"] in EDGE_TYPES, e
        keys = [(e["type"], e["src"], e["dst"]) for e in g["edges"]]
        assert keys == sorted(keys), "edges not sorted by (type, src, dst)"
        assert len(keys) == len(set(keys)), "duplicate (src,dst,type)"
    # semantic spot-checks on the rich slide
    g = graphs[0]
    et = {(e["src"], e["dst"], e["type"]) for e in g["edges"]}
    assert ("a", "b", "TOP_ALIGNED") in et and ("b", "a", "TOP_ALIGNED") in et
    assert ("g1", "a", "CONTAINS") in et  # hierarchy edge
    nn = [e for e in g["edges"] if e["type"] == "NEAREST_HORIZONTAL"]
    assert nn and all(isinstance(e.get("w"), float) and e["w"] >= 0.0 for e in nn)
    print(f"no self edges / sorted OK (edge types={sorted(g['graph_metadata']['n_edges_by_type'])})")


def test_feature_lengths_align():
    g = build_slide_graph(_rich_slide(), deck_id="d")
    rf = relational_features(g)
    af = anchor_features(g, {})
    of = oracle_context_features(g, {})
    assert len(rf) == len(af) == len(of) == len(g["nodes"])
    for row in rf:
        assert set(row.keys()) == set(RELATIONAL_FEATURE_NAMES)
    labels = {g["nodes"][1]["id"]: "RESTYLE", g["nodes"][3]["id"]: "UNCHANGED"}
    of2 = oracle_context_features(g, labels)
    assert len(of2) == len(g["nodes"])
    for row in of2:
        assert set(row.keys()) == {
            "nbr_restyle", "nbr_resize", "nbr_move", "nbr_remove",
            "nbr_recolor", "nbr_unchanged", "nbr_weak_frac",
        }
    assert of2[2]["nbr_restyle"] == 1  # node 2 is adjacent to labeled node 1
    assert of2[2]["nbr_unchanged"] == 1  # ... and to node 3 labeled UNCHANGED
    assert of2[2]["nbr_weak_frac"] == 0.5  # 1 weak-class label / 2 labeled neighbors
    print("feature lengths align OK")


def test_anchor_zeros():
    g = build_slide_graph(_rich_slide(), deck_id="d")
    af = anchor_features(g, {})
    assert len(af) == len(g["nodes"])
    assert all(all(v == 0 or v == 0.0 for v in row.values()) for row in af)
    # typed anchors propagate to neighbors only via adjacency
    anchors = {g["nodes"][0]["id"]: {"op": "set_font_family", "confidence": 0.9}}
    af2 = anchor_features(g, anchors)
    assert af2[0]["is_anchor"] == 1 and af2[0]["neighbor_anchor_restyle"] == 0
    nid0 = g["nodes"][0]["id"]
    nbr0 = {
        e["dst"] if e["src"] == nid0 else e["src"]
        for e in g["edges"] if nid0 in (e["src"], e["dst"])
    }
    assert sum(r["neighbor_anchor_restyle"] for r in af2) == len(nbr0)
    print("anchor zeros OK")


def test_oracle_sentinel():
    first_line = (MORPHLITE_ROOT / "graph" / "oracle_features.py").read_text(
        encoding="utf-8"
    ).splitlines()[0]
    assert first_line.startswith("# ORACLE_ONLY"), first_line
    assert oracle_mod.ORACLE_ONLY is True
    rows = oracle_context_features(build_slide_graph(_rich_slide()), {})
    assert all(all(v == 0 or v == 0.0 for v in r.values()) for r in rows)
    print("oracle sentinel OK")


def test_inference_rules_clean():
    banned = "oracle_features"
    checked = 0
    for sub in ("inference", "rules"):
        base = MORPHLITE_ROOT / sub
        assert base.is_dir(), base
        for p in sorted(base.rglob("*")):
            if p.is_file() and p.suffix in (".py", ".json", ".jsonc", ".md", ".txt"):
                try:
                    text = p.read_text(encoding="utf-8", errors="ignore")
                except OSError:
                    continue
                assert banned not in text, f"forbidden reference in {sub}/{p.name}"
                checked += 1
    assert checked > 0
    print(f"inference/rules clean OK ({checked} files scanned)")


if __name__ == "__main__":
    test_determinism()
    test_empty_slide()
    test_single_node()
    test_missing_bbox()
    test_cyclic_parents_terminate()
    test_no_self_edges_and_sorted()
    test_feature_lengths_align()
    test_anchor_zeros()
    test_oracle_sentinel()
    test_inference_rules_clean()
    print("GRAPH GATE PASSED")
    sys.exit(0)
