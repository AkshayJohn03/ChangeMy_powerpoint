"""V2 datasets: same labels, groups and split hashing as V1; v2 features.

    python -m morphlite.training.dataset_builder_v2
"""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

from .. import config
from ..features import fingerprint as fp
from ..features.deck_features_v2 import DECK_FEATURE_NAMES_V2, extract_deck_features_v2
from ..features.node_features_v2 import FEATURE_NAMES_V2, extract_slide_node_features_v2
from .dataset_builder import (
    PROCESSED,
    ast_manifest_index,
    group_split,
    intent_label,
    keep_change_counts,
    label_from_tags,
    load_json,
    truth_node_labels,
)

PAIRS_DIR = config.PAIRS_DIR
AST_V2 = config.EXTRACTED_DIR / "ast_v2"
CHROME_ROOT = config.EXTRACTED_DIR / "chrome"


def v2_manifest_index() -> dict[str, dict]:
    idx = {}
    with open(AST_V2 / "extraction_manifest_v2.jsonl", encoding="utf-8") as fh:
        for line in fh:
            rec = json.loads(line)
            idx[rec["deck_id"]] = rec["ast_v2_path"]
    return idx


def main() -> None:
    PROCESSED.mkdir(parents=True, exist_ok=True)
    paths = v2_manifest_index()

    template_ids = [d for d in paths if d.startswith("template__")]
    template_fps = {d: fp.fingerprint_deck(d, load_json(Path(paths[d]))) for d in template_ids}

    with open(PAIRS_DIR / "validated_pairs.jsonl", encoding="utf-8") as fh:
        pairs = [json.loads(line) for line in fh]

    seen = set()
    intent_rows = []

    def add_intent(raw_deck: str, bran_deck: str):
        key = (raw_deck, bran_deck)
        if key in seen or raw_deck not in paths:
            return
        seen.add(key)
        rc = load_json(CHROME_ROOT / f"{raw_deck}.json")
        bc = load_json(CHROME_ROOT / f"{bran_deck}.json")
        n = min(len(rc["slides"]), len(bc["slides"]))
        mappings = [
            {
                "raw_slide_id": f"{raw_deck}__s{i + 1:03d}",
                "branded_slide_id": f"{bran_deck}__s{i + 1:03d}",
            }
            for i in range(n)
        ]
        equal, diff = keep_change_counts(rc, bc, mappings)
        deck = load_json(Path(paths[raw_deck]))
        feats = extract_deck_features_v2(deck, rc, template_fps)
        g = raw_deck.rsplit("__", 1)[0]
        intent_rows.append(
            {
                "sample_id": f"intent2__{raw_deck}__{bran_deck}",
                "group": g,
                "label": intent_label(equal, diff),
                "basis": "golden",
                "equal": equal,
                "changed": diff,
                "features": feats,
            }
        )

    for v in pairs:
        add_intent(v["raw_deck"], v["branded_deck"])

    res_path = PAIRS_DIR / "review_resolutions.jsonl"
    if res_path.exists():
        with open(res_path, encoding="utf-8") as fh:
            resolutions = [json.loads(line) for line in fh]
        raw_side = {v["raw_deck"]: v for v in pairs}
        bran_side = {v["branded_deck"]: v for v in pairs}
        for r in resolutions:
            match = r.get("best_match_deck")
            if not match or r.get("mean_similarity", 0) < 0.75:
                continue
            if r["resolution"] == "RAW_VARIANT_OF_PAIRED_RAW" and match in raw_side:
                src = raw_side[match]
                add_intent(r["review_deck"], src["branded_deck"])
            elif r["resolution"] == "CLEAN_VARIANT_OF_PAIRED_BRANDED" and match in bran_side:
                src = bran_side[match]
                add_intent(src["raw_deck"], r["review_deck"])
            elif r["resolution"] == "CLEAN_VARIANT_CANDIDATE" and r.get("best_match_bucket") == "branded_only":
                add_intent(r["review_deck"], match)

    truth = truth_node_labels()
    node_rows = []
    with open(PAIRS_DIR / "slide_alignments.jsonl", encoding="utf-8") as fh:
        alignments = [json.loads(line) for line in fh]
    by_align = {a["alignment_id"]: a for a in alignments}

    for v in pairs:
        if v["raw_deck"] not in paths or v["branded_deck"] not in paths:
            continue
        raw_deck = load_json(Path(paths[v["raw_deck"]]))
        bran_deck = load_json(Path(paths[v["branded_deck"]]))
        group = v["name_key"] or v["raw_deck"]

        for sm in v["slide_mappings"]:
            ri = int(sm["raw_slide_id"].rsplit("__s", 1)[1]) - 1
            bi = int(sm["branded_slide_id"].rsplit("__s", 1)[1]) - 1
            feats = extract_slide_node_features_v2(raw_deck["slides"][ri])
            ids = [nd["id"] for nd in __import__("morphlite.ast.extractor", fromlist=["x"]).flatten_nodes(raw_deck["slides"][ri]["nodes"])]
            for nid, f in zip(ids, feats):
                entry = truth.get(nid)
                label = label_from_tags(entry["tags"]) if entry else "UNCHANGED"
                node_rows.append({"sample_id": nid, "group": group, "label": label, "side": "raw", "slide_similarity": sm["similarity"], "features": f})

            aid = sm["pair_id"].replace("pair_", "align_")
            al = by_align.get(aid)
            if al and al["unmatched_branded"]:
                wanted = {e["id"] for e in al["unmatched_branded"]}
                bfeats = extract_slide_node_features_v2(bran_deck["slides"][bi])
                bids = [nd["id"] for nd in __import__("morphlite.ast.extractor", fromlist=["x"]).flatten_nodes(bran_deck["slides"][bi]["nodes"])]
                for nid, f in zip(bids, bfeats):
                    if nid in wanted:
                        node_rows.append({"sample_id": nid, "group": group, "label": "ADD", "side": "branded", "slide_similarity": sm["similarity"], "features": f})

    for row in intent_rows + node_rows:
        row["split"] = group_split(row["group"])

    def dump(name, rows):
        with open(PROCESSED / name, "w", encoding="utf-8") as fh:
            for r in rows:
                fh.write(json.dumps(r, ensure_ascii=False) + "\n")

    dump("intent_dataset_v2.jsonl", intent_rows)
    dump("node_dataset_v2.jsonl", node_rows)

    def summarize(rows):
        c = defaultdict(lambda: defaultdict(int))
        for r in rows:
            c[r["split"]][r["label"]] += 1
        return {k: dict(v) for k, v in c.items()}

    meta = {
        "feature_schema_version": "2.0.0",
        "intent": {"n": len(intent_rows), "labels": ["MIXED", "PRESERVE", "REBUILD"], "splits": summarize(intent_rows), "features": DECK_FEATURE_NAMES_V2},
        "node": {"n": len(node_rows), "labels": ["UNCHANGED", "RESTYLE", "RESIZE", "MOVE", "RECOLOR", "REMOVE", "ADD"], "splits": summarize(node_rows), "features": FEATURE_NAMES_V2},
    }
    (PROCESSED / "dataset_meta_v2.json").write_text(json.dumps(meta, indent=1), encoding="utf-8")
    print(json.dumps({"intent_n": len(intent_rows), "node_n": len(node_rows)}, indent=1))


if __name__ == "__main__":
    main()
