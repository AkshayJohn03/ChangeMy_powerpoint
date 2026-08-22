"""Phase 8: MOVE utility boundary + counterfactual ambiguity analysis.

Questions:
  1. Is the catastrophic MOVE recall concentrated in micro/small nudges?
  2. Does displacement-weighted recall tell a different story than event recall?
  3. Do similar deployable inputs map to inconsistent targets (irreducible ambiguity)?

    python -m morphlite.training.move_utility
"""
from __future__ import annotations

import json
import math
from collections import Counter
from pathlib import Path

import numpy as np

from .. import config
from .bench_classifiers import choose_folds
from .dataset_builder import truth_node_labels
from .propagation import load_rows
from .seed_recovery import assemble_seed_probabilities, geometry_matrix

BUCKETS = [("MICRO", 0.0, 0.01), ("SMALL", 0.01, 0.03), ("MEDIUM", 0.03, 0.08), ("LARGE", 0.08, float("inf"))]
WEAK = ["RESTYLE", "RESIZE", "REMOVE", "MOVE"]


def _bucket(disp: float) -> str:
    for name, lo, hi in BUCKETS:
        if lo <= disp < hi:
            return name
    return "LARGE"


def _entropy(counts: list[int]) -> float:
    total = sum(counts)
    if total == 0:
        return 0.0
    h = 0.0
    for c in counts:
        if c:
            p = c / total
            h -= p * math.log2(p)
    return round(h, 4)


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

    records = {}
    with open(config.PAIRS_DIR / "transformation_records.jsonl", encoding="utf-8") as fh:
        for line in fh:
            rec = json.loads(line)
            if rec.get("kind") == "MORPH":
                records[rec["raw_node_id"]] = rec

    P_D = seeds["D_hybrid_ensemble"]
    pred_labels = np.array([LABELS_PRESENT[i] for i in P_D.argmax(axis=1)])

    move_idx = [i for i, lab in enumerate(y) if lab == "MOVE"]
    per_node = []
    for i in move_idx:
        rec = records.get(rows[i]["sample_id"], {})
        g = rec.get("geometry") or {}
        dx = abs((g.get("x") or {}).get("delta") or 0.0)
        dy = abs((g.get("y") or {}).get("delta") or 0.0)
        disp = math.hypot(dx, dy)
        detected = bool(pred_labels[i] == "MOVE")
        per_node.append({"idx": i, "disp": disp, "bucket": _bucket(disp), "detected": detected})

    buckets_out = {}
    for name, lo, hi in BUCKETS:
        members = [p for p in per_node if lo <= p["disp"] < hi]
        det = sum(1 for m in members if m["detected"])
        buckets_out[name] = {
            "n_true_move": len(members),
            "detected": det,
            "recall_event": round(det / max(len(members), 1), 4),
            "displacement_mass_share": round(sum(m["disp"] for m in members) / max(sum(p["disp"] for p in per_node), 1e-9), 4),
        }

    total_disp = sum(p["disp"] for p in per_node)
    detected_disp = sum(p["disp"] for p in per_node if p["detected"])
    weighted_recall = round(detected_disp / max(total_disp, 1e-9), 4)

    micro_small_mass = sum(p["disp"] for p in per_node if p["bucket"] in ("MICRO", "SMALL"))
    micro_small_events = sum(1 for p in per_node if p["bucket"] in ("MICRO", "SMALL"))

    summary = {
        "true_move_nodes": len(move_idx),
        "event_recall_overall": round(len([p for p in per_node if p["detected"]]) / max(len(move_idx), 1), 4),
        "weighted_displacement_recall": weighted_recall,
        "micro_small": {
            "events": micro_small_events,
            "event_share": round(micro_small_events / max(len(move_idx), 1), 4),
            "mass_share": round(micro_small_mass / max(total_disp, 1e-9), 4),
        },
        "buckets": buckets_out,
    }

    # Phase 8.5 - counterfactual ambiguity: label entropy among k deployable-space neighbours
    k = 10
    Xn = X_base / np.maximum(np.linalg.norm(X_base, axis=1, keepdims=True), 1e-9)
    nbr_moves_frac = []
    nbr_entropy = []
    slide_key = [r["slide_key"] for r in rows]
    for i in move_idx:
        sims = Xn @ Xn[i]
        order = np.argsort(-sims)
        picked = 0
        counts = Counter()
        for j in order:
            if j == i or slide_key[j] == slide_key[i]:
                continue
            counts[y[j]] += 1
            picked += 1
            if picked >= k:
                break
        nbr_entropy.append(_entropy(list(counts.values())))
        nbr_moves_frac.append(counts.get("MOVE", 0) / max(picked, 1))

    amb = {
        "knn_k": k,
        "global_label_entropy_H_Y": _entropy(list(Counter(y).values())),
        "mean_neighbour_entropy_for_MOVE_nodes": round(float(np.mean(nbr_entropy)), 4),
        "mean_nbr_move_fraction_for_MOVE_nodes": round(float(np.mean(nbr_moves_frac)), 4),
    }
    for name, lo, hi in BUCKETS:
        idxs = [p["idx"] for p in per_node if lo <= p["disp"] < hi]
        ent = [nbr_entropy[move_idx.index(i)] for i in idxs if i in move_idx]
        mvf = [nbr_moves_frac[move_idx.index(i)] for i in idxs if i in move_idx]
        amb[f"bucket_{name}"] = {
            "n": len(idxs),
            "mean_neighbour_entropy": round(float(np.mean(ent)), 4) if ent else None,
            "mean_nbr_move_fraction": round(float(np.mean(mvf)), 4) if mvf else None,
        }

    payload = {"schema": "move_utility_v1", "utility": summary, "ambiguity": amb}
    out = config.METADATA_DIR / "MOVE_UTILITY.json"
    out.write_text(json.dumps(payload, indent=1), encoding="utf-8")
    print(json.dumps(payload, indent=1))


if __name__ == "__main__":
    main()
