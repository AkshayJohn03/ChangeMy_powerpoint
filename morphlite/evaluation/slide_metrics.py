"""Per-slide plan correctness proxies."""
from __future__ import annotations

from .plan_metrics import OP_CLASS_MAP, entry_label


def slide_scores(plan: dict, truth_by_node: dict, slide_node_ids: list[str]) -> dict:
    ids = list(slide_node_ids or [])
    id_set = set(ids)
    preds_by_node: dict[str, list[dict]] = {}
    pred_ops_on_slide = 0
    for op in plan.get("node_plan_approved") or []:
        node_id = op.get("node_id")
        if node_id in id_set:
            preds_by_node.setdefault(node_id, []).append(op)
            pred_ops_on_slide += 1

    correct_nodes = 0
    executed_correct = 0
    expected_operations = 0
    nodes_labeled = 0
    for node_id in ids:
        ops = preds_by_node.get(node_id) or []
        pred_classes = [OP_CLASS_MAP.get(o.get("op")) for o in ops]
        pred_classes = [c for c in pred_classes if c]
        entry = (truth_by_node or {}).get(node_id)
        if entry is None:
            continue
        nodes_labeled += 1
        label = entry_label(entry)
        if label == "UNCHANGED":
            if not pred_classes:
                correct_nodes += 1
            continue
        expected_operations += 1
        if label in pred_classes:
            correct_nodes += 1
            executed_correct += 1

    return {
        "nodes_total": len(ids),
        "nodes_labeled": nodes_labeled,
        "pred_ops_on_slide": pred_ops_on_slide,
        "correct_nodes": correct_nodes,
        "expected_operations": expected_operations,
        "executed_correct": executed_correct,
        "node_accuracy": round(correct_nodes / nodes_labeled, 6) if nodes_labeled else 0.0,
        "op_precision_proxy": round(executed_correct / pred_ops_on_slide, 6) if pred_ops_on_slide else 0.0,
    }
