"""Safety gate: conservative filtering of planned operations."""
from __future__ import annotations

MIN_APPLY_CONFIDENCE = 0.60

FORBIDDEN_OPS_UNTIL_PROVEN = {"move_node", "add_node"}


def vet(operation: dict) -> tuple[bool, str]:
    if operation.get("op") in FORBIDDEN_OPS_UNTIL_PROVEN:
        return False, "operation_class_blocked_pending_reliable_predictor"
    if operation.get("source") == "fallback_preserve":
        return False, "preserve_by_default"
    conf = operation.get("confidence", 0.0)
    if conf < MIN_APPLY_CONFIDENCE:
        return False, "below_min_confidence"
    before = operation.get("before")
    if "expected_before_check" in operation and operation["before"] != operation.get("expected_before"):
        return False, "stale_before_value"
    if before is None and operation.get("requires_before"):
        return False, "missing_before_value"
    return True, "ok"


def vet_plan(ops: list[dict]) -> tuple[list[dict], list[dict]]:
    approved, rejected = [], []
    for op in ops:
        ok, reason = vet(op)
        (approved if ok else rejected).append({**op, "vet_reason": reason} if not ok else op)
    return approved, rejected
