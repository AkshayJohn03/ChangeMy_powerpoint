"""Transformation diff engine.

Consumes data/pairs/slide_alignments.jsonl and produces:
    data/pairs/transformation_records.jsonl   one object-level morph/add/remove record
    data/metadata/TRANSFORMATION_TAXONOMY.json  aggregated rule statistics

    python -m morphlite.training.ast_diff
"""
from __future__ import annotations

import json
import statistics
from collections import Counter, defaultdict
from pathlib import Path

from .. import config
from ..ast import extractor

PAIRS_DIR = config.PAIRS_DIR
AST_ROOT = config.EXTRACTED_DIR / "ast"

GEOM_MOVE_EPS = 0.02
GEOM_RESIZE_REL = 0.05
FONT_SIZE_EPS = 0.75


def dominant_props(node: dict) -> dict:
    fams: Counter = Counter()
    sizes: Counter = Counter()
    colors: Counter = Counter()
    bolds: Counter = Counter()
    for p in node.get("paragraphs") or []:
        for r in p.get("runs") or []:
            if r.get("font_family"):
                fams[r["font_family"].lower()] += 1
            if r.get("font_size_pt"):
                sizes[round(r["font_size_pt"], 1)] += 1
            if r.get("color"):
                colors[r["color"].upper()] += 1
            if r.get("bold") is not None:
                bolds[str(bool(r["bold"]))] += 1

    def pick(c: Counter):
        return c.most_common(1)[0][0] if c else None

    return {
        "font_family": pick(fams),
        "font_size_pt": pick(sizes),
        "run_color": pick(colors),
        "bold": pick(bolds),
    }


def _pair(feature: str, before, after):
    if before is None or after is None:
        return None
    return feature, before, after


def build_record(alignment: dict, m: dict, raw_node: dict, bran_node: dict, seq: int) -> dict:
    rb, bb = raw_node.get("bbox_norm") or {}, bran_node.get("bbox_norm") or {}
    geometry = {}
    for k in ("x", "y", "w", "h"):
        bv, av = rb.get(k), bb.get(k)
        if bv is None or av is None:
            continue
        geometry[k] = {"before": bv, "after": av, "delta": round(av - bv, 5)}

    dp_raw, dp_bran = dominant_props(raw_node), dominant_props(bran_node)
    typography = {f: {"before": dp_raw[f], "after": dp_bran[f]} for f in dp_raw}

    ta, tb = extractor.node_text(raw_node), extractor.node_text(bran_node)
    content = {
        "chars_before": len(ta),
        "chars_after": len(tb),
        "similarity": textsim_light(ta, tb),
        "text_changed": ta.strip() != tb.strip(),
    }

    rec = {
        "record_id": f"{alignment['alignment_id']}__m{seq:03d}",
        "kind": "MORPH",
        "deck_pair_id": alignment["deck_pair_id"],
        "name_key": alignment["name_key"],
        "status": alignment["status"],
        "raw_node_id": raw_node["id"],
        "branded_node_id": bran_node["id"],
        "node_type": raw_node["type"],
        "match_confidence": m["confidence"],
        "geometry": geometry,
        "typography": typography,
        "style": {
            "fill_color": {"before": raw_node.get("fill_color"), "after": bran_node.get("fill_color")},
        },
        "content": content,
    }
    rec["tags"] = classify(rec)
    return rec


def textsim_light(a: str, b: str) -> float:
    from . import textsim

    return textsim.similarity(a, b)


def classify(rec: dict) -> list[str]:
    tags = []
    t = rec["typography"]

    def changed(feat):
        v = t.get(feat)
        return bool(v and v["before"] is not None and v["after"] is not None and v["before"] != v["after"])

    if changed("font_family"):
        tags.append("TYPOGRAPHY_FONT_FAMILY")
    fs = t.get("font_size_pt")
    if fs and fs["before"] and fs["after"] and abs(fs["before"] - fs["after"]) >= FONT_SIZE_EPS:
        tags.append("TYPOGRAPHY_FONT_SIZE")
    if changed("bold"):
        tags.append("TYPOGRAPHY_WEIGHT")
    if changed("run_color"):
        tags.append("TYPOGRAPHY_COLOR")

    s = rec["style"]
    fc = s.get("fill_color")
    if fc and fc["before"] and fc["after"] and fc["before"] != fc["after"]:
        tags.append("STYLE_FILL")

    g = rec["geometry"]
    if any(k in g and abs(g[k]["delta"]) > GEOM_MOVE_EPS for k in ("x", "y")):
        tags.append("GEOMETRY_TRANSLATE")
    for k in ("w", "h"):
        if k in g and g[k]["before"] and abs(g[k]["delta"]) / max(g[k]["before"], 1e-9) > GEOM_RESIZE_REL:
            tags.append("GEOMETRY_RESIZE")
            break

    if rec["content"]["text_changed"]:
        tags.append("CONTENT_REWRITE")
    if not tags:
        tags.append("UNCHANGED")
    return tags


def side_record(alignment: dict, entry: dict, side: str, seq: int) -> dict:
    return {
        "record_id": f"{alignment['alignment_id']}__{'r' if side == 'REMOVED' else 'a'}{seq:03d}",
        "kind": side,
        "deck_pair_id": alignment["deck_pair_id"],
        "name_key": alignment["name_key"],
        "node_type": entry["type"],
        "node_id": entry["id"],
        "tags": ["STRUCTURE_REMOVE" if side == "REMOVED" else "STRUCTURE_ADD"],
    }


def aggregate(records: list[dict]) -> dict:
    cat_counts: Counter = Counter()
    rule_support: Counter = Counter()
    attempts: Counter = Counter()
    geom = {"dx": [], "dy": [], "dw_rel": [], "dh_rel": []}
    by_kind: Counter = Counter()

    for r in records:
        by_kind[r["kind"]] += 1
        for tag in r["tags"]:
            cat_counts[tag] += 1
        if r["kind"] != "MORPH":
            continue
        t = r["typography"]
        feats = {
            "font_family": (t["font_family"]["before"], t["font_family"]["after"]),
            "font_size_pt": (t["font_size_pt"]["before"], t["font_size_pt"]["after"]),
            "bold": (t["bold"]["before"], t["bold"]["after"]),
            "run_color": (t["run_color"]["before"], t["run_color"]["after"]),
            "fill_color": (r["style"]["fill_color"]["before"], r["style"]["fill_color"]["after"]),
        }
        for feat, (b, a) in feats.items():
            if b is None or a is None:
                continue
            attempts[feat] += 1
            rule_support[(feat, str(b).lower(), str(a).lower())] += 1

        g = r["geometry"]
        if "x" in g:
            geom["dx"].append(g["x"]["delta"])
        if "y" in g:
            geom["dy"].append(g["y"]["delta"])
        for key, axis in (("dw_rel", "w"), ("dh_rel", "h")):
            if axis in g and g[axis]["before"]:
                geom[key].append(round(g[axis]["delta"] / g[axis]["before"], 4))

    rules_by_feature: dict[str, list] = defaultdict(list)
    for (feat, b, a), support in rule_support.items():
        rules_by_feature[feat].append(
            {"feature": feat, "from_value": b, "to_value": a, "support": support,
             "confidence": round(support / attempts[feat], 4)}
        )
    for feat in rules_by_feature:
        rules_by_feature[feat] = sorted(rules_by_feature[feat], key=lambda x: -x["support"])[:20]

    geom_stats = {}
    for key, vals in geom.items():
        if vals:
            geom_stats[key] = {
                "n": len(vals),
                "mean": round(statistics.mean(vals), 4),
                "median": round(statistics.median(vals), 4),
                "p90_abs": round(sorted(abs(v) for v in vals)[int(0.9 * (len(vals) - 1))], 4),
            }

    return {
        "records_total": len(records),
        "by_kind": dict(by_kind),
        "category_counts": dict(cat_counts.most_common()),
        "feature_attempts": dict(attempts),
        "rules_by_feature": rules_by_feature,
        "geometry_stats": geom_stats,
    }


def main() -> None:
    decks_by_id = {}
    with open(AST_ROOT / "extraction_manifest.jsonl", encoding="utf-8") as fh:
        for line in fh:
            rec = json.loads(line)
            decks_by_id[rec["deck_id"]] = rec

    node_index_cache: dict[str, dict] = {}

    def node_by_id(deck_id: str, node_id: str):
        if deck_id not in node_index_cache:
            deck = json.loads(Path(decks_by_id[deck_id]["ast_path"]).read_text(encoding="utf-8"))
            idx = {}
            for slide in deck["slides"]:
                for n in extractor.flatten_nodes(slide["nodes"]):
                    idx[n["id"]] = n
            node_index_cache[deck_id] = idx
        return node_index_cache[deck_id].get(node_id)

    records = []
    with open(PAIRS_DIR / "slide_alignments.jsonl", encoding="utf-8") as fh:
        for line in fh:
            alignment = json.loads(line)
            raw_deck_id = alignment["raw_slide_id"].rsplit("__s", 1)[0]
            bran_deck_id = alignment["branded_slide_id"].rsplit("__s", 1)[0]

            seq = 0
            for m in alignment["matches"]:
                rn = node_by_id(raw_deck_id, m["raw_node_id"])
                bn = node_by_id(bran_deck_id, m["branded_node_id"])
                if rn is None or bn is None:
                    continue
                records.append(build_record(alignment, m, rn, bn, seq))
                seq += 1
            for e in alignment["unmatched_raw"]:
                records.append(side_record(alignment, e, "REMOVED", seq))
                seq += 1
            for e in alignment["unmatched_branded"]:
                records.append(side_record(alignment, e, "ADDED", seq))
                seq += 1

    out = PAIRS_DIR / "transformation_records.jsonl"
    with open(out, "w", encoding="utf-8") as fh:
        for r in records:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")

    taxonomy = aggregate(records)
    (config.METADATA_DIR / "TRANSFORMATION_TAXONOMY.json").write_text(json.dumps(taxonomy, indent=1), encoding="utf-8")

    print(json.dumps({k: v for k, v in taxonomy.items() if k != "rules_by_feature"}, indent=2))
    print("\nTop rules:")
    for feat, rules in taxonomy["rules_by_feature"].items():
        for r in rules[:4]:
            print(f"  {feat:14s} {str(r['from_value'])[:22]:24s} -> {str(r['to_value'])[:22]:24s} support={r['support']:5d} conf={r['confidence']:.2f}")


if __name__ == "__main__":
    main()
