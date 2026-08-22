"""Phase 7.7: MOVE error forensics.

Interrogates why true-MOVE nodes are missed by the best deployable seed model
(D_hybrid). Uses golden-pair ground-truth deltas as FORENSIC-ONLY evidence;
none of these features are deployable at inference.

    python -m morphlite.training.move_forensics
"""
from __future__ import annotations

import json
import math
from collections import Counter
from pathlib import Path

import numpy as np

from .. import config
from ..ast import extractor
from .bench_classifiers import choose_folds
from .dataset_builder import label_from_tags, truth_node_labels
from .propagation import load_rows
from .seed_recovery import assemble_seed_probabilities, geometry_matrix

WEAK = ["RESTYLE", "RESIZE", "REMOVE", "MOVE"]


def _load_records() -> dict[str, dict]:
    out = {}
    path = config.PAIRS_DIR / "transformation_records.jsonl"
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            r = json.loads(line)
            if r.get("kind") == "MORPH":
                out[r["raw_node_id"]] = r
    return out


def _box(g: dict, which: str):
    try:
        return (
            g["x"][which], g["y"][which],
            max(g["w"][which] or 0.0, 1e-6), max(g["h"][which] or 0.0, 1e-6),
        )
    except Exception:
        return None


def _iou(a, b) -> float:
    if a is None or b is None:
        return float("nan")
    ix = max(0.0, min(a[0] + a[2], b[0] + b[2]) - max(a[0], b[0]))
    iy = max(0.0, min(a[1] + a[3], b[1] + b[3]) - max(a[1], b[1]))
    inter = ix * iy
    union = a[2] * a[3] + b[2] * b[3] - inter
    return round(inter / union, 4) if union > 1e-9 else 0.0


def _auc(pos_vals, neg_vals) -> float | None:
    pos = [v for v in pos_vals if v == v]
    neg = [v for v in neg_vals if v == v]
    if not pos or not neg:
        return None
    from scipy.stats import mannwhitneyu

    try:
        u = mannwhitneyu(pos, neg, alternative="greater").statistic
        return round(float(u) / (len(pos) * len(neg)), 4)
    except Exception:
        return None


def classify_missed(rec_feat: dict) -> str:
    conf = rec_feat.get("match_confidence")
    if conf is None or conf < 0.5:
        return "ambiguous_correspondence"
    if rec_feat["disp"] < 0.02:
        return "small_displacement"
    if rec_feat["resize_coincident"]:
        return "simultaneous_resize_move"
    if rec_feat.get("group_move_frac", 0.0) >= 0.5:
        return "group_movement"
    if rec_feat["dx"] < 0.005:
        return "vertical_only_move"
    if rec_feat["dy"] < 0.005:
        return "horizontal_only_move"
    if rec_feat["disp"] > 0.15:
        return "large_displacement"
    return "other"


def main() -> None:
    rows = load_rows()
    feat_names = sorted(rows[0]["base"].keys())
    X_base = np.array([[float(r["base"].get(k) or 0.0) for k in feat_names] for r in rows])
    X_geo = geometry_matrix(rows)
    y = np.array([r["label"] for r in rows])
    groups = np.array([r["group"] for r in rows])

    LABELS_PRESENT = sorted(set(y))
    from . import seed_recovery as _sr

    _sr.LABELS_PRESENT = LABELS_PRESENT
    n_splits = choose_folds(y, groups)
    from sklearn.model_selection import StratifiedGroupKFold

    folds = list(StratifiedGroupKFold(n_splits=n_splits, shuffle=True, random_state=0).split(X_base, y, groups))
    seeds = assemble_seed_probabilities(rows, X_base, X_geo, y, groups, folds)
    P_D = seeds["D_hybrid_ensemble"]
    pred_idx = P_D.argmax(axis=1)

    records = _load_records()
    move_rows = [(i, r) for i, r in enumerate(rows) if r["label"] == "MOVE"]
    print(f"true MOVE nodes: {len(move_rows)}")

    samples = []
    missed_counter = Counter()
    for i, r in move_rows:
        rec = records.get(r["sample_id"])
        detected = bool(LABELS_PRESENT[pred_idx[i]] == "MOVE")
        base_feat = {
            "detected": detected,
            "node_type": r["base"].get("is_text"),
            "depth": r["base"].get("container_depth"),
            "text_len_log": r["base"].get("text_len_log1p"),
            "group_size": 1 + len(r["nbrs"].get("GROUP", [])),
        }
        if rec is None:
            missed_counter["no_record"] += 1
            base_feat["bucket"] = "no_record"
            samples.append({"sample_id": r["sample_id"], **base_feat})
            continue
        g = rec.get("geometry") or {}
        dx = abs((g.get("x") or {}).get("delta") or 0.0)
        dy = abs((g.get("y") or {}).get("delta") or 0.0)
        disp = round(math.hypot(dx, dy), 5)
        gnbrs = [j for j, _w in r["nbrs"].get("GROUP", [])]
        if gnbrs:
            group_move_frac = round(sum(1 for j in gnbrs if rows[j]["label"] == "MOVE") / len(gnbrs), 4)
        else:
            group_move_frac = 0.0
        samples.append(
            {
                "sample_id": r["sample_id"],
                **base_feat,
                "dx": round(dx, 5), "dy": round(dy, 5), "disp": disp,
                "overlap_before_after": _iou(_box(g, "before"), _box(g, "after")),
                "match_confidence": rec.get("match_confidence"),
                "resize_coincident": int("TYPOGRAPHY_FONT_SIZE" in (rec.get("tags") or []) or "GEOMETRY_RESIZE" in (rec.get("tags") or [])),
                "content_changed": int("CONTENT_REWRITE" in (rec.get("tags") or [])),
                "group_move_frac": group_move_frac,
                "bucket": None,
            }
        )

    for s in samples:
        if s.get("bucket") is not None:
            continue
        s["bucket"] = classify_missed(s)

    detected_feats = [s for s in samples if s["detected"]]
    missed_feats = [s for s in samples if not s["detected"]]

    numeric = ["disp", "dx", "dy", "overlap_before_after", "match_confidence",
               "group_size", "group_move_frac", "depth", "text_len_log"]
    comparison = {}
    for f in numeric:
        det_vals = [s[f] for s in detected_feats if isinstance(s.get(f), (int, float))]
        mis_vals = [s[f] for s in missed_feats if isinstance(s.get(f), (int, float))]

        def med(v):
            return round(float(np.median(v)), 5) if v else None

        def mean(v):
            return round(float(np.mean(v)), 5) if v else None

        comparison[f] = {
            "detected_median": med(det_vals), "missed_median": med(mis_vals),
            "detected_mean": mean(det_vals), "missed_mean": mean(mis_vals),
            "auc_detected_vs_missed": _auc(det_vals, mis_vals),
        }

    tax = Counter(s["bucket"] for s in missed_feats)
    tax_detected = Counter(s["bucket"] for s in detected_feats)

    other_rows = [s for s in missed_feats if s["bucket"] == "other"]
    other_profile = {
        "share_non_text": round(sum(1 for s in other_rows if not s.get("text_len_log")) / max(len(other_rows), 1), 4),
        "share_grouped": round(sum(1 for s in other_rows if (s.get("group_size") or 1) > 1) / max(len(other_rows), 1), 4),
        "median_disp": round(float(np.median([s["disp"] for s in other_rows])), 5) if other_rows else None,
        "median_depth": float(np.median([s.get("depth") or 0 for s in other_rows])) if other_rows else None,
    }

    dominant, dom_n = (tax.most_common(1)[0] if tax else ("none", 0))
    share = round(dom_n / max(sum(tax.values()), 1), 4)

    decision_map = {
        "ambiguous_correspondence": "Correspondence failure -> improve node matching before more data",
        "small_displacement": "Sub-threshold displacements -> add targeted displacement-scale features / relabel tolerance",
        "simultaneous_resize_move": "Compound operations -> split MOVE/RESIZE into joint structured targets",
        "group_movement": "Group-level displacement -> relational/group-state representation required",
        "horizontal_only_move": "Axis-specific signal -> add directional displacement features",
        "vertical_only_move": "Axis-specific signal -> add directional displacement features",
        "large_displacement": "Large moves missed -> model capacity/data issue, collect targeted pairs",
        "other": "No separable signal -> more labelled pairs needed",
        "no_record": "Alignment gaps -> improve slide-mapping coverage",
    }

    payload = {
        "schema": "move_forensics_v1",
        "true_move_nodes": len(samples),
        "detected": len(detected_feats),
        "missed": len(missed_feats),
        "feature_comparison_detected_vs_missed": comparison,
        "missed_taxonomy": dict(tax.most_common()),
        "taxonomy_share_of_misses": {k: round(v / max(sum(tax.values()), 1), 4) for k, v in tax.most_common()},
        "detected_taxonomy_for_reference": dict(tax_detected.most_common()),
        "dominant_bucket": {"name": dominant, "share": share},
        "other_bucket_profile": other_profile,
        "recommended_action": decision_map.get(dominant, "unknown"),
        "note": "Forensic-only analysis using golden-pair ground-truth deltas; features are NOT deployable.",
    }
    (config.METADATA_DIR / "MOVE_FORENSICS.json").write_text(json.dumps(payload, indent=1), encoding="utf-8")

    md = [
        "# Phase 7.7 - MOVE Error Forensics",
        "",
        f"True MOVE nodes: **{len(samples)}** | detected: **{len(detected_feats)}** | missed: **{len(missed_feats)}**",
        "",
        "## Detected vs missed distributions",
        "",
        "| Feature | detected median | missed median | AUC(det vs miss) |",
        "|---|---|---|---|",
    ]
    for f, c in comparison.items():
        md.append(f"| {f} | {c['detected_median']} | {c['missed_median']} | {c['auc_detected_vs_missed']} |")
    md += [
        "",
        "## Missed-MOVE taxonomy",
        "",
        "| Bucket | Count | Share of misses |",
        "|---|---:|---:|",
    ]
    for k, v in tax.most_common():
        md.append(f"| {k} | {v} | {round(v / max(sum(tax.values()), 1), 3)} |")
    md += [
        "",
        f"**Dominant failure mode:** `{dominant}` ({share:.0%} of misses)",
        "",
        f"**Recommended action:** {decision_map.get(dominant)}",
        "",
        "Fold-safety audit note: D_hybrid OOF predictions derive exclusively from fold-safe "
        "component models; forensic deltas above use branded-deck ground truth and are marked non-deployable.",
    ]
    (config.METADATA_DIR / "PHASE_77_MOVE_FORENSICS.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(json.dumps({k: payload[k] for k in ("true_move_nodes", "detected", "missed", "dominant_bucket", "recommended_action")}, indent=1))


if __name__ == "__main__":
    main()
