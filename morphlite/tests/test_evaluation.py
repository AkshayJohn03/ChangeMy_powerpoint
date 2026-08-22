"""Synthetic-fixture gate for the evaluation module.

    python -m morphlite.tests.test_evaluation
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from morphlite.evaluation.plan_metrics import (
    OP_CLASS_MAP,
    operation_prf,
    truth_label,
    truth_node_id,
)
from morphlite.evaluation.property_metrics import property_accuracy
from morphlite.evaluation.safety_metrics import safety_counters, unsafe_with_truth
from morphlite.evaluation.slide_metrics import slide_scores
from morphlite.evaluation.harness import run_evaluation

CLASSES = ("RESTYLE", "RESIZE", "RECOLOR", "REMOVE")


def _typography(family_after="Arial", size_after=14.0, color_after="#112233"):
    return {
        "font_family": {"before": "Calibri", "after": family_after},
        "font_size_pt": {"before": 12.0, "after": size_after},
        "bold": {"before": False, "after": False},
        "run_color": {"before": "#AABBCC", "after": color_after},
    }


def _morph_record(tags, typography=None):
    return {
        "kind": "MORPH",
        "tags": list(tags),
        "geometry": {"x": {"before": 1.0, "after": 1.0}, "y": {"before": 1.0, "after": 1.0},
                     "w": {"before": 2.0, "after": 2.0}, "h": {"before": 2.0, "after": 2.0}},
        "typography": typography if typography is not None else _typography(),
        "style": {"fill_color": {"before": None, "after": None}},
        "content": {"chars_before": 10, "chars_after": 9, "similarity": 0.9, "text_changed": True},
    }


def _removed_record():
    return {"kind": "REMOVED", "tags": ["STRUCTURE_REMOVE"]}


def _wrap(records_by_node):
    out = {}
    for node_id, record in records_by_node.items():
        out[node_id] = {"label": truth_label(record), "record": record}
    return out


def _op(op_name, node_id, value=None):
    return {"op": op_name, "node_id": node_id, "value": value}


def test_truth_label_mapping():
    assert truth_label(_morph_record(["TYPOGRAPHY_FONT_SIZE"])) == "RESIZE"
    assert truth_label(_morph_record(["GEOMETRY_RESIZE"])) == "RESIZE"
    assert truth_label(_morph_record(["GEOMETRY_TRANSLATE"])) == "MOVE"
    assert truth_label(_morph_record(["TYPOGRAPHY_COLOR"])) == "RECOLOR"
    assert truth_label(_morph_record(["STYLE_FILL"])) == "RECOLOR"
    assert truth_label(_morph_record(["TYPOGRAPHY_FONT_FAMILY"])) == "RESTYLE"
    assert truth_label(_morph_record(["TYPOGRAPHY_WEIGHT"])) == "RESTYLE"
    assert truth_label(_morph_record(["CONTENT_REWRITE"])) == "RESTYLE"
    assert truth_label(_removed_record()) == "REMOVE"
    assert truth_label(_morph_record(["UNCHANGED"])) == "UNCHANGED"
    assert truth_label(_morph_record(["STRUCTURE_ADD", "UNCHANGED"])) == "UNCHANGED"


def test_operation_prf_hand_case():
    records = {
        "n1": _morph_record(["TYPOGRAPHY_FONT_FAMILY"]),
        "n2": _morph_record(["TYPOGRAPHY_WEIGHT"]),
        "n3": _removed_record(),
        "n4": _morph_record(["UNCHANGED"]),
    }
    truth = _wrap(records)
    preds = [
        _op("set_font_family", "n1", "Arial"),
        _op("set_font_family", "n2", "Verdana"),
        _op("set_font_size", "n4", 16.0),
    ]
    result = operation_prf(preds, truth)
    pc = result["per_class"]
    restyle = pc["RESTYLE"]
    assert abs(restyle["precision"] - 1.0) < 1e-9
    assert abs(restyle["recall"] - 1.0) < 1e-9
    assert abs(restyle["f1"] - 1.0) < 1e-9
    assert restyle["support"] == 2
    resize = pc["RESIZE"]
    assert abs(resize["precision"]) < 1e-9 and abs(resize["recall"]) < 1e-9
    assert abs(resize["f1"]) < 1e-9 and resize["support"] == 0
    recolor = pc["RECOLOR"]
    assert recolor["support"] == 0 and abs(recolor["f1"]) < 1e-9
    remove = pc["REMOVE"]
    assert remove["support"] == 1
    assert abs(remove["precision"]) < 1e-9 and abs(remove["recall"]) < 1e-9
    assert abs(remove["f1"]) < 1e-9
    assert result["overall"]["tp"] == 2
    assert result["overall"]["fp"] == 1
    assert result["overall"]["fn"] == 1
    assert result["unsafe_fp_count"] == 1


def test_operation_prf_duplicate_and_unlabeled():
    records = {
        "m1": _morph_record(["TYPOGRAPHY_FONT_FAMILY"]),
        "m2": _removed_record(),
    }
    truth = _wrap(records)
    preds = [
        _op("set_font_family", "m1", "Arial"),
        _op("set_font_family", "m1", "Arial"),
        _op("set_font_size", "zz_unknown", 18.0),
        _op("remove_node", "m2", None),
    ]
    result = operation_prf(preds, truth)
    restyle = result["per_class"]["RESTYLE"]
    assert abs(restyle["precision"] - 0.5) < 1e-9
    assert abs(restyle["recall"] - 1.0) < 1e-9
    assert restyle["support"] == 1
    resize = result["per_class"]["RESIZE"]
    assert abs(resize["precision"]) < 1e-9 and resize["support"] == 0
    remove = result["per_class"]["REMOVE"]
    assert abs(remove["precision"] - 1.0) < 1e-9 and abs(remove["recall"] - 1.0) < 1e-9
    assert result["overall"]["tp"] == 2
    assert result["overall"]["fp"] == 2
    assert result["overall"]["fn"] == 0
    assert result["overall"]["support_total"] == 2
    assert result["unsafe_fp_count"] == 1


def test_property_rates_exact():
    records = {
        "fam1": _morph_record(["TYPOGRAPHY_FONT_FAMILY"], _typography(family_after="Arial")),
        "fam2": _morph_record(["TYPOGRAPHY_FONT_FAMILY"], _typography(family_after="Verdana")),
        "sz1": _morph_record(["TYPOGRAPHY_FONT_SIZE"], _typography(size_after=14.0)),
        "sz2": _morph_record(["TYPOGRAPHY_FONT_SIZE"], _typography(size_after=15.0)),
        "col1": _morph_record(["TYPOGRAPHY_COLOR"], _typography(color_after="#112233")),
        "col2": _morph_record(["TYPOGRAPHY_COLOR"], _typography(color_after="#000000")),
    }
    truth = _wrap(records)
    preds = [
        _op("set_font_family", "fam1", "arial"),
        _op("set_font_family", "fam2", "Helvetica"),
        _op("set_font_size", "sz1", 16.0),
        _op("set_font_size", "sz2", 13.0),
        _op("set_run_color", "col1", "#112233"),
        _op("set_run_color", "col2", "#FFFFFF"),
    ]
    props = property_accuracy(preds, truth)
    assert abs(props["font_family_exact_match_rate"] - 0.5) < 1e-9
    assert abs(props["font_size_mae_pt"] - 2.0) < 1e-9
    assert abs(props["font_color_match_rate"] - 0.5) < 1e-9
    assert props["fill_color_match_rate"] is None
    assert props["geometry_position_error"] is None
    assert props["geometry_size_error"] is None

    empty = property_accuracy([], {})
    assert empty["font_family_exact_match_rate"] is None
    assert empty["font_size_mae_pt"] is None
    assert empty["font_color_match_rate"] is None
    assert empty["fill_color_match_rate"] is None


def test_safety_counters_crafted():
    plan = {
        "node_plan_approved": [
            _op("remove_node", "a"),
            _op("move_node", "b"),
            _op("set_font_family", "c", "Arial"),
        ],
        "node_plan_rejected": [
            _op("move_node", "d"),
            _op("add_node", "e"),
            _op("set_font_size", "f", 16.0),
            _op("set_run_color", "g", "#112233"),
            _op("set_font_size", "h", 14.0),
            _op("add_node", "i"),
        ],
    }
    reasons = [
        "operation_class_blocked_pending_reliable_predictor",
        "operation_class_blocked_pending_reliable_predictor",
        "preserve_by_default",
        "below_min_confidence",
        "stale_before_value",
        "missing_before_value",
    ]
    for op, reason in zip(plan["node_plan_rejected"], reasons):
        op["vet_reason"] = reason
    counters = safety_counters(plan)
    assert counters["unsafe_auto_apply_count"] == 2
    assert counters["incorrect_destructive_operations"] == 0
    assert counters["fallback_preserve_count"] == 2
    assert counters["blocked_move_count"] == 1
    assert counters["blocked_add_count"] == 1
    assert counters["stale_operation_rejections"] == 1
    assert counters["total_approved"] == 3
    assert counters["total_rejected"] == 6

    truth = _wrap({"c": _morph_record(["UNCHANGED"]), "a": _removed_record()})
    assert unsafe_with_truth(plan["node_plan_approved"], truth) == 1
    assert unsafe_with_truth([], truth) == 0
    assert unsafe_with_truth([_op("set_font_family", "unknown_node")], truth) == 0


def test_slide_scores_edge_cases():
    truth = _wrap({
        "s1": _morph_record(["TYPOGRAPHY_FONT_FAMILY"]),
        "s2": _morph_record(["UNCHANGED"]),
        "s3": _removed_record(),
    })
    plan = {"node_plan_approved": [_op("set_font_family", "s1", "Arial"), _op("set_run_color", "s9", "#112233")]}

    empty = slide_scores(plan, truth, [])
    assert empty["nodes_total"] == 0
    assert empty["nodes_labeled"] == 0
    assert empty["correct_nodes"] == 0
    assert empty["expected_operations"] == 0
    assert empty["executed_correct"] == 0
    assert empty["node_accuracy"] == 0.0
    assert empty["op_precision_proxy"] == 0.0

    single = slide_scores(plan, truth, ["s1"])
    assert single["nodes_labeled"] == 1
    assert single["expected_operations"] == 1
    assert single["executed_correct"] == 1
    assert single["correct_nodes"] == 1
    assert abs(single["node_accuracy"] - 1.0) < 1e-9
    assert abs(single["op_precision_proxy"] - 1.0) < 1e-9

    unchanged = slide_scores({"node_plan_approved": []}, truth, ["s2"])
    assert unchanged["correct_nodes"] == 1
    assert unchanged["expected_operations"] == 0
    assert unchanged["executed_correct"] == 0
    assert abs(unchanged["node_accuracy"] - 1.0) < 1e-9

    mixed = slide_scores(plan, truth, ["s1", "s2", "s3"])
    assert mixed["nodes_labeled"] == 3
    assert mixed["expected_operations"] == 2
    assert mixed["executed_correct"] == 1
    assert mixed["correct_nodes"] == 2


def test_harness_end_to_end_limit2():
    out_path = Path(os.environ.get("TEMP", ".")) / "morphlite_eval_test_harness.json"
    if out_path.exists():
        out_path.unlink()
    summary = run_evaluation(limit_pairs=2, out_path=str(out_path))
    try:
        assert summary["pairs_evaluated"] >= 1
        pooled = summary["pooled_operation_prf"]
        assert set(pooled["per_class"].keys()) == set(CLASSES)
        assert isinstance(pooled["weak_class_macro_f1"], float)
        for key in (
            "mean_property_accuracy",
            "mean_safety_counters",
            "mean_slide_scores",
            "mean_operation_prf",
            "slides_evaluated",
        ):
            assert key in summary
        written = json.loads(out_path.read_text(encoding="utf-8"))
        assert "pooled_operation_prf" in written
        assert "pairs_evaluated" in written
    finally:
        if out_path.exists():
            out_path.unlink()


TESTS = [
    test_truth_label_mapping,
    test_operation_prf_hand_case,
    test_operation_prf_duplicate_and_unlabeled,
    test_property_rates_exact,
    test_safety_counters_crafted,
    test_slide_scores_edge_cases,
    test_harness_end_to_end_limit2,
]


def main() -> int:
    for test in TESTS:
        test()
        print(f"ok {test.__name__}")
    print("EVALUATION GATE PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
