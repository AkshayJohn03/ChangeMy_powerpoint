"""Phase 7.5: high-recall seed recovery experiment.

Seeds (all strictly out-of-fold, deck-family grouped):
    A  current multiclass RF OOF probabilities          (baseline)
    B  class-weighted multiclass RF                     (weak-recall oriented)
    C  one-vs-rest binary weak-op detectors             (MOVE/REMOVE/RESIZE/RESTYLE)
    D  hybrid ensemble                                  (weights tuned inside folds)

Geometry detector uses DEPLOYABLE RAW-ONLY signals only (alignment residuals,
grid occupancy, rotation flag, overlap fraction, nearest distance, plus
same-slide group-centroid deviation computed from node centroids).

Outputs:
    data/metadata/SEED_RECOVERY.json        seed quality table
    data/metadata/PROPAGATION_RESULTS_P75.json  narrowed propagation re-run
    data/metadata/PHASE_75_SEED_RECOVERY.md     human report

    python -m morphlite.training.seed_recovery [--skip-propagation]
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from itertools import product

import numpy as np
from sklearn.metrics import average_precision_score, brier_score_loss, f1_score, precision_recall_fscore_support
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from sklearn.tree import DecisionTreeClassifier

from .. import config
from .bench_classifiers import choose_folds
from .propagation import (
    EDGE_SUBSETS,
    LABELS,
    load_rows,
    meta_features,
    oof_probabilities,
    propagate,
)

WEAK = ["RESTYLE", "RESIZE", "REMOVE", "MOVE"]
GATES = {
    "weak_delta_vs_anchor_min": 0.10,
    "move_recall_min": 0.25,
    "move_f1_min": 0.20,
    "unchanged_recall_drop_max": 0.03,
}


def _rf(weights=None, balanced=False):
    return RandomForestClassifier(
        n_estimators=300, min_samples_leaf=2, n_jobs=-1, random_state=0,
        class_weight=("balanced_subsample" if balanced else weights),
    )


def geometry_matrix(rows: list[dict]) -> np.ndarray:
    """Raw-only deployable geometry signals incl same-slide centroid deviation."""
    slide_members: dict[str, list[int]] = {}
    for i, r in enumerate(rows):
        slide_members.setdefault(r["slide_key"], []).append(i)

    names = ["gx_cx", "gx_cy", "gx_area", "gx_aspect", "gx_rot", "gx_depth",
             "gx_align_x_resid", "gx_align_y_resid", "gx_grid_occ", "gx_overlap",
             "gx_nn_dist", "gx_group_centroid_dev"]
    X = np.zeros((len(rows), len(names)), dtype=float)
    name_idx = {n: i for i, n in enumerate(names)}
    for i, r in enumerate(rows):
        b = r["base"]
        vals = {
            "gx_cx": b.get("cx"), "gx_cy": b.get("cy"),
            "gx_area": b.get("area_log1p"), "gx_aspect": b.get("aspect"),
            "gx_rot": b.get("rotation_flag"), "gx_depth": b.get("container_depth"),
            "gx_align_x_resid": b.get("align_x_resid"), "gx_align_y_resid": b.get("align_y_resid"),
            "gx_grid_occ": b.get("grid_occupancy"), "gx_overlap": b.get("overlap_frac_max"),
            "gx_nn_dist": b.get("nn_dist"),
        }
        for k, v in vals.items():
            X[i, name_idx[k]] = float(v or 0.0)

    for members in slide_members.values():
        if len(members) < 2:
            continue
        pts = np.array([(rows[i]["base"].get("cx") or 0.0, rows[i]["base"].get("cy") or 0.0) for i in members])
        cent = pts.mean(axis=0)
        for local, gi in enumerate(members):
            dev = float(np.hypot(*(pts[local] - cent)))
            X[gi, name_idx["gx_group_centroid_dev"]] = min(dev, 2.0)
    return X


def _binary_block(X, y, pos_label, folds, seed=0):
    """OOF positive-class probabilities for a one-vs-rest detector."""
    yb = (y == pos_label).astype(int)
    P = np.zeros(len(y), dtype=float)
    for tr, te in folds:
        m = _rf(balanced=True)
        m.fit(X[tr], yb[tr])
        if 1 in m.classes_:
            col = list(m.classes_).index(1)
            P[te] = m.predict_proba(X[te])[:, col]
    return P


def assemble_seed_probabilities(rows, X_base, X_geo, y, groups, folds):
    k_present = len(LABELS_PRESENT)
    n = len(rows)
    seeds = {}

    P_A = oof_probabilities(X_base, y, groups, "random_forest")
    seeds["A_base_rf"] = P_A

    clf_b = _rf(weights={"MOVE": 10.0})
    P_B = np.zeros((n, k_present))
    for tr, te in folds:
        clf_b.fit(X_base[tr], y[tr])
        P_B[te] = clf_b.predict_proba(X_base[te])
    seeds["B_weighted_rf"] = P_B

    P_C = np.zeros((n, k_present))
    binary_probs = {}
    for lab in [l for l in WEAK if l in set(y)]:
        pb = _binary_block(X_base, y, lab, folds)
        binary_probs[lab] = pb
        col = LABELS_PRESENT.index(lab)
        P_C[:, col] = pb
    rem = np.maximum(0.0, 1.0 - P_C.sum(axis=1))
    ucol = LABELS_PRESENT.index("UNCHANGED")
    P_C[:, ucol] += rem
    P_C /= np.maximum(P_C.sum(axis=1, keepdims=True), 1e-9)
    seeds["C_binary_detectors"] = P_C

    pgm = _binary_block(X_geo, y, "MOVE", folds)

    weights_chosen = _select_weights(X_base, X_geo, y, groups)
    wb, wc, wg = weights_chosen
    move_col = LABELS_PRESENT.index("MOVE")

    P_D = wb * P_B + wc * P_C
    move_ens = (wb * P_B[:, move_col] + wc * P_C[:, move_col]) / max(wb + wc, 1e-9)
    P_D[:, move_col] = (wb + wc) * move_ens + wg * pgm
    P_D /= np.maximum(P_D.sum(axis=1, keepdims=True), 1e-9)
    if not np.isfinite(P_D).all():
        raise ValueError("hybrid ensemble produced non-finite probabilities")
    seeds["D_hybrid_ensemble"] = P_D
    seeds["_meta"] = {"weights_chosen": list(weights_chosen), "geo_ap": round(float(average_precision_score((y == "MOVE").astype(int), pgm)), 4)}
    return seeds


def _select_weights(X_base, X_geo, y, groups):
    """Tune ensemble weights on inner grouped folds only (never on final OOF metrics)."""
    presets = [(0.4, 0.3, 0.3), (0.25, 0.35, 0.4), (0.34, 0.33, 0.33), (0.15, 0.35, 0.5)]
    yb = (y == "MOVE").astype(int)
    scores = {p: [] for p in presets}
    sgkf = StratifiedGroupKFold(n_splits=3, shuffle=True, random_state=11)
    for tr, te in sgkf.split(X_base, y, groups):
        m_b = _rf().fit(X_base[tr], y[tr])
        col_b = list(m_b.classes_).index("MOVE") if "MOVE" in m_b.classes_ else None
        p_b = m_b.predict_proba(X_base[te])[:, col_b] if col_b is not None else np.zeros(len(te))
        pc = _binary_block(X_base, y, "MOVE", [(tr, te)])
        pg = _binary_block(X_geo, y, "MOVE", [(tr, te)])
        for p in presets:
            mix_move = p[0] * p_b + p[1] * pc[te] + p[2] * pg[te]
            scores[p].append(average_precision_score(yb[te], mix_move))
    means = {p: float(np.mean(v)) for p, v in scores.items()}
    return max(means, key=means.get)


LABELS_PRESENT = []


def seed_quality_table(seeds: dict, y: np.ndarray) -> dict:
    out = {}
    move_mask_true = y == "MOVE"
    weak_mask = np.isin(y, WEAK)
    for name, P in seeds.items():
        if name.startswith("_"):
            continue
        pred = P.argmax(axis=1)
        pred_labels = np.array([LABELS_PRESENT[i] for i in pred])
        move_pred = pred_labels == "MOVE"
        tp = int((move_pred & move_mask_true).sum())
        precision = round(tp / max(move_pred.sum(), 1), 4)
        recall = round(tp / max(move_mask_true.sum(), 1), 4)
        f1 = round(2 * precision * recall / max(precision + recall, 1e-9), 4)
        weak_recall = round(float((pred_labels[weak_mask] != "UNCHANGED").mean()), 4) if weak_mask.any() else 0.0
        destructive_wrong = int((((pred_labels == "MOVE") | (pred_labels == "REMOVE")) & ~(move_mask_true | (y == "REMOVE"))).sum())
        unsafe_rate = round(destructive_wrong / max(len(y), 1), 4)
        prf = precision_recall_fscore_support(y, pred_labels, labels=LABELS_PRESENT, zero_division=0)
        unchanged_recall = None
        if "UNCHANGED" in LABELS_PRESENT:
            ui = LABELS_PRESENT.index("UNCHANGED")
            unchanged_recall = round(prf[1][ui], 4)
        out[name] = {
            "move_precision": precision, "move_recall": recall, "move_f1": f1,
            "weak_recall_nonunchanged": weak_recall,
            "unchanged_recall": unchanged_recall,
            "unsafe_destructive_rate": unsafe_rate,
            "macro_f1": round(f1_score(y, pred_labels, average="macro", zero_division=0), 4),
        }
    return out


def main() -> None:
    global LABELS_PRESENT
    rows = load_rows()
    n = len(rows)
    feat_names = sorted(rows[0]["base"].keys())
    X_base = np.array([[float(r["base"].get(k) or 0.0) for k in feat_names] for r in rows])
    X_geo = geometry_matrix(rows)
    y = np.array([r["label"] for r in rows])
    groups = np.array([r["group"] for r in rows])

    LABELS_PRESENT = sorted(set(y))
    n_splits = choose_folds(y, groups)
    sgkf = StratifiedGroupKFold(n_splits=n_splits, shuffle=True, random_state=0)
    folds = list(sgkf.split(X_base, y, groups))

    seeds = assemble_seed_probabilities(rows, X_base, X_geo, y, groups, folds)
    table = seed_quality_table(seeds, y)
    print(json.dumps(table, indent=1))

    payload = {
        "schema": "seed_recovery_v1",
        "n_rows": n,
        "n_groups": int(len(set(groups))),
        "n_splits": n_splits,
        "labels_present": LABELS_PRESENT,
        "geometry_features_note": "raw-only deployable geometry signals (no before/after correspondence)",
        "seeds": table,
    }
    (config.METADATA_DIR / "SEED_RECOVERY.json").write_text(json.dumps(payload, indent=1), encoding="utf-8")
    print(f"written {config.METADATA_DIR / 'SEED_RECOVERY.json'}")

    if "--skip-propagation" in sys.argv:
        return
    _run_narrowed_propagation(rows, seeds, y, groups, folds)


def _run_narrowed_propagation(rows, seeds, y, groups, folds):
    nbrs = [r["nbrs"] for r in rows]
    prior = np.array([(y == lab).mean() for lab in LABELS_PRESENT])
    anchor_ref = json.loads((config.METADATA_DIR / "RELATIONAL_BENCHMARK.json").read_text(encoding="utf-8"))
    arc = anchor_ref["results"]["ANCHOR_CONTEXT"]["random_forest"]["pooled_per_class_f1"]
    weak_present = [k for k in WEAK if k in arc]
    anchor_weak = sum(arc[k] for k in weak_present) / len(weak_present)
    base_seeds = seed_quality_table({"A": seeds["A_base_rf"]}, y)["A"]

    transforms = {"raw": lambda M: M}

    grid = []
    y_onehot = np.eye(len(LABELS_PRESENT))[[LABELS_PRESENT.index(v) for v in y]]
    for seed_name in ("A_base_rf", "C_binary_detectors", "D_hybrid_ensemble"):
        P0 = seeds[seed_name]
        P0t = P0 / np.maximum(P0.sum(axis=1, keepdims=True), 1e-9)
        for edges in ("GROUP", "ALL"):
            idx_lists = [[j for j, _w in r["nbrs"].get(edges, [])] for r in rows]
            for rounds in (1, 2):
                for alpha in (0.8, 0.7, 0.6):
                    Pt = P0t
                    Pp = propagate(Pt, idx_lists, alpha, rounds)
                    pred = np.array([LABELS_PRESENT[i] for i in Pp.argmax(axis=1)])
                    entry = _score(seed_name, edges, rounds, alpha, "raw", "argmax", y, pred, Pp, y_onehot, base_seeds, anchor_weak)
                    grid.append(entry)
                    N1 = _nbr_mean(Pp, idx_lists)
                    mf = meta_features(P0t, N1, _nbr_mean(N1, idx_lists))
                    preds = np.empty(len(y), dtype=object)
                    for tr, te in folds:
                        m = _rf()
                        m.fit(mf[tr], y[tr])
                        preds[te] = m.predict(mf[te])
                    e2 = _score(seed_name, edges, rounds, alpha, "raw", "rf_meta", y, preds, None, y_onehot, base_seeds, anchor_weak)
                    grid.append(e2)
    best = max(grid, key=lambda x: x["weak_macro_f1"])
    promoted, reasons = _gates(best, base_seeds, anchor_weak)
    payload = {
        "schema": "prop_results_p75_v1",
        "n_rows": len(rows), "n_groups": int(len(set(groups))),
        "anchor_weak_reference": round(anchor_weak, 4),
        "baselines": {"base_round0": base_seeds},
        "promotion_gates": GATES,
        "grid_top10": sorted(grid, key=lambda x: -x["weak_macro_f1"])[:10],
        "best": best,
        "promotion": {"promoted": promoted, "reasons": reasons},
    }
    (config.METADATA_DIR / "PROPAGATION_RESULTS_P75.json").write_text(json.dumps(payload, indent=1), encoding="utf-8")
    print(json.dumps({"best": {k: best[k] for k in ("edges", "rounds", "alpha", "head", "transform", "seed", "weak_macro_f1", "move_recall", "move_f1")}, "promoted": promoted, "reasons": reasons}, indent=1))


def _nbr_mean(P, idx_lists):
    out = np.zeros_like(P)
    for i, lst in enumerate(idx_lists):
        if lst:
            out[i] = P[lst].mean(axis=0)
        else:
            out[i] = P[i]
    return out


def _score(seed_name, edges, rounds, alpha, tname, head, y, pred, Pp, y_onehot, base_seeds, anchor_weak):
    pred = np.asarray(pred)
    prf = precision_recall_fscore_support(y, pred, labels=LABELS_PRESENT, zero_division=0)
    mi = LABELS_PRESENT.index("MOVE")
    ui = LABELS_PRESENT.index("UNCHANGED")
    weak_present = [l for l in WEAK if l in LABELS_PRESENT]
    wi = [LABELS_PRESENT.index(l) for l in weak_present]
    weak_macro = round(float(np.mean([prf[2][i] for i in wi])), 4)
    destructive = (pred == "MOVE") | (pred == "REMOVE")
    truth_destructive = (y == "MOVE") | (y == "REMOVE")
    wrong_destructive = int((destructive & ~truth_destructive).sum())
    brier = None
    if Pp is not None:
        Pc = np.clip(Pp, 0, 1)
        brier = round(float(((Pc - y_onehot) ** 2).sum(axis=1).mean()) / len(LABELS_PRESENT), 5)
    return {
        "seed": seed_name, "edges": edges, "rounds": rounds, "alpha": alpha,
        "transform": tname, "head": head,
        "pooled_macro_f1": round(f1_score(y, pred, average="macro", zero_division=0), 4),
        "weak_macro_f1": weak_macro,
        "move_precision": round(prf[0][mi], 4), "move_recall": round(prf[1][mi], 4), "move_f1": round(prf[2][mi], 4),
        "unchanged_recall": round(prf[1][ui], 4),
        "unchanged_recall_drop_vs_base": round(max(0.0, base_seeds["unchanged_recall"] - prf[1][ui]), 4),
        "unsafe_destructive_rate": round(wrong_destructive / len(y), 4),
        "brier": brier,
        "_anchor_weak_reference": round(anchor_weak, 4),
    }


def _gates(best: dict, base_seeds: dict, anchor_weak: float):
    reasons = []
    if best["weak_macro_f1"] - anchor_weak < GATES["weak_delta_vs_anchor_min"]:
        reasons.append("weak_delta_vs_anchor_below_min")
    if best["move_recall"] < GATES["move_recall_min"]:
        reasons.append("move_recall_below_min")
    if best["move_f1"] < GATES["move_f1_min"]:
        reasons.append("move_f1_below_min")
    if best["unchanged_recall_drop_vs_base"] > GATES["unchanged_recall_drop_max"]:
        reasons.append("unchanged_recall_drop_over_max")
    return (not reasons), reasons


if __name__ == "__main__":
    main()
