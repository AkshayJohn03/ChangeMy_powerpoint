"""Object-level node alignment between matched slide pairs.

Produces data/pairs/slide_alignments.jsonl where each record holds the
node correspondence for one aligned slide pair.

    python -m morphlite.training.pair_alignment
"""
from __future__ import annotations

import json
import math
from collections import defaultdict
from pathlib import Path

from .. import config
from ..ast import extractor
from . import textsim

PAIRS_DIR = config.PAIRS_DIR
AST_ROOT = config.EXTRACTED_DIR / "ast"

SCORE_FLOOR = 0.35
POS_WEIGHT_SCALE = 1.6


def centroid(node: dict) -> tuple[float, float] | None:
    b = node.get("bbox_norm") or {}
    if any(b.get(k) is None for k in ("x", "y", "w", "h")):
        return None
    return (b["x"] + b["w"] / 2, b["y"] + b["h"] / 2)


def area_norm(node: dict) -> float | None:
    b = node.get("bbox_norm") or {}
    if b.get("w") is None or b.get("h") is None:
        return None
    return abs(b["w"] * b["h"])


def dist(a, b) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def _score_pair(a: dict, b: dict) -> float | None:
    if a["type"] != b["type"]:
        return None
    ca, cb = centroid(a), centroid(b)
    pos = 1.0 - min(1.0, dist(ca, cb) * POS_WEIGHT_SCALE) if ca and cb else 0.30
    ta, tb = extractor.node_text(a), extractor.node_text(b)
    if ta or tb:
        return 0.78 * textsim.similarity(ta, tb) + 0.22 * pos
    sa, sb = area_norm(a), area_norm(b)
    if sa is None or sb is None or sa <= 0 or sb <= 0:
        return 0.5 * pos + 0.2
    ratio = max(sa, sb) / max(min(sa, sb), 1e-9)
    size_sim = math.exp(-math.log(ratio))
    return 0.45 * pos + 0.55 * size_sim


def align_slide(raw_nodes: list[dict], bran_nodes: list[dict]) -> dict:
    ra = extractor.flatten_nodes(raw_nodes)
    ba = extractor.flatten_nodes(bran_nodes)

    entries = []
    for i, a in enumerate(ra):
        for j, b in enumerate(ba):
            s = _score_pair(a, b)
            if s is not None and s >= 0.20:
                entries.append((s, i, j))
    entries.sort(key=lambda e: (-e[0], e[1], e[2]))

    used_a: set[int] = set()
    used_b: set[int] = set()
    matches = []
    for s, i, j in entries:
        if i in used_a or j in used_b:
            continue
        if s < SCORE_FLOOR:
            continue
        used_a.add(i)
        used_b.add(j)
        matches.append(
            {
                "raw_node_id": ra[i]["id"],
                "branded_node_id": ba[j]["id"],
                "node_type": ra[i]["type"],
                "confidence": round(s, 4),
            }
        )
    matches.sort(key=lambda m: m["raw_node_id"])
    return {
        "matches": matches,
        "unmatched_raw": [{"id": n["id"], "type": n["type"]} for k, n in enumerate(ra) if k not in used_a],
        "unmatched_branded": [{"id": n["id"], "type": n["type"]} for k, n in enumerate(ba) if k not in used_b],
    }


def main() -> None:
    decks_by_id = {}
    with open(AST_ROOT / "extraction_manifest.jsonl", encoding="utf-8") as fh:
        for line in fh:
            rec = json.loads(line)
            decks_by_id[rec["deck_id"]] = rec

    deck_cache: dict[str, dict] = {}

    def get_deck(deck_id: str) -> dict:
        if deck_id not in deck_cache:
            path = Path(decks_by_id[deck_id]["ast_path"])
            deck_cache[deck_id] = json.loads(path.read_text(encoding="utf-8"))
        return deck_cache[deck_id]

    out_path = PAIRS_DIR / "slide_alignments.jsonl"
    stats = {"slide_pairs": 0, "matched_nodes": 0, "unmatched_raw": 0, "unmatched_branded": 0}
    n_decks = 0

    with open(PAIRS_DIR / "validated_pairs.jsonl", encoding="utf-8") as fh, open(out_path, "w", encoding="utf-8") as out:
        for line in fh:
            verdict = json.loads(line)
            raw_deck = get_deck(verdict["raw_deck"])
            bran_deck = get_deck(verdict["branded_deck"])
            n_decks += 1
            for sm in verdict["slide_mappings"]:
                r_idx = int(sm["raw_slide_id"].rsplit("__s", 1)[1]) - 1
                b_idx = int(sm["branded_slide_id"].rsplit("__s", 1)[1]) - 1
                result = align_slide(raw_deck["slides"][r_idx]["nodes"], bran_deck["slides"][b_idx]["nodes"])
                record = {
                    "alignment_id": sm["pair_id"].replace("pair_", "align_"),
                    "deck_pair_id": verdict["deck_pair_id"],
                    "name_key": verdict["name_key"],
                    "status": verdict["status"],
                    "raw_slide_id": sm["raw_slide_id"],
                    "branded_slide_id": sm["branded_slide_id"],
                    "slide_similarity": sm["similarity"],
                    **result,
                }
                out.write(json.dumps(record, ensure_ascii=False) + "\n")
                stats["slide_pairs"] += 1
                stats["matched_nodes"] += len(result["matches"])
                stats["unmatched_raw"] += len(result["unmatched_raw"])
                stats["unmatched_branded"] += len(result["unmatched_branded"])

    stats["deck_pairs"] = n_decks
    (config.METADATA_DIR / "alignment_summary.json").write_text(json.dumps(stats, indent=2), encoding="utf-8")
    print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    main()
