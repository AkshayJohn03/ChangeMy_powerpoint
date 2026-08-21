"""Phase A + B runner: AST V2 quality audit, feature coverage, dataset integrity.

Artifacts (aggregate statistics only; no restricted tokens):
    data/metadata/AST_V2_AUDIT.json
    data/metadata/FEATURE_COVERAGE_V2.json
    data/metadata/DATASET_INTEGRITY.json

    python -m morphlite.training.audit_v2
"""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

from .. import config

AST_V1 = config.EXTRACTED_DIR / "ast"
AST_V2 = config.EXTRACTED_DIR / "ast_v2"
PROCESSED = config.DATA_DIR / "processed"
META = config.METADATA_DIR

EFF_FIELDS = ("font_family", "font_size_pt", "bold", "italic", "color")
SUSPECT_DEFAULT_SIZES = {18.0}


def _iter_manifest(path: Path):
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            yield json.loads(line)


def audit_ast_v2() -> dict:
    decks = slides = text_nodes = other_nodes = 0
    field_resolved = Counter()
    origin_hist = Counter()
    unresolved = Counter()
    suspicious = Counter()

    for rec in _iter_manifest(AST_V2 / "extraction_manifest_v2.jsonl"):
        decks += 1
        deck = json.loads(Path(rec["ast_v2_path"]).read_text(encoding="utf-8"))
        from ..ast import extractor

        for slide in deck.get("slides", []):
            slides += 1
            for nd in extractor.flatten_nodes(slide.get("nodes") or []):
                if not nd.get("paragraphs"):
                    if nd.get("type") != "GROUP":
                        other_nodes += 1
                    continue
                text_nodes += 1
                eff = nd.get("effective")
                if not eff:
                    unresolved["node_without_effective"] += 1
                    continue
                for f in EFF_FIELDS:
                    payload = eff.get(f)
                    if payload and payload.get("value") is not None:
                        field_resolved[f] += 1
                        origin_hist[f"{f}:{payload.get('origin')}"] += 1
                        if f == "font_size_pt" and payload.get("value") in SUSPECT_DEFAULT_SIZES and payload.get("origin") in ("theme", "master_other_style"):
                            suspicious[f"size18@{payload.get('origin')}"] += 1
                    else:
                        unresolved[f"field:{f}"] += 1

    return {
        "decks": decks,
        "slides": slides,
        "text_nodes": text_nodes,
        "non_text_nodes": other_nodes,
        "field_resolved": dict(field_resolved),
        "field_resolution_rate": {f: round(field_resolved[f] / max(text_nodes, 1), 4) for f in EFF_FIELDS},
        "unresolved_counts": dict(unresolved),
        "origin_histogram": dict(origin_hist.most_common(24)),
        "suspicious_defaults": dict(suspicious),
    }


def feature_coverage_v2() -> dict:
    out = {}
    for version, ds_name in (("v1", "node_dataset_v1.jsonl"), ("v2", "node_dataset_v2.jsonl")):
        path = PROCESSED / ds_name
        if not path.exists():
            continue
        rows = [json.loads(l) for l in open(path, encoding="utf-8")]
        names = list(rows[0]["features"].keys()) if rows else []
        nonzero = Counter()
        for r in rows:
            for k, v in r["features"].items():
                try:
                    if abs(float(v)) > 1e-9:
                        nonzero[k] += 1
                except (TypeError, ValueError):
                    pass
        n = max(len(rows), 1)
        out[version] = {
            "n_samples": len(rows),
            "feature_signal_rate": {k: round(nonzero[k] / n, 4) for k in names},
            "eff_features_present": any(k.startswith("eff_") for k in names),
        }
    return out


def dataset_integrity() -> dict:
    report = {}
    for version in ("v1", "v2"):
        entry = {}
        for task in ("intent", "node"):
            path = PROCESSED / f"{task}_dataset_{version}.jsonl"
            if not path.exists():
                continue
            rows = [json.loads(l) for l in open(path, encoding="utf-8")]
            group_splits = defaultdict(set)
            labels_by_split = defaultdict(Counter)
            dup_ids = 0
            seen_ids = set()
            for r in rows:
                group_splits[r["group"]].add(r["split"])
                labels_by_split[r["split"]][r["label"]] += 1
                if r["sample_id"] in seen_ids:
                    dup_ids += 1
                seen_ids.add(r["sample_id"])
            leaked_groups = [g for g, sp in group_splits.items() if len(sp) > 1]
            label_counts = Counter(r["label"] for r in rows)
            entry[task] = {
                "n_samples": len(rows),
                "unique_groups": len(group_splits),
                "groups_spanning_splits": len(leaked_groups),
                "duplicate_sample_ids": dup_ids,
                "label_distribution_total": dict(label_counts),
                "labels_per_split": {k: dict(v) for k, v in sorted(labels_by_split.items())},
                "min_class_support_overall": min(label_counts.values()) if label_counts else 0,
            }
        fp_idx = META / "FINGERPRINT_INDEX.json"
        if fp_idx.exists():
            idx = json.loads(fp_idx.read_text(encoding="utf-8"))
            hash_to_decks = defaultdict(list)
            for did, payload in idx.items():
                hash_to_decks[payload["exact_hash"]].append(did)
            entry["template_family_clusters"] = sum(1 for d in hash_to_decks.values() if len(d) > 1)
            entry["decks_in_shared_template_families"] = sum(len(d) for d in hash_to_decks.values() if len(d) > 1)
        report[version] = entry
    return report


def main() -> None:
    audit = audit_ast_v2()
    (META / "AST_V2_AUDIT.json").write_text(json.dumps(audit, indent=1), encoding="utf-8")

    cov = feature_coverage_v2()
    (META / "FEATURE_COVERAGE_V2.json").write_text(json.dumps(cov, indent=1), encoding="utf-8")

    integ = dataset_integrity()
    (META / "DATASET_INTEGRITY.json").write_text(json.dumps(integ, indent=1), encoding="utf-8")

    print(json.dumps({
        "ast_v2": {k: audit[k] for k in ("decks", "slides", "text_nodes", "field_resolution_rate")},
        "suspicious_defaults": audit["suspicious_defaults"],
        "coverage_versions": list(cov),
        "integrity_v2_intent": integ.get("v2", {}).get("intent"),
        "integrity_v2_node_groups": (integ.get("v2", {}).get("node") or {}).get("unique_groups"),
    }, indent=1))


if __name__ == "__main__":
    main()
