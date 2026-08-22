"""Relational leakage guard: sentinel-expansion regression + oracle separation.

Regression gate for the make_X sentinel fix ("__oracle__"/"__anchor__" must be
expanded to real feature names and read from their own block) plus static
source-scan assertions keeping ground-truth signals out of production code.

    python -m morphlite.tests.test_relational_guard
"""
from __future__ import annotations

import copy
import re
import sys
from pathlib import Path

import numpy as np

from ..features.node_features_v2 import FEATURE_NAMES_V2
from ..graph.builder import build_slide_graph
from ..graph.features import (
    ANCHOR_FEATURE_NAMES,
    RELATIONAL_FEATURE_NAMES,
    anchor_features,
    relational_features,
)
from ..graph.oracle_features import ORACLE_CONTEXT_FEATURES
from ..inference.safety_gate import vet, vet_plan
from ..evaluation.plan_metrics import operation_prf
from ..evaluation.property_metrics import property_accuracy
from ..training import relational_benchmark as rb

MORPHLITE_ROOT = Path(__file__).resolve().parents[1]
SCAN_EXTS = {".py", ".json", ".jsonc", ".md", ".txt"}


def _row(k: int) -> dict:
    return {
        "sample_id": f"d{chr(97 + k)}__s001__n{k:03d}",
        "group": "familyA",
        "label": "RESTYLE",
        "base": {name: 1.0 + k + i * 0.01 for i, name in enumerate(FEATURE_NAMES_V2)},
        "rel": {name: 2.0 + k + i * 0.01 for i, name in enumerate(RELATIONAL_FEATURE_NAMES)},
        "anchor": {name: 3.0 + k + i * 0.01 for i, name in enumerate(ANCHOR_FEATURE_NAMES)},
        "oracle": {name: 4.0 + k + i * 0.01 for i, name in enumerate(ORACLE_CONTEXT_FEATURES)},
    }


def _zero(names):
    return {name: 0 for name in names}


def test_make_x_sentinel_expansion_nonzero():
    """(a) Regression: ORACLE/ANCHOR variants expand sentinels to real columns."""
    rows = [_row(0), _row(1), _row(2)]
    offset = len(FEATURE_NAMES_V2)

    x_oracle = rb.make_X(rows, "ORACLE_CONTEXT")
    assert x_oracle.shape == (3, offset + len(ORACLE_CONTEXT_FEATURES))
    assert (np.var(x_oracle[:, offset:], axis=0) > 0).all(), "all-zero oracle column"

    x_anchor = rb.make_X(rows, "ANCHOR_CONTEXT")
    assert x_anchor.shape == (3, offset + len(ANCHOR_FEATURE_NAMES))
    assert (np.var(x_anchor[:, offset:], axis=0) > 0).all(), "all-zero anchor column"

    x_base = rb.make_X(rows, "BASE_NODE_ONLY")
    assert x_base.shape == (3, offset)

    x_all = rb.make_X(rows, "ALL_RELATIONAL")
    assert x_all.shape == (3, offset + len(RELATIONAL_FEATURE_NAMES))
    print(
        f"sentinel expansion OK (oracle {x_oracle.shape}, anchor {x_anchor.shape}, "
        f"base {x_base.shape})"
    )


def test_make_x_source_block_routing():
    """Extra columns must read the variant's OWN block, not a sibling block."""
    rows = []
    for k in range(3):
        r = _row(k)
        r["rel"] = _zero(RELATIONAL_FEATURE_NAMES)  # rel dead, oracle/anchor alive
        rows.append(r)
    offset = len(FEATURE_NAMES_V2)

    geom = rb.make_X(rows, "GEOMETRY_RELATIONS")
    assert (geom[:, offset:] == 0.0).all(), "GEOMETRY_RELATIONS leaked a non-rel block"

    orc = rb.make_X(rows, "ORACLE_CONTEXT")
    assert (orc[:, offset:] != 0.0).any()
    for k in range(3):
        expected = np.array([rows[k]["oracle"][n] for n in ORACLE_CONTEXT_FEATURES], dtype=float)
        assert np.allclose(orc[k, offset:], expected)

    anch = rb.make_X(rows, "ANCHOR_CONTEXT")
    for k in range(3):
        expected = np.array([rows[k]["anchor"][n] for n in ANCHOR_FEATURE_NAMES], dtype=float)
        assert np.allclose(anch[k, offset:], expected)
    print("source block routing OK")


def test_make_x_unknown_variant_loud():
    try:
        rb.make_X([_row(0)], "NOT_A_VARIANT")
    except KeyError:
        print("unknown variant raises OK")
    else:
        raise AssertionError("unknown variant silently produced features")


def test_variants_schema_no_silent_zeros():
    """Any explicit name list must exist in the rel schema, else column goes 0."""
    for v, names in rb.VARIANTS.items():
        if names is None or names == [] or names == ["__oracle__"] or names == ["__anchor__"]:
            continue
        unknown = [n for n in names if n not in RELATIONAL_FEATURE_NAMES]
        assert not unknown, f"{v}: names missing from rel schema -> silent zero cols: {unknown}"
    print(f"variants schema OK ({len(rb.VARIANTS)} variants)")


def test_source_scan_inference_rules_clean():
    """(b) No 'oracle' token anywhere under morphlite/inference or morphlite/rules."""
    checked = 0
    offenders = []
    for sub in ("inference", "rules"):
        base = MORPHLITE_ROOT / sub
        assert base.is_dir(), base
        for p in sorted(base.rglob("*")):
            if "__pycache__" in p.parts or p.suffix.lower() not in SCAN_EXTS:
                continue
            try:
                text = p.read_text(encoding="utf-8", errors="ignore").lower()
            except OSError:
                continue
            checked += 1
            if "oracle" in text:
                offenders.append(str(p.relative_to(MORPHLITE_ROOT)))
    assert checked > 0
    assert not offenders, f"oracle referenced in production code: {offenders}"
    print(f"inference/rules oracle-free OK ({checked} files)")


def test_rules_engine_no_truth_inputs():
    src = (MORPHLITE_ROOT / "rules" / "engine.py").read_text(encoding="utf-8").lower()
    for banned in ("transformation_record", "validated_pairs", "truth", "branded"):
        assert banned not in src, f"rules/engine.py references '{banned}'"
    print("rules/engine truth-inputs clean OK")


def test_benchmark_function_scoped_oracle_imports():
    src_lines = (MORPHLITE_ROOT / "training" / "relational_benchmark.py").read_text(
        encoding="utf-8"
    ).splitlines()
    for i, ln in enumerate(src_lines, 1):
        if re.search(r"^\s*(from|import)\s", ln) and "oracle" in ln.lower():
            assert ln[:1].isspace() or ln.startswith("\t"), (
                f"module-level oracle import at relational_benchmark.py:{i}"
            )
    full = "\n".join(src_lines)
    assert "branded" not in full.lower(), "benchmark touches branded decks"
    assert "branded_deck" not in full
    # make_X must never fold identifiers/groups/labels into the feature matrix
    body = full[full.index("def make_X") : full.index("\ndef ", full.index("def make_X"))]
    for tok in ("sample_id", "deck_id", "group", "label"):
        assert not re.search(rf"\b{tok}\b", body), f"make_X references '{tok}'"
    print("function-scoped oracle imports OK")


def test_safety_gate_blocks_forbidden_ops():
    """(c) move_node/add_node stay blocked even at perfect confidence."""
    for op in ("move_node", "add_node"):
        ok, reason = vet({"op": op, "confidence": 1.0})
        assert not ok and "blocked" in reason, (op, ok, reason)
    ok, reason = vet({"op": "set_font_family", "confidence": 0.9})
    assert ok and reason == "ok"
    ok, reason = vet({"op": "set_font_size", "confidence": 0.5})
    assert not ok and reason == "below_min_confidence"

    ops = [
        {"op": "set_run_color", "node_id": "a", "value": "#112233", "confidence": 0.9},
        {"op": "move_node", "node_id": "b", "value": None, "confidence": 1.0},
    ]
    snapshot = copy.deepcopy(ops)
    approved, rejected = vet_plan(ops)
    assert [o["op"] for o in approved] == ["set_run_color"]
    assert [o["op"] for o in rejected] == ["move_node"]
    assert ops == snapshot, "vet_plan mutated its input ops"
    print("safety gate blocks OK")


def test_anchor_ignores_label_fields():
    """Anchor provenance: truth-ish keys in anchor specs must be ignored."""
    slide = {
        "slide_id": "synthetic_guard__s001",
        "nodes": [
            {"id": "ga_n1", "type": "TEXT", "parent_container_id": None,
             "bbox_norm": {"x": 0.10, "y": 0.10, "w": 0.20, "h": 0.20},
             "paragraphs": [{"text": "alpha", "runs": []}]},
            {"id": "gb_n1", "type": "TEXT", "parent_container_id": None,
             "bbox_norm": {"x": 0.50, "y": 0.10, "w": 0.20, "h": 0.20},
             "paragraphs": [{"text": "beta", "runs": []}]},
        ],
    }
    g = build_slide_graph(slide)
    anchors = {"gb_n1": {"op": "set_font_family", "confidence": 0.9}}
    poisoned = dict(anchors)
    poisoned["gb_n1"] = {
        **anchors["gb_n1"],
        "label": "REMOVE",
        "truth_tags": ["STRUCTURE_REMOVE"],
        "record": {"kind": "MORPH"},
    }
    assert anchor_features(g, anchors) == anchor_features(g, poisoned)
    feats = anchor_features(g, anchors)
    assert feats[1]["is_anchor"] == 1
    assert sum(r["anchor_neighbors"] for r in feats) == 1  # exactly the other node
    print("anchor label-field immunity OK")


def test_evaluation_metrics_do_not_mutate_inputs():
    preds = [
        {"op": "set_font_family", "node_id": "n1", "value": "Arial"},
        {"op": "remove_node", "node_id": "n2", "value": None},
    ]
    truth = {
        "n1": {"label": "RESTYLE", "record": {"kind": "MORPH",
                                              "tags": ["TYPOGRAPHY_FONT_FAMILY"]}},
        "n2": {"label": "REMOVE", "record": {"kind": "REMOVED"}},
    }
    p_snap, t_snap = copy.deepcopy(preds), copy.deepcopy(truth)
    operation_prf(preds, truth)
    property_accuracy(preds, truth)
    assert preds == p_snap and truth == t_snap, "metric mutated its inputs"
    print("evaluation purity OK")


TESTS = [
    test_make_x_sentinel_expansion_nonzero,
    test_make_x_source_block_routing,
    test_make_x_unknown_variant_loud,
    test_variants_schema_no_silent_zeros,
    test_source_scan_inference_rules_clean,
    test_rules_engine_no_truth_inputs,
    test_benchmark_function_scoped_oracle_imports,
    test_safety_gate_blocks_forbidden_ops,
    test_anchor_ignores_label_fields,
    test_evaluation_metrics_do_not_mutate_inputs,
]


def main() -> int:
    for test in TESTS:
        test()
        print(f"ok {test.__name__}")
    print("RELATIONAL GUARD PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
