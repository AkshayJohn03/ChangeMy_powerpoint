"""Property-level accuracy of planned values vs transformation-record truth."""
from __future__ import annotations

from .plan_metrics import entry_label


def _norm_text(value) -> str | None:
    if value is None:
        return None
    return str(value).strip().lower()


def _norm_color(value) -> str | None:
    if value is None:
        return None
    return str(value).strip().lstrip("#").upper()


def _truth_after(record: dict | None, group: str, field: str):
    if not record:
        return None
    payload = (record.get(group) or {}).get(field)
    if not isinstance(payload, dict):
        return None
    return payload.get("after")


def property_accuracy(pred_ops: list[dict], truth_by_node: dict) -> dict:
    fam_den = fam_hit = col_den = col_hit = fill_den = fill_hit = 0
    size_errors: list[float] = []
    for op in pred_ops or []:
        node_id = op.get("node_id")
        entry = (truth_by_node or {}).get(node_id)
        record = entry.get("record") if isinstance(entry, dict) else entry
        name = op.get("op")
        value = op.get("value")
        if name == "set_font_family":
            fam_den += 1
            after = _truth_after(record, "typography", "font_family")
            if _norm_text(after) is not None and _norm_text(after) == _norm_text(value):
                fam_hit += 1
        elif name == "set_font_size":
            if entry is not None and entry_label(entry) == "RESIZE":
                after = _truth_after(record, "typography", "font_size_pt")
                if isinstance(after, (int, float)) and isinstance(value, (int, float)):
                    size_errors.append(abs(float(value) - float(after)))
        elif name == "set_run_color":
            col_den += 1
            after = _truth_after(record, "typography", "run_color")
            if _norm_color(after) is not None and _norm_color(after) == _norm_color(value):
                col_hit += 1
        elif name == "set_fill_color":
            fill_den += 1
            after = _truth_after(record, "style", "fill_color")
            if _norm_color(after) is not None and _norm_color(after) == _norm_color(value):
                fill_hit += 1

    return {
        "font_family_exact_match_rate": (fam_hit / fam_den) if fam_den else None,
        "font_size_mae_pt": (sum(size_errors) / len(size_errors)) if size_errors else None,
        "font_color_match_rate": (col_hit / col_den) if col_den else None,
        "fill_color_match_rate": (fill_hit / fill_den) if fill_den else None,
        "geometry_position_error": None,
        "geometry_size_error": None,
        "geometry_note": "plan contains no geometry ops",
    }
