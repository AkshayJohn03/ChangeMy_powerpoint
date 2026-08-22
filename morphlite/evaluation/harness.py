"""Evaluation harness: run the hybrid planner over validated pairs and score it.

    python -c "from morphlite.evaluation import harness; harness.run_evaluation(limit_pairs=5)"
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from .. import config
from ..inference.hybrid_planner import build_hybrid_plan
from .plan_metrics import operation_prf, truth_label, truth_node_id
from .property_metrics import property_accuracy
from .safety_metrics import safety_counters, unsafe_with_truth
from .slide_metrics import slide_scores

DEFAULT_OUT_PATH = config.METADATA_DIR / "EVALUATION_HARNESS.json"
VALIDATED_PAIRS_PATH = config.PAIRS_DIR / "validated_pairs.jsonl"
TRANSFORM_RECORDS_PATH = config.PAIRS_DIR / "transformation_records.jsonl"
AST_V2_MANIFEST_PATH = config.EXTRACTED_DIR / "ast_v2" / "extraction_manifest_v2.jsonl"

PROPERTY_KEYS = (
    "font_family_exact_match_rate",
    "font_size_mae_pt",
    "font_color_match_rate",
    "fill_color_match_rate",
    "geometry_position_error",
    "geometry_size_error",
)
SAFETY_KEYS = (
    "unsafe_auto_apply_count",
    "incorrect_destructive_operations",
    "fallback_preserve_count",
    "blocked_move_count",
    "blocked_add_count",
    "stale_operation_rejections",
    "total_approved",
    "total_rejected",
)


def build_truth_index(records_path: str | Path | None = None) -> dict[str, dict[str, dict]]:
    """Group transformation records by deck_pair_id -> node_id once."""
    path = Path(records_path) if records_path else TRANSFORM_RECORDS_PATH
    index: dict[str, dict[str, dict]] = {}
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            pair_id = record.get("deck_pair_id")
            node_id = truth_node_id(record)
            if not pair_id or not node_id:
                continue
            index.setdefault(pair_id, {})[node_id] = {
                "label": truth_label(record),
                "record": record,
            }
    return index


def load_rules() -> dict:
    return json.loads((config.METADATA_DIR / "LEARNED_RULES.json").read_text(encoding="utf-8"))


def load_ast_manifest() -> dict[str, dict]:
    manifest: dict[str, dict] = {}
    with open(AST_V2_MANIFEST_PATH, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            manifest[row["deck_id"]] = row
    return manifest


def _flatten_node_ids(nodes: list) -> list[str]:
    out: list[str] = []
    stack = list(nodes)
    while stack:
        node = stack.pop(0)
        nid = node.get("id")
        if nid:
            out.append(nid)
        stack.extend(node.get("children") or [])
    return out


def _mean_of_dicts(dicts: list[dict]) -> dict:
    def merge(acc: dict, payload: dict) -> None:
        for key, value in payload.items():
            if isinstance(value, dict):
                merge(acc.setdefault(key, {}), value)
            elif isinstance(value, (int, float)) and not isinstance(value, bool):
                acc.setdefault(key, []).append(value)

    def finalize(part: dict) -> dict:
        out = {}
        for key, value in part.items():
            if isinstance(value, dict):
                out[key] = finalize(value)
            else:
                out[key] = round(sum(value) / len(value), 6) if value else None
        return out

    acc: dict = {}
    for payload in dicts or []:
        merge(acc, payload)
    return finalize(acc)


def evaluate_pair(pair: dict, deck_ast: dict, chrome: dict, rules: dict, truth_by_node: dict) -> dict:
    plan = build_hybrid_plan(deck_ast, chrome, rules, models=None)
    approved = plan.get("node_plan_approved") or []
    prf = operation_prf(approved, truth_by_node)
    props = property_accuracy(approved, truth_by_node)
    counters = safety_counters(plan)
    counters["incorrect_destructive_operations"] = unsafe_with_truth(approved, truth_by_node)

    mapped_slide_ids = {m.get("raw_slide_id") for m in (pair.get("slide_mappings") or [])}
    slide_results = []
    for slide in deck_ast.get("slides") or []:
        if slide.get("slide_id") not in mapped_slide_ids:
            continue
        node_ids = _flatten_node_ids(slide.get("nodes") or [])
        slide_results.append(slide_scores(plan, truth_by_node, node_ids))

    return {
        "deck_pair_id": pair.get("deck_pair_id"),
        "n_slides_scored": len(slide_results),
        "operation_prf": prf,
        "property_accuracy": props,
        "safety_counters": counters,
        "slide_scores_mean": _mean_of_dicts(slide_results),
        "pred_ops_approved": approved,
    }


def run_evaluation(limit_pairs: int | None = None, out_path: str | Path | None = None) -> dict:
    rules = load_rules()
    manifest = load_ast_manifest()
    truth_index = build_truth_index()

    results = []
    pooled_preds: list[dict] = []
    pooled_truth: dict[str, dict] = {}
    skipped = 0
    with open(VALIDATED_PAIRS_PATH, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            if limit_pairs is not None and len(results) >= limit_pairs:
                break
            pair = json.loads(line)
            entry = manifest.get(pair.get("raw_deck"))
            if entry is None:
                skipped += 1
                continue
            ast_path = Path(entry["ast_v2_path"])
            chrome_path = config.EXTRACTED_DIR / "chrome" / f"{pair['raw_deck']}.json"
            if not ast_path.exists() or not chrome_path.exists():
                skipped += 1
                continue
            deck_ast = json.loads(ast_path.read_text(encoding="utf-8"))
            chrome = json.loads(chrome_path.read_text(encoding="utf-8"))
            truth_by_node = truth_index.get(pair.get("deck_pair_id"), {})
            result = evaluate_pair(pair, deck_ast, chrome, rules, truth_by_node)
            results.append(result)
            pooled_preds.extend(result.pop("pred_ops_approved"))
            pooled_truth.update(truth_by_node)

    pooled_prf = operation_prf(pooled_preds, pooled_truth)
    summary = {
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "pairs_evaluated": len(results),
        "pairs_skipped": skipped,
        "slides_evaluated": sum(r["n_slides_scored"] for r in results),
        "pooled_operation_prf": pooled_prf,
        "mean_operation_prf": _mean_of_dicts([r["operation_prf"] for r in results]),
        "mean_property_accuracy": _mean_of_dicts([r["property_accuracy"] for r in results]),
        "mean_safety_counters": _mean_of_dicts([r["safety_counters"] for r in results]),
        "mean_slide_scores": _mean_of_dicts([r["slide_scores_mean"] for r in results]),
        "per_pair": [
            {
                "deck_pair_id": r["deck_pair_id"],
                "weak_class_macro_f1": r["operation_prf"]["weak_class_macro_f1"],
                "total_approved": r["safety_counters"]["total_approved"],
                "total_rejected": r["safety_counters"]["total_rejected"],
            }
            for r in results
        ],
    }

    target = Path(out_path) if out_path else DEFAULT_OUT_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    per_class = pooled_prf.get("per_class", {})
    props = summary["mean_property_accuracy"]
    safety = summary["mean_safety_counters"]
    print(f"EVALUATION SUMMARY pairs={summary['pairs_evaluated']} slides={summary['slides_evaluated']}")
    print(f"weak_class_macro_f1={pooled_prf.get('weak_class_macro_f1')}")
    print(
        "per_class_f1="
        + " ".join(f"{cls}={per_class.get(cls, {}).get('f1')}" for cls in ("RESTYLE", "RESIZE", "RECOLOR", "REMOVE"))
    )
    print("property_rates=" + " ".join(f"{k}={props.get(k)}" for k in PROPERTY_KEYS))
    print("safety_totals=" + " ".join(f"{k}={round(float(safety.get(k) or 0), 3)}" for k in SAFETY_KEYS))
    return summary


if __name__ == "__main__":
    run_evaluation()
