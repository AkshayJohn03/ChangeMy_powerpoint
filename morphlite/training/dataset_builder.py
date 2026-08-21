"""Build labeled benchmark datasets with deck-grouped splits.

Outputs:
    data/processed/intent_dataset.jsonl   REBUILD / PRESERVE / MIXED per deck pair
    data/processed/node_dataset.jsonl     UNCHANGED / RESTYLE / RESIZE / MOVE /
                                          RECOLOR / REMOVE / ADD per node
    data/processed/dataset_meta.json      schema versions, split summary

Split rule (PDR section 4): by deck family group, never mixing slides of one
logical deck across splits.

    python -m morphlite.training.dataset_builder
"""
from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from pathlib import Path

from .. import config
from ..ast import extractor
from .chrome_diff import slide_index as chrome_slide_index
from ..features import node_features, deck_features

PAIRS_DIR = config.PAIRS_DIR
AST_ROOT = config.EXTRACTED_DIR / "ast"
CHROME_ROOT = config.EXTRACTED_DIR / "chrome"
PROCESSED = config.DATA_DIR / "processed"

INTENT_LABELS = ["PRESERVE", "MIXED", "REBUILD"]
NODE_LABELS = ["UNCHANGED", "RESTYLE", "RESIZE", "MOVE", "RECOLOR", "REMOVE", "ADD"]

REBUILD_RATIO = 0.6


def load_json(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


def ast_manifest_index() -> dict[str, dict]:
    idx = {}
    with open(AST_ROOT / "extraction_manifest.jsonl", encoding="utf-8") as fh:
        for line in fh:
            rec = json.loads(line)
            idx[rec["deck_id"]] = rec["ast_path"]
    return idx


def keep_change_counts(raw_chrome: dict, bran_chrome: dict, mappings: list[dict]) -> tuple[int, int]:
    equal = diff = 0
    for sm in mappings:
        ri = int(sm["raw_slide_id"].rsplit("__s", 1)[1]) - 1 if isinstance(sm["raw_slide_id"], str) else -1
        bi = int(sm["branded_slide_id"].rsplit("__s", 1)[1]) - 1
        rl = raw_chrome["slides"][ri].get("layout") if 0 <= ri < len(raw_chrome["slides"]) else None
        bl = bran_chrome["slides"][bi].get("layout") if 0 <= bi < len(bran_chrome["slides"]) else None
        if rl == bl:
            equal += 1
        else:
            diff += 1
    return equal, diff


def intent_label(equal: int, diff: int) -> str:
    ratio = diff / max(equal + diff, 1)
    if ratio == 0.0:
        return "PRESERVE"
    if ratio >= REBUILD_RATIO:
        return "REBUILD"
    return "MIXED"


def group_split(group: str, n_buckets: int = 10) -> str:
    h = int(hashlib.md5(group.encode("utf-8")).hexdigest(), 16) % n_buckets
    if h < 6:
        return "train"
    if h < 8:
        return "val"
    return "test"


def build_intent_dataset(ast_paths: dict[str, str], known_sources: set[str]) -> list[dict]:
    rows = []
    seen_pairs = set()

    def add_sample(raw_deck: str, bran_deck: str, mappings: list[dict], basis: str, group: str | None):
        key = (raw_deck, bran_deck)
        if key in seen_pairs:
            return None
        seen_pairs.add(key)
        raw_chrome = load_json(CHROME_ROOT / f"{raw_deck}.json")
        bran_chrome = load_json(CHROME_ROOT / f"{bran_deck}.json")
        equal, diff = keep_change_counts(raw_chrome, bran_chrome, mappings)
        label = intent_label(equal, diff)
        deck = load_json(Path(ast_paths[raw_deck]))
        feats = deck_features.extract_deck_features(deck, raw_chrome, known_sources)
        g = group or raw_deck.rsplit("__", 1)[0]
        row = {
            "sample_id": f"intent__{raw_deck}__{bran_deck}",
            "group": g,
            "label": label,
            "basis": basis,
            "equal": equal,
            "changed": diff,
            "features": feats,
        }
        rows.append(row)
        return row

    with open(PAIRS_DIR / "validated_pairs.jsonl", encoding="utf-8") as fh:
        pairs = [json.loads(line) for line in fh]
    for v in pairs:
        add_sample(v["raw_deck"], v["branded_deck"], v["slide_mappings"], v["status"], None)

    variant_added = 0
    res_path = PAIRS_DIR / "review_resolutions.jsonl"
    if res_path.exists():
        with open(res_path, encoding="utf-8") as fh:
            resolutions = [json.loads(line) for line in fh]
        raw_side_by_rawdeck = {v["raw_deck"]: v for v in pairs}
        bran_side_by_brandeck = {v["branded_deck"]: v for v in pairs}
        for r in resolutions:
            match = r.get("best_match_deck")
            if not match or r["mean_similarity"] < 0.75:
                continue
            src = None
            if r["resolution"] == "RAW_VARIANT_OF_PAIRED_RAW" and match in raw_side_by_rawdeck:
                src = raw_side_by_rawdeck[match]
                raw_deck, bran_deck = r["review_deck"], src["branded_deck"]
                mappings = src["slide_mappings"]
            elif r["resolution"] == "CLEAN_VARIANT_OF_PAIRED_BRANDED" and match in bran_side_by_brandeck:
                src = bran_side_by_brandeck[match]
                raw_deck, bran_deck = src["raw_deck"], r["review_deck"]
                mappings = src["slide_mappings"]
            elif r["resolution"] == "CLEAN_VARIANT_CANDIDATE" and r.get("best_match_bucket") == "branded_only":
                raw_deck, bran_deck = r["review_deck"], match
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
            else:
                continue
            if add_sample(raw_deck, bran_deck, mappings, "variant_twin", r["name_key"]):
                variant_added += 1

    print(f"intent dataset: {len(rows)} samples ({variant_added} variant twins)")
    return rows


def truth_node_labels() -> dict[str, dict]:
    out: dict[str, dict] = {}
    with open(PAIRS_DIR / "transformation_records.jsonl", encoding="utf-8") as fh:
        for line in fh:
            r = json.loads(line)
            if r["kind"] == "MORPH":
                entry = out.setdefault(r["raw_node_id"], {"tags": set()})
                entry["tags"].update(r["tags"])
            elif r["kind"] == "REMOVED":
                out.setdefault(r["node_id"], {"tags": {"STRUCTURE_REMOVE"}})["tags"].add("STRUCTURE_REMOVE")
    return out


PRIORITY = [
    ("REMOVE", {"STRUCTURE_REMOVE"}),
    ("RESIZE", {"TYPOGRAPHY_FONT_SIZE", "GEOMETRY_RESIZE"}),
    ("MOVE", {"GEOMETRY_TRANSLATE"}),
    ("RECOLOR", {"TYPOGRAPHY_COLOR", "STYLE_FILL"}),
    ("RESTYLE", {"TYPOGRAPHY_FONT_FAMILY", "TYPOGRAPHY_WEIGHT", "CONTENT_REWRITE"}),
]


def label_from_tags(tags: set[str]) -> str:
    for label, markers in PRIORITY:
        if tags & markers:
            return label
    return "UNCHANGED"


def build_node_dataset(ast_paths: dict[str, str], known_sources: set[str]) -> list[dict]:
    truth = truth_node_labels()
    rows = []

    with open(PAIRS_DIR / "validated_pairs.jsonl", encoding="utf-8") as fh:
        pairs = [json.loads(line) for line in fh]

    for v in pairs:
        raw_deck = load_json(Path(ast_paths[v["raw_deck"]]))
        bran_deck = load_json(Path(ast_paths[v["branded_deck"]]))
        group = v["name_key"] or v["raw_deck"]

        for sm in v["slide_mappings"]:
            ri = int(sm["raw_slide_id"].rsplit("__s", 1)[1]) - 1
            bi = int(sm["branded_slide_id"].rsplit("__s", 1)[1]) - 1
            raw_feats = node_features.extract_slide_node_features(raw_deck["slides"][ri]["nodes"])
            raw_ids = node_features.node_ids_of_slide(raw_deck["slides"][ri]["nodes"])
            for nid, f in zip(raw_ids, raw_feats):
                entry = truth.get(nid)
                label = label_from_tags(entry["tags"]) if entry else "UNCHANGED"
                rows.append(
                    {
                        "sample_id": nid,
                        "group": group,
                        "label": label,
                        "side": "raw",
                        "slide_similarity": sm["similarity"],
                        "features": f,
                    }
                )

    with open(PAIRS_DIR / "slide_alignments.jsonl", encoding="utf-8") as fh:
        alignments = [json.loads(line) for line in fh]
    by_align_id = {a["alignment_id"]: a for a in alignments}

    for v in pairs:
        bran_deck_cache = None
        for sm in v["slide_mappings"]:
            aid = sm["pair_id"].replace("pair_", "align_")
            al = by_align_id.get(aid)
            if not al or not al["unmatched_branded"]:
                continue
            bi = int(sm["branded_slide_id"].rsplit("__s", 1)[1]) - 1
            if bran_deck_cache is None:
                bran_deck_cache = load_json(Path(ast_paths[v["branded_deck"]]))
            bran_feats = node_features.extract_slide_node_features(bran_deck_cache["slides"][bi]["nodes"])
            bran_ids = node_features.node_ids_of_slide(bran_deck_cache["slides"][bi]["nodes"])
            wanted = {e["id"] for e in al["unmatched_branded"]}
            group = v["name_key"] or v["raw_deck"]
            for nid, f in zip(bran_ids, bran_feats):
                if nid in wanted:
                    rows.append(
                        {
                            "sample_id": nid,
                            "group": group,
                            "label": "ADD",
                            "side": "branded",
                            "slide_similarity": sm["similarity"],
                            "features": f,
                        }
                    )

    print(f"node dataset: {len(rows)} samples")
    return rows


def main() -> None:
    PROCESSED.mkdir(parents=True, exist_ok=True)
    ast_paths = ast_manifest_index()

    rules = load_json(config.METADATA_DIR / "LEARNED_RULES.json")
    known_sources = set((rules.get("layout_swap_map") or {}).keys())

    intent_rows = build_intent_dataset(ast_paths, known_sources)
    node_rows = build_node_dataset(ast_paths, known_sources)

    for row in intent_rows + node_rows:
        row["split"] = group_split(row["group"])

    def dump(name, rows):
        with open(PROCESSED / name, "w", encoding="utf-8") as fh:
            for r in rows:
                fh.write(json.dumps(r, ensure_ascii=False) + "\n")

    dump("intent_dataset.jsonl", intent_rows)
    dump("node_dataset.jsonl", node_rows)

    def summarize(rows):
        c = defaultdict(lambda: defaultdict(int))
        for r in rows:
            c[r["split"]][r["label"]] += 1
        return {k: dict(v) for k, v in c.items()}

    meta = {
        "feature_schema_version": node_features.FEATURE_SCHEMA_VERSION,
        "intent": {
            "n": len(intent_rows),
            "labels": INTENT_LABELS,
            "splits": summarize(intent_rows),
            "features": deck_features.DECK_FEATURE_NAMES,
        },
        "node": {
            "n": len(node_rows),
            "labels": NODE_LABELS,
            "splits": summarize(node_rows),
            "features": node_features.FEATURE_NAMES,
        },
    }
    (PROCESSED / "dataset_meta.json").write_text(json.dumps(meta, indent=1), encoding="utf-8")
    print(json.dumps(meta["intent"]["splits"], indent=1))
    print(json.dumps(meta["node"]["splits"], indent=1))


class CounterLike(dict):
    pass


if __name__ == "__main__":
    main()
