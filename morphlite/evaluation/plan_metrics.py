"""Plan-vs-truth operation classification metrics (pure functions, no IO)."""
from __future__ import annotations

OP_CLASS_MAP = {
    "set_font_family": "RESTYLE",
    "set_font_size": "RESIZE",
    "set_run_color": "RECOLOR",
    "remove_node": "REMOVE",
}

TRUTH_TAG_MAP = {
    "TYPOGRAPHY_FONT_FAMILY": "RESTYLE",
    "TYPOGRAPHY_WEIGHT": "RESTYLE",
    "CONTENT_REWRITE": "RESTYLE",
    "TYPOGRAPHY_FONT_SIZE": "RESIZE",
    "GEOMETRY_RESIZE": "RESIZE",
    "GEOMETRY_TRANSLATE": "MOVE",
    "TYPOGRAPHY_COLOR": "RECOLOR",
    "STYLE_FILL": "RECOLOR",
    "STRUCTURE_REMOVE": "REMOVE",
}

TRUTH_TAG_PRIORITY = (
    "TYPOGRAPHY_FONT_SIZE",
    "GEOMETRY_RESIZE",
    "GEOMETRY_TRANSLATE",
    "TYPOGRAPHY_COLOR",
    "STYLE_FILL",
    "TYPOGRAPHY_FONT_FAMILY",
    "TYPOGRAPHY_WEIGHT",
    "CONTENT_REWRITE",
)

CLASSES = ("RESTYLE", "RESIZE", "RECOLOR", "REMOVE")

UNCHANGED = "UNCHANGED"


def truth_label(record: dict) -> str:
    if record.get("kind") == "REMOVED":
        return "REMOVE"
    tags = set(record.get("tags") or [])
    for tag in TRUTH_TAG_PRIORITY:
        if tag in tags:
            return TRUTH_TAG_MAP[tag]
    return UNCHANGED


def truth_node_id(record: dict):
    if record.get("kind") == "REMOVED":
        return record.get("node_id")
    return record.get("raw_node_id")


def entry_label(entry) -> str:
    """Accept a wrapped {"label","record"} entry or a raw transformation record."""
    if isinstance(entry, str):
        return entry
    if isinstance(entry, dict):
        if "label" in entry:
            return entry["label"]
        return truth_label(entry)
    return UNCHANGED


def _new_counts() -> dict:
    return {cls: {"tp": 0, "fp": 0, "fn": 0, "support": 0} for cls in CLASSES}


def operation_prf(pred_ops: list[dict], truth_by_node: dict) -> dict:
    counts = _new_counts()
    matched: set[tuple] = set()
    unsafe_fp = 0
    predicted = 0
    for op in pred_ops or []:
        cls = OP_CLASS_MAP.get(op.get("op"))
        if cls is None:
            continue
        predicted += 1
        node_id = op.get("node_id")
        entry = (truth_by_node or {}).get(node_id)
        label = entry_label(entry) if entry is not None else None
        if label == cls and (node_id, cls) not in matched:
            matched.add((node_id, cls))
            counts[cls]["tp"] += 1
        else:
            counts[cls]["fp"] += 1
            if label is None or label == UNCHANGED:
                unsafe_fp += 1
    labeled_nodes = 0
    for node_id, entry in (truth_by_node or {}).items():
        label = entry_label(entry)
        if label not in counts:
            continue
        counts[label]["support"] += 1
        labeled_nodes += 1
        if (node_id, label) not in matched:
            counts[label]["fn"] += 1

    per_class = {}
    f1_values = []
    tp_total = fp_total = fn_total = support_total = 0
    for cls in CLASSES:
        c = counts[cls]
        precision = c["tp"] / (c["tp"] + c["fp"]) if (c["tp"] + c["fp"]) else 0.0
        recall = c["tp"] / (c["tp"] + c["fn"]) if (c["tp"] + c["fn"]) else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
        per_class[cls] = {
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
            "support": c["support"],
        }
        f1_values.append(f1)
        tp_total += c["tp"]
        fp_total += c["fp"]
        fn_total += c["fn"]
        support_total += c["support"]
    macro_f1 = sum(f1_values) / len(f1_values) if f1_values else 0.0
    return {
        "per_class": per_class,
        "weak_class_macro_f1": round(macro_f1, 4),
        "overall": {
            "tp": tp_total,
            "fp": fp_total,
            "fn": fn_total,
            "predicted_ops": predicted,
            "labeled_nodes": labeled_nodes,
            "support_total": support_total,
        },
        "unsafe_fp_count": unsafe_fp,
    }
