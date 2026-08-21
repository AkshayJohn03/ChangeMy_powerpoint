"""Chrome-level transformation analysis over validated deck pairs.

Quantifies where branding is actually applied:
    - layout swaps            raw_layout -> branded_layout
    - background transforms   raw_bg -> branded_bg
    - theme palette changes
    - <p:style> theme-ref adoption

    python -m morphlite.training.chrome_diff
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from .. import config

CHROME_ROOT = config.EXTRACTED_DIR / "chrome"
PAIRS_DIR = config.PAIRS_DIR


def load_chrome(deck_id: str) -> dict:
    return json.loads((CHROME_ROOT / f"{deck_id}.json").read_text(encoding="utf-8"))


def slide_index(slide_id: str) -> int:
    return int(slide_id.rsplit("__s", 1)[1]) - 1


def bg_desc(bg: dict | None) -> str:
    if not bg:
        return "absent"
    if bg.get("type") == "solid":
        return f"solid:{(bg.get('color') or '?').upper()}"
    if bg.get("type") == "picture":
        return f"pic:{bg.get('image_md5_8')}"
    return bg.get("type") or "absent"


def main() -> None:
    layout_swaps: Counter = Counter()
    bg_transforms: Counter = Counter()
    pair_rows = []
    theme_stats = {"identical": 0, "changed": 0}
    ref_adoption = {"raw_with_refs": 0, "branded_with_refs": 0, "slides": 0}

    with open(PAIRS_DIR / "validated_pairs.jsonl", encoding="utf-8") as fh:
        pairs = [json.loads(line) for line in fh]

    for v in pairs:
        raw_c, bran_c = load_chrome(v["raw_deck"]), load_chrome(v["branded_deck"])
        themes_same = raw_c["themes"] == bran_c["themes"]
        theme_stats["identical" if themes_same else "changed"] += 1

        swaps, bgs = [], []
        for sm in v["slide_mappings"]:
            ri, bi = slide_index(sm["raw_slide_id"]), slide_index(sm["branded_slide_id"])
            rs = raw_c["slides"][ri] if ri < len(raw_c["slides"]) else {}
            bs = bran_c["slides"][bi] if bi < len(bran_c["slides"]) else {}

            rl, bl = rs.get("layout"), bs.get("layout")
            if rl != bl:
                layout_swaps[(str(rl), str(bl))] += 1
                swaps.append({"slide": sm["pair_id"], "before": rl, "after": bl})

            rd, bd = bg_desc(rs.get("background")), bg_desc(bs.get("background"))
            if rd != bd:
                bg_transforms[(rd.split(":")[0], bd.split(":")[0])] += 1
                bgs.append({"slide": sm["pair_id"], "before": rd, "after": bd})

            ref_adoption["slides"] += 1
            if rs.get("style_refs"):
                ref_adoption["raw_with_refs"] += 1
            if bs.get("style_refs"):
                ref_adoption["branded_with_refs"] += 1

        pair_rows.append(
            {
                "deck_pair_id": v["deck_pair_id"],
                "name_key": v["name_key"],
                "status": v["status"],
                "themes_identical": themes_same,
                "layout_swaps": swaps,
                "background_changes": bgs,
            }
        )

    def top_rules(counter, limit=25):
        return [
            {"from": a, "to": b, "support": n}
            for (a, b), n in counter.most_common(limit)
        ]

    taxonomy = {
        "golden_pairs_analyzed": len(pairs),
        "themes": theme_stats,
        "layout_swap_rules": top_rules(layout_swaps),
        "background_transform_rules": top_rules(bg_transforms),
        "style_ref_adoption": ref_adoption,
        "distinct_layouts_raw": len({k[0] for k in layout_swaps}),
        "distinct_layouts_branded": len({k[1] for k in layout_swaps}),
    }
    (config.METADATA_DIR / "CHROME_TAXONOMY.json").write_text(json.dumps(taxonomy, indent=1), encoding="utf-8")
    with open(PAIRS_DIR / "chrome_diff.jsonl", "w", encoding="utf-8") as fh:
        for r in pair_rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(json.dumps(taxonomy, indent=2)[:3000])


if __name__ == "__main__":
    main()
