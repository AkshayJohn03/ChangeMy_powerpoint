"""Day-one evaluation instrumentation for the deterministic baseline.

For every golden deck pair:
    1. run the rules engine on the RAW deck (AST + chrome)
    2. score the produced plan against the ACTUAL branded deck:
         - layout assignment accuracy
         - background-clear precision/recall
         - node-op precision / recall / F1 per op type (value-checked)

Artifacts double as future training data:
    data/pairs/baseline_plans/<deck_pair_id>.json   engine predictions
    data/metadata/BASELINE_EVAL.json                metrics

    python -m morphlite.training.evaluate_baseline
"""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

from .. import config
from ..rules import engine as rule_engine
from .chrome_diff import bg_desc, slide_index

PAIRS_DIR = config.PAIRS_DIR
AST_ROOT = config.EXTRACTED_DIR / "ast"
CHROME_ROOT = config.EXTRACTED_DIR / "chrome"


def _load_json(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


def load_truth_ops() -> dict[str, dict]:
    truth = {}
    with open(PAIRS_DIR / "transformation_records.jsonl", encoding="utf-8") as fh:
        for line in fh:
            r = json.loads(line)
            if r["kind"] == "MORPH":
                entry = truth.setdefault(r["raw_node_id"], {"tags": set(), "after": {}})
                entry["tags"].update(r["tags"])
                t = r["typography"]
                if "TYPOGRAPHY_FONT_FAMILY" in r["tags"]:
                    entry["after"]["font_family"] = t["font_family"]["after"]
                if "TYPOGRAPHY_FONT_SIZE" in r["tags"]:
                    entry["after"]["font_size_pt"] = t["font_size_pt"]["after"]
                if "TYPOGRAPHY_COLOR" in r["tags"]:
                    entry["after"]["run_color"] = t["run_color"]["after"]
            elif r["kind"] == "REMOVED":
                truth.setdefault(r["node_id"], {"tags": set(), "after": {}})["tags"].add("STRUCTURE_REMOVE")
            elif r["kind"] == "ADDED":
                pass
    return truth


OP_TO_TAG = {
    "set_font_family": "TYPOGRAPHY_FONT_FAMILY",
    "set_font_size": "TYPOGRAPHY_FONT_SIZE",
    "set_run_color": "TYPOGRAPHY_COLOR",
    "remove_node": "STRUCTURE_REMOVE",
}

VALUE_KEY = {"set_font_family": ("after", "font_family"), "set_font_size": ("after", "font_size_pt"), "set_run_color": ("after", "run_color")}


def main() -> None:
    rules = _load_json(config.METADATA_DIR / "LEARNED_RULES.json")
    decks = {}
    with open(AST_ROOT / "extraction_manifest.jsonl", encoding="utf-8") as fh:
        for line in fh:
            rec = json.loads(line)
            decks[rec["deck_id"]] = rec

    plans_dir = PAIRS_DIR / "baseline_plans"
    plans_dir.mkdir(parents=True, exist_ok=True)

    truth_ops = load_truth_ops()

    layout_hits = layout_total = 0
    bg_pred_pos = bg_tp = bg_truth_pos = 0
    op_stats: dict[str, Counter] = defaultdict(lambda: Counter())
    confusion: Counter = Counter()
    per_pair = []

    with open(PAIRS_DIR / "validated_pairs.jsonl", encoding="utf-8") as fh:
        pairs = [json.loads(line) for line in fh]

    for v in pairs:
        raw_deck = _load_json(Path(decks[v["raw_deck"]]["ast_path"]))
        raw_chrome = _load_json(CHROME_ROOT / f"{v['raw_deck']}.json")
        bran_chrome = _load_json(CHROME_ROOT / f"{v['branded_deck']}.json")

        plan = rule_engine.build_plan(raw_deck, raw_chrome, rules)
        (plans_dir / f"{v['deck_pair_id']}.json").write_text(json.dumps(plan, indent=1, ensure_ascii=False), encoding="utf-8")

        pred_layout = {c["slide_index"]: c for c in plan["chrome_plan"]}
        pair_layout_hits = 0
        for sm in v["slide_mappings"]:
            ri, bi = slide_index(sm["raw_slide_id"]), slide_index(sm["branded_slide_id"])
            pc = pred_layout.get(ri + 1)
            actual_layout = bran_chrome["slides"][bi].get("layout") if bi < len(bran_chrome["slides"]) else None
            layout_total += 1
            if pc and pc["target_layout"] == actual_layout:
                layout_hits += 1
                pair_layout_hits += 1
            else:
                confusion[(str(pc["target_layout"]) if pc else "?", str(actual_layout))] += 1

            raw_bg = raw_chrome["slides"][ri].get("background") if ri < len(raw_chrome["slides"]) else None
            bran_bg = bran_chrome["slides"][bi].get("background") if bi < len(bran_chrome["slides"]) else None
            raw_explicit = bool(raw_bg and raw_bg.get("type") in ("solid", "picture"))
            actual_cleared = bool(raw_explicit) and bg_desc(bran_bg).split(":")[0] == "absent"
            predicted_clear = bool(pc and pc["clear_background"])
            if raw_explicit:
                bg_truth_pos += 1
                if predicted_clear:
                    bg_pred_pos += 1
                    if actual_cleared:
                        bg_tp += 1

        touched_nodes = {op["node_id"]: op for op in plan["node_plan"]}
        for nid, op in touched_nodes.items():
            tag = OP_TO_TAG[op["op"]]
            truth = truth_ops.get(nid)
            hit = bool(truth and tag in truth["tags"])
            value_ok = False
            if hit and op["op"] in VALUE_KEY:
                _, key = VALUE_KEY[op["op"]]
                actual_val = truth.get("after", {}).get(key)
                value_ok = actual_val is not None and str(actual_val).lower() == str(op["value"]).lower()
            op_stats[op["op"]]["predicted"] += 1
            if hit:
                op_stats[op["op"]]["tag_hit"] += 1
                if value_ok or op["op"] == "remove_node":
                    op_stats[op["op"]]["value_correct"] += 1

        for nid, truth in truth_ops.items():
            if not nid.startswith(v["raw_deck"]):
                continue
            for tag in truth["tags"]:
                mapped_op = next((o for o, t in OP_TO_TAG.items() if t == tag), None)
                if mapped_op:
                    op_stats[mapped_op]["truth"] += 1
                    if nid in touched_nodes:
                        op_stats[mapped_op]["truth_covered"] += 1

        per_pair.append(
            {
                "deck_pair_id": v["deck_pair_id"],
                "name_key": v["name_key"],
                "status": v["status"],
                "layout_accuracy": round(pair_layout_hits / max(len(v["slide_mappings"]), 1), 4),
                "ops_issued": len(plan["node_plan"]),
            }
        )

    def prf(c: Counter):
        p = c["tag_hit"] / c["predicted"] if c["predicted"] else 0.0
        r = c["truth_covered"] / c["truth"] if c["truth"] else 0.0
        f = 2 * p * r / (p + r) if p + r else 0.0
        return {"precision": round(p, 4), "recall": round(r, 4), "f1": round(f, 4),
                "value_precision": round(c["value_correct"] / c["predicted"], 4) if c["predicted"] else 0.0,
                "predicted": c["predicted"], "truth": c["truth"]}

    report = {
        "ruleset": rules.get("ruleset_version"),
        "pairs_evaluated": len(pairs),
        "layout_top1_accuracy": round(layout_hits / max(layout_total, 1), 4),
        "layout_confusion_top": [{"pred": k[0], "actual": k[1], "n": n} for k, n in confusion.most_common(5)],
        "bg_clear": {
            "precision": round(bg_tp / bg_pred_pos, 4) if bg_pred_pos else None,
            "recall": round(bg_tp / bg_truth_pos, 4) if bg_truth_pos else None,
            "raw_slides_with_bg": bg_truth_pos,
        },
        "node_ops": {op: prf(c) for op, c in sorted(op_stats.items())},
        "per_pair_worst": sorted(per_pair, key=lambda x: x["layout_accuracy"])[:5],
    }
    (config.METADATA_DIR / "BASELINE_EVAL.json").write_text(json.dumps(report, indent=1), encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("ruleset", "pairs_evaluated", "layout_top1_accuracy", "bg_clear", "node_ops")}, indent=2))


if __name__ == "__main__":
    main()
