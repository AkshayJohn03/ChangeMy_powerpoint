"""Derive the versioned learned-rules artifact from validated transformation data.

Inputs (produced by earlier pipeline stages):
    data/pairs/transformation_records.jsonl
    data/metadata/CHROME_TAXONOMY.json

Output:
    data/metadata/LEARNED_RULES.json

    python -m morphlite.rules.learn
"""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from .. import config

PAIRS_DIR = config.PAIRS_DIR
MIN_SIZE_SUPPORT = 3
MIN_FAMILY_SUPPORT = 3


def learn_font_rules(records: list[dict]) -> dict:
    family_changes: Counter = Counter()
    size_changes: Counter = Counter()
    color_changes: Counter = Counter()
    family_totals: Counter = Counter()

    for r in records:
        if r["kind"] != "MORPH":
            continue
        t = r["typography"]
        ff, fs, rc = t["font_family"], t["font_size_pt"], t["run_color"]
        if ff["before"] and ff["after"]:
            family_totals[ff["before"]] += 1
            if ff["before"] != ff["after"]:
                family_changes[(ff["before"], ff["after"])] += 1
        if fs["before"] and fs["after"] and abs(fs["before"] - fs["after"]) >= 0.75:
            size_changes[(round(fs["before"], 2), round(fs["after"], 2))] += 1
        if rc["before"] and rc["after"] and rc["before"] != rc["after"]:
            color_changes[(rc["before"], rc["after"])] += 1

    best_family: dict[str, tuple[str, int]] = {}
    brand_sources = {"roboto", "arial", "times new roman"}
    for (before, after), support in family_changes.items():
        if support < MIN_FAMILY_SUPPORT:
            continue
        if before in brand_sources or after.startswith("+"):
            continue
        total_seen = family_totals.get(before, 0)
        if total_seen and support / total_seen < 0.5:
            continue
        cur = best_family.get(before)
        if cur is None or support > cur[1]:
            best_family[before] = (after, support)

    best_size: dict[float, dict] = {}
    grouped: dict[float, Counter] = defaultdict(Counter)
    for (before, after), support in size_changes.items():
        if support >= MIN_SIZE_SUPPORT:
            grouped[before][after] += support
    for before, votes in grouped.items():
        after, support = votes.most_common(1)[0]
        total = sum(votes.values())
        best_size[before] = {
            "to": after,
            "support": support,
            "votes": dict(votes),
            "confidence": round(support / total, 3),
        }

    return {
        "font_family_map": {k: {"to": v[0], "support": v[1]} for k, v in sorted(best_family.items())},
        "font_size_map": {str(k): v for k, v in sorted(best_size.items())},
        "font_size_grid": [9, 10, 10.5, 11, 12, 14, 18, 24, 28, 32, 36, 40],
        "run_color_map": {
            f"{b}->{a}": support for (b, a), support in color_changes.most_common(30)
        },
        "family_change_totals": dict(family_totals.most_common(15)),
    }


def learn_chrome_rules() -> dict:
    swaps: dict[str, Counter] = defaultdict(Counter)
    bg_actions: Counter = Counter()
    pair_count = 0
    diff_path = PAIRS_DIR / "chrome_diff.jsonl"
    with open(diff_path, encoding="utf-8") as fh:
        for line in fh:
            row = json.loads(line)
            pair_count += 1
            for s in row.get("layout_swaps", []):
                swaps[str(s["before"])][str(s["after"])] += 1
            for b in row.get("background_changes", []):
                bg_actions[f"{b['before']}->{b['after']}"] += 1

    targets: Counter = Counter()
    for votes in swaps.values():
        for tgt, n in votes.items():
            targets[tgt] += n
    total = sum(targets.values())
    dominant_target, dominant_support = (targets.most_common(1)[0] if targets else ("", 0))
    layout_swap_map = {}
    for src, votes in swaps.items():
        tgt, support = votes.most_common(1)[0]
        layout_swap_map[src] = {"to": tgt, "support": support, "confidence": round(support / sum(votes.values()), 3)}
    return {
        "pairs_learned_from": pair_count,
        "target_layouts": dict(targets),
        "default_layout": dominant_target,
        "default_layout_share": round(dominant_support / total, 4) if total else 0.0,
        "layout_policy": "always_keep",
        "layout_policy_note": "remap intent is deck-level (REBUILD vs PRESERVE); per-layout voting loses to pure-keep 0.54 vs 0.86; intent classification deferred to ML layer",
        "layout_swap_map": layout_swap_map,
        "background_actions": dict(bg_actions),
        "clear_explicit_background": True,
    }


def main() -> None:
    records = []
    with open(PAIRS_DIR / "transformation_records.jsonl", encoding="utf-8") as fh:
        for line in fh:
            records.append(json.loads(line))

    ruleset = {
        "ruleset_version": "learned_v1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source_counts": {"morph_records": sum(1 for r in records if r["kind"] == "MORPH")},
        **learn_font_rules(records),
        **learn_chrome_rules(),
    }
    out = config.METADATA_DIR / "LEARNED_RULES.json"
    out.write_text(json.dumps(ruleset, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"written {out}")
    print(json.dumps({k: ruleset[k] for k in ("default_layout", "default_layout_share", "font_family_map")}, indent=1, ensure_ascii=False))
    sizes = {k: v["to"] for k, v in ruleset["font_size_map"].items()}
    print("size map:", sizes)


if __name__ == "__main__":
    main()
