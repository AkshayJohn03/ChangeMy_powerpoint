"""Phase 6B/6C: relational-context benchmark.

Experiments (all under leakage-safe grouped CV):
    BASE_NODE_ONLY     V2 node features
    ORACLE_CONTEXT     + TRUE neighbour labels   (ORACLE_ONLY, research bound)
    ANCHOR_CONTEXT     + deterministic rule anchors (deployable)
    GEOMETRY_RELATIONS / TYPOGRAPHY_RELATIONS / GROUP_RELATIONS / ALL_RELATIONAL

    python -m morphlite.training.relational_benchmark [--rebuild]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

from .. import config
from ..ast import extractor
from ..features.node_features_v2 import FEATURE_NAMES_V2, extract_slide_node_features_v2
from .bench_classifiers import choose_folds, model_zoo, repeated_group_cv
from .dataset_builder import label_from_tags, load_json, truth_node_labels

AST_V2 = config.EXTRACTED_DIR / "ast_v2"
CHROME_ROOT = config.EXTRACTED_DIR / "chrome"
PAIRS_DIR = config.PAIRS_DIR
CACHE = config.DATA_DIR / "processed" / "node_relational_cache.jsonl"

WEAK = ["RESTYLE", "RESIZE", "REMOVE", "MOVE"]

GEOM_REL = ["nn_h_gap", "nn_v_gap", "same_group_size", "container_child_count",
            "overlap_cnt", "left_aligned_cnt", "right_aligned_cnt", "top_aligned_cnt", "bottom_aligned_cnt"]
TYPO_REL = ["same_font_frac", "similar_size_frac", "same_color_frac", "text_neighbor_frac"]
GROUP_REL = ["same_group_size", "container_child_count"]

VARIANTS = {
    "BASE_NODE_ONLY": [],
    "ORACLE_CONTEXT": ["__oracle__"],
    "ANCHOR_CONTEXT": ["__anchor__"],
    "GEOMETRY_RELATIONS": GEOM_REL,
    "TYPOGRAPHY_RELATIONS": TYPO_REL,
    "GROUP_RELATIONS": GROUP_REL,
    "ALL_RELATIONAL": None,
}


def build_rows(rebuild: bool = False) -> list[dict]:
    from ..graph.features import ANCHOR_FEATURE_NAMES, RELATIONAL_FEATURE_NAMES
    from ..graph.oracle_features import ORACLE_CONTEXT_FEATURES

    if CACHE.exists() and not rebuild:
        rows = [json.loads(l) for l in open(CACHE, encoding="utf-8")]
        if rows:
            probe = rows[0]
            schema_ok = (
                set(probe.get("rel", {})) == set(RELATIONAL_FEATURE_NAMES)
                and set(probe.get("anchor", {})) == set(ANCHOR_FEATURE_NAMES)
                and set(probe.get("oracle", {})) == set(ORACLE_CONTEXT_FEATURES)
            )
            if not schema_ok:
                print("relational cache schema drift -> rebuilding", flush=True)
            else:
                return rows

    from ..graph.builder import build_slide_graph
    from ..graph.features import anchor_features, relational_features
    from ..graph.oracle_features import oracle_context_features
    from ..rules.engine import build_plan as deterministic_plan

    paths = {}
    with open(AST_V2 / "extraction_manifest_v2.jsonl", encoding="utf-8") as fh:
        for line in fh:
            rec = json.loads(line)
            paths[rec["deck_id"]] = rec["ast_v2_path"]

    rules = load_json(config.METADATA_DIR / "LEARNED_RULES.json")
    truth = truth_node_labels()
    rows = []

    with open(PAIRS_DIR / "validated_pairs.jsonl", encoding="utf-8") as fh:
        pairs = [json.loads(line) for line in fh]

    for v in pairs:
        raw_deck = load_json(Path(paths[v["raw_deck"]]))
        chrome = load_json(CHROME_ROOT / f"{v['raw_deck']}.json")
        plan = deterministic_plan(raw_deck, chrome, rules)
        anchors = {op["node_id"]: {"op": op["op"], "confidence": op["confidence"]} for op in plan.get("node_plan", [])}
        group = v["name_key"] or v["raw_deck"]

        for sm in v["slide_mappings"]:
            ri = int(sm["raw_slide_id"].rsplit("__s", 1)[1]) - 1
            slide = raw_deck["slides"][ri]
            graph = build_slide_graph(slide, deck_id=raw_deck["deck_id"])
            base = extract_slide_node_features_v2(slide)
            rel = relational_features(graph)
            anch = anchor_features(graph, anchors)
            ids = [nd["id"] for nd in extractor.flatten_nodes(slide["nodes"])]
            labels = {nid: (label_from_tags(truth[nid]["tags"]) if nid in truth else "UNCHANGED") for nid in ids}
            orc = oracle_context_features(graph, labels)

            for i, nid in enumerate(ids):
                rows.append(
                    {
                        "sample_id": nid,
                        "group": group,
                        "label": labels[nid],
                        "base": base[i],
                        "rel": rel[i],
                        "anchor": anch[i],
                        "oracle": orc[i],
                    }
                )

    CACHE.parent.mkdir(parents=True, exist_ok=True)
    with open(CACHE, "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    return rows


def make_X(rows: list[dict], variant: str) -> np.ndarray:
    extra_names = VARIANTS[variant]
    use_oracle = extra_names == ["__oracle__"]
    use_anchor = extra_names == ["__anchor__"]
    if use_oracle:
        from ..graph.oracle_features import ORACLE_CONTEXT_FEATURES

        extra_names = list(ORACLE_CONTEXT_FEATURES)
    elif use_anchor:
        from ..graph.features import ANCHOR_FEATURE_NAMES

        extra_names = list(ANCHOR_FEATURE_NAMES)
    elif extra_names is None:
        extra_names = list(rows[0]["rel"].keys())

    X = np.zeros((len(rows), len(FEATURE_NAMES_V2) + len(extra_names)), dtype=float)
    for r_i, r in enumerate(rows):
        for c_i, name in enumerate(FEATURE_NAMES_V2):
            X[r_i, c_i] = float(r["base"].get(name) or 0.0)
        offset = len(FEATURE_NAMES_V2)
        source = "oracle" if use_oracle else "anchor" if use_anchor else "rel"
        block = r[source]
        for c_i, name in enumerate(extra_names):
            X[r_i, offset + c_i] = float(block.get(name) or 0.0)
    return X


def weak_metrics(cv: dict) -> dict:
    per = cv.get("pooled_per_class_f1", {})
    present = [k for k in WEAK if k in per]
    recalls = recall_from_confusion(cv)
    return {
        "weak_class_macro_f1": round(sum(per[k] for k in present) / max(len(present), 1), 4),
        "move_recall": recalls.get("MOVE"),
        "per_class_recall": {k: recalls.get(k) for k in present},
    }


def recall_from_confusion(cv: dict) -> dict:
    labels = cv["pooled_labels"]
    cm = cv["pooled_confusion"]
    out = {}
    for i, lab in enumerate(labels):
        denom = sum(cm[i])
        out[lab] = round(cm[i][i] / denom, 4) if denom else 0.0
    return out


def main() -> None:
    rebuild = "--rebuild" in sys.argv
    rows = build_rows(rebuild)
    y = np.array([r["label"] for r in rows])
    groups = np.array([r["group"] for r in rows])
    folds = choose_folds(y, groups)

    results = {}
    for variant in VARIANTS:
        X = make_X(rows, variant)
        entry = {}
        for name in model_zoo("node"):
            cv = repeated_group_cv(lambda n=name: model_zoo("node")[n], X, y, groups, repeats=1)
            entry[name] = {
                "cv_macro_f1_mean": cv["cv_macro_f1_mean"],
                "cv_macro_f1_std": cv["cv_macro_f1_std"],
                "pooled_macro_f1": cv["pooled_macro_f1"],
                **weak_metrics(cv),
                "pooled_per_class_f1": cv["pooled_per_class_f1"],
            }
            e = entry[name]
            print(f"{variant:22s} {name:14s} cv={e['cv_macro_f1_mean']:.3f} weak={e['weak_class_macro_f1']:.3f} moveR={e['move_recall']}", flush=True)
        results[variant] = entry

    payload = {
        "n_rows": len(rows),
        "n_groups": int(len(set(groups))),
        "n_splits_used": folds,
        "labels": sorted(set(y)),
        "results": results,
    }
    out = config.METADATA_DIR / "RELATIONAL_BENCHMARK.json"
    out.write_text(json.dumps(payload, indent=1), encoding="utf-8")
    print(f"written {out}")


if __name__ == "__main__":
    main()
