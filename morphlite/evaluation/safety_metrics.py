"""Safety counters over planner output (approved/rejected operation lists)."""
from __future__ import annotations

from .plan_metrics import OP_CLASS_MAP, entry_label

DESTRUCTIVE_CLASSES = frozenset({"MOVE", "REMOVE"})
_BLOCKED_MARKER = "operation_class_blocked"
_STALE_MARKER = "stale"
_PRESERVE_MARKERS = ("preserve", "below_min")


def safety_counters(plan: dict) -> dict:
    approved = plan.get("node_plan_approved") or []
    rejected = plan.get("node_plan_rejected") or []
    counters = {
        "unsafe_auto_apply_count": 0,
        "incorrect_destructive_operations": 0,
        "fallback_preserve_count": 0,
        "blocked_move_count": 0,
        "blocked_add_count": 0,
        "stale_operation_rejections": 0,
        "total_approved": len(approved),
        "total_rejected": len(rejected),
    }
    for op in approved:
        cls = OP_CLASS_MAP.get(op.get("op"))
        if cls is None and op.get("op") == "move_node":
            cls = "MOVE"
        if cls in DESTRUCTIVE_CLASSES:
            counters["unsafe_auto_apply_count"] += 1
    for op in rejected:
        reason = str(op.get("vet_reason") or "").lower()
        op_name = op.get("op")
        if any(marker in reason for marker in _PRESERVE_MARKERS):
            counters["fallback_preserve_count"] += 1
        if _BLOCKED_MARKER in reason and op_name == "move_node":
            counters["blocked_move_count"] += 1
        elif _BLOCKED_MARKER in reason and op_name == "add_node":
            counters["blocked_add_count"] += 1
        if _STALE_MARKER in reason:
            counters["stale_operation_rejections"] += 1
    return counters


def unsafe_with_truth(approved_ops: list[dict], truth_by_node: dict) -> int:
    count = 0
    for op in approved_ops or []:
        entry = (truth_by_node or {}).get(op.get("node_id"))
        if entry is None:
            continue
        if entry_label(entry) == "UNCHANGED":
            count += 1
    return count
