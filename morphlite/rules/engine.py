"""Deterministic transformation engine.

Pure function core (no IO) so the same plan builder serves:
    - the deterministic baseline evaluation
    - the future API route (POST /api/plan_transformation)
    - training-data generation for the later ML layers

    python -m morphlite.rules.engine <deck_json> <chrome_json> [out.json]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from . import brand_tokens as bt

PLAN_VERSION = "1.0.0"


def _dominant_props(node: dict) -> dict:
    fams, sizes, colors = {}, {}, {}
    for p in node.get("paragraphs") or []:
        for r in p.get("runs") or []:
            if r.get("font_family"):
                f = r["font_family"].lower()
                fams[f] = fams.get(f, 0) + 1
            if r.get("font_size_pt"):
                s = round(r["font_size_pt"], 2)
                sizes[s] = sizes.get(s, 0) + 1
            if r.get("color"):
                c = r["color"].upper()
                colors[c] = colors.get(c, 0) + 1

    def pick(d):
        return max(d, key=d.get) if d else None

    return {"font_family": pick(fams), "font_size_pt": pick(sizes), "run_color": pick(colors)}


def _node_text(node: dict) -> str:
    return " ".join(p["text"] for p in node.get("paragraphs") or [])


def build_plan(deck: dict, chrome: dict, rules: dict) -> dict:
    swap_map = rules.get("layout_swap_map") or {}
    policy = rules.get("layout_policy", "always_keep")
    chrome_plan = []
    for slide in chrome.get("slides", []):
        raw_layout = slide.get("layout")
        swap = swap_map.get(raw_layout or "") if policy == "keep_unless_known_swap_source" else None
        target = swap["to"] if swap else raw_layout
        confidence = swap["confidence"] if swap else 0.90
        raw_bg = slide.get("background")
        has_explicit_bg = bool(raw_bg and raw_bg.get("type") in ("solid", "picture"))
        chrome_plan.append(
            {
                "slide_index": slide["index"],
                "raw_layout": raw_layout,
                "target_layout": target,
                "layout_action": "remap" if swap else "keep",
                "clear_background": has_explicit_bg,
                "confidence": confidence,
            }
        )

    family_map = {k.lower(): v["to"] for k, v in (rules.get("font_family_map") or {}).items()}
    size_map = {}
    for k, v in (rules.get("font_size_map") or {}).items():
        try:
            size_map[round(float(k), 2)] = v
        except ValueError:
            continue
    grid = {float(g) for g in rules.get("font_size_grid") or []}
    color_map = {}
    for pair_key in rules.get("run_color_map") or {}:
        try:
            before, after = pair_key.split("->")
        except ValueError:
            continue
        color_map.setdefault(before.upper(), after)

    node_plan = []
    ops_by_type = {}

    def add_op(op: str, node_id: str, before, value, basis: str, confidence: float):
        node_plan.append(
            {
                "op": op,
                "node_id": node_id,
                "before": before,
                "value": value,
                "basis": basis,
                "confidence": round(confidence, 3),
            }
        )
        ops_by_type[op] = ops_by_type.get(op, 0) + 1

    for slide in deck.get("slides", []):
        for node in _iter_nodes(slide.get("nodes", [])):
            nid = node["id"]
            text = _node_text(node).strip()
            low = text.lower()

            if text and any(marker in low for marker in bt.GUIDANCE_TEXT_MARKERS):
                add_op("remove_node", nid, text[:60], None, "rule:guidance_text", 0.99)
                continue

            props = _dominant_props(node)

            fam = props["font_family"]
            if fam and fam in family_map:
                target_fam = family_map[fam]
                entry = rules["font_family_map"][fam]
                add_op("set_font_family", nid, fam, target_fam, "rule:font_family", min(0.95, entry["support"] / (entry["support"] + 5)))

            size = props["font_size_pt"]
            if size is not None and size in size_map and size not in grid:
                entry = size_map[size]
                if entry.get("confidence", 0) >= 0.7:
                    add_op("set_font_size", nid, size, entry["to"], "rule:font_size_offgrid", entry["confidence"])

            color = props["run_color"]
            if color and color in bt.LEGACY_GOLD_VARIANTS:
                add_op("set_run_color", nid, color, bt.BRAND_COLORS["gold"], "rule:legacy_gold", 0.9)
            elif color and color in bt.LEGACY_AQUA_VARIANTS:
                add_op("set_run_color", nid, color, bt.BRAND_COLORS["aqua"], "rule:legacy_aqua", 0.8)

    return {
        "plan_version": PLAN_VERSION,
        "ruleset": rules.get("ruleset_version"),
        "deck_id": deck["deck_id"],
        "chrome_plan": chrome_plan,
        "node_plan": node_plan,
        "summary": {"ops_by_type": ops_by_type, "slides": len(chrome_plan), "nodes_touched": len(node_plan)},
    }


def _iter_nodes(nodes):
    stack = list(nodes)
    while stack:
        n = stack.pop(0)
        yield n
        stack.extend(n.get("children") or [])


def main() -> None:
    deck_path = Path(sys.argv[1])
    chrome_path = Path(sys.argv[2])
    out_path = Path(sys.argv[3]) if len(sys.argv) > 3 else None
    rules_path = config_path = Path(__file__).resolve().parents[2] / "data" / "metadata" / "LEARNED_RULES.json"
    rules = json.loads(rules_path.read_text(encoding="utf-8"))
    plan = build_plan(json.loads(deck_path.read_text(encoding="utf-8")), json.loads(chrome_path.read_text(encoding="utf-8")), rules)
    rendered = json.dumps(plan, indent=1, ensure_ascii=False)
    if out_path:
        out_path.write_text(rendered, encoding="utf-8")
        print(f"written {out_path}")
    else:
        print(rendered[:2000])


if __name__ == "__main__":
    main()
