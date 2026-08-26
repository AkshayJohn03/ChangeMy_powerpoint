"""Phase 14: Per-node transformation model with relational features.

Architecture:
    Binary MOVE detector (hardest class)
    Binary REMOVE detector (destructive, needs high precision)
    Multiclass classifier (RESTYLE/RESIZE/RECOLOR/PRESERVE)

All use: V2 node features + relational features + slide type feature.
Evaluated with grouped CV (deck-family groups).

    python -m morphlite.training.train_node_model
"""
from __future__ import annotations

import json
import os
import sys
from collections import Counter
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.metrics import classification_report, f1_score, precision_recall_fscore_support
from sklearn.model_selection import StratifiedGroupKFold

sys.path.insert(0, ".")

from morphlite.training.propagation import load_rows
from morphlite.training.dataset_builder import truth_node_labels, label_from_tags

PRIORITY = [
    ("REMOVE", {"STRUCTURE_REMOVE"}),
    ("RESIZE", {"TYPOGRAPHY_FONT_SIZE", "GEOMETRY_RESIZE"}),
    ("MOVE", {"GEOMETRY_TRANSLATE"}),
    ("RECOLOR", {"TYPOGRAPHY_COLOR", "STYLE_FILL"}),
    ("RESTYLE", {"TYPOGRAPHY_FONT_FAMILY", "TYPOGRAPHY_WEIGHT", "CONTENT_REWRITE"}),
]

SLIDE_TYPES = ["TITLE", "AGENDA", "GENERIC_CONTENT", "GENERIC_MINIMAL",
               "CASE_STUDY", "SECTION_SPLITTER", "THANK_YOU", "WHO_WE_ARE"]

RELATIONAL_FEATURES = [
    "nn3_mean", "align_x_resid", "align_y_resid", "overlap_frac_max",
    "same_type_frac", "grid_occupancy", "deg_all",
    "nbr_text_frac", "nbr_eff_delta_mean", "nbr_cxdist_mean",
    "nbr_cydist_mean", "nbr_overlap_mean", "nbr_area_delta_mean",
    "nbr_image_frac",
]


def load_training_data():
    rows = load_rows()  # propagation cache: sample_id, group, label, slide_key, base, nbrs
    truth = truth_node_labels()

    X_base = []
    X_rel = []
    y = []
    groups = []
    slide_keys = []

    for r in rows:
        base = r["base"]
        nbrs = r.get("nbrs", {}).get("ALL", [])
        feat_base = [float(base.get(k) or 0.0) for k in sorted(base.keys())]

        # Relational features from neighbors
        nbr_idxs = [j for j, _w in nbrs]
        if nbr_idxs:
            nbr_bases = [rows[j]["base"] for j in nbr_idxs if j < len(rows)]
            deg = len(nbr_idxs)
            nbr_text_frac = sum(1 for nb in nbr_bases if nb.get("is_text")) / max(deg, 1)
            nbr_eff = [float(nb.get("eff_size_pt") or 0) for nb in nbr_bases if nb.get("eff_size_pt")]
            own_eff = float(base.get("eff_size_pt") or 0)
            nbr_eff_delta = (sum(nbr_eff) / max(len(nbr_eff), 1)) - own_eff if nbr_eff else 0.0
            cxs = [float(nb.get("cx") or 0) for nb in nbr_bases]
            cys = [float(nb.get("cy") or 0) for nb in nbr_bases]
            own_cx = float(base.get("cx") or 0)
            own_cy = float(base.get("cy") or 0)
            cxd = sum(abs(own_cx - c) for c in cxs) / max(len(cxs), 1)
            cyd = sum(abs(own_cy - c) for c in cys) / max(len(cys), 1)
            nbr_ovl = sum(float(nb.get("overlap_frac_max") or 0) for nb in nbr_bases) / max(deg, 1)
            nbr_area = sum(float(nb.get("area_log1p") or 0) for nb in nbr_bases) / max(deg, 1)
            own_area = float(base.get("area_log1p") or 0)
            nbr_area_delta = nbr_area - own_area
            nbr_img = sum(1 for nb in nbr_bases if nb.get("is_image")) / max(deg, 1)
        else:
            deg = 0
            nbr_text_frac = 0.0
            nbr_eff_delta = 0.0
            cxd = 0.0
            cyd = 0.0
            nbr_ovl = 0.0
            nbr_area_delta = 0.0
            nbr_img = 0.0

        X_base.append(feat_base)
        X_rel.append([deg, nbr_text_frac, nbr_eff_delta, cxd, cyd, nbr_ovl, nbr_area_delta, nbr_img])
        groups.append(r["group"])
        slide_keys.append(r["slide_key"])

        # Label
        entry = truth.get(r["sample_id"])
        if entry:
            y.append(label_from_tags(entry["tags"]))
        else:
            y.append("UNCHANGED")

    return (
        np.array(X_base), np.array(X_rel),
        np.array(y), np.array(groups),
        np.array(slide_keys), sorted(rows[0]["base"].keys()),
    )


def get_slide_type_features(slide_keys: list[str], n_types: int = len(SLIDE_TYPES)) -> np.ndarray:
    """One-hot encode slide types. Since we don't have per-row slide type in cache,
    we use slide_key hash as a proxy. In production, this comes from the classifier."""
    # For now, derive a simple hash-based feature (will be replaced by real classifier output)
    # This is a placeholder — real slide type should come from the ML classifier
    st = np.zeros((len(slide_keys), n_types))
    for i, sk in enumerate(slide_keys):
        # Use slide position within deck as a proxy for type
        try:
            slide_num = int(sk.rsplit("__s", 1)[1].split("__")[0])
        except (ValueError, IndexError):
            slide_num = 0
        st[i, 0] = 1 if slide_num == 1 else 0  # first slide = likely title
        st[i, 1] = 1 if slide_num == 2 else 0  # second = likely agenda
        st[i, 2] = 1 if slide_num >= 3 else 0  # rest = content
    return st


def train_binary_detector(X, y_binary, groups, model_name: str):
    """Train a binary detector with grouped CV. Returns OOF probabilities."""
    sgkf = StratifiedGroupKFold(n_splits=3, shuffle=True, random_state=0)
    P = np.zeros(len(y_binary))
    for tr, te in sgkf.split(X, y_binary, groups):
        if model_name == "rf":
            m = RandomForestClassifier(n_estimators=300, min_samples_leaf=2,
                                       class_weight="balanced", random_state=0, n_jobs=-1)
        else:
            m = HistGradientBoostingClassifier(max_depth=4, random_state=0)
        m.fit(X[tr], y_binary[tr])
        if 1 in m.classes_:
            P[te] = m.predict_proba(X[te])[:, list(m.classes_).index(1)]
    return P


def main() -> None:
    print("=== Phase 14: Per-node transformation model ===\n")

    X_base, X_rel, y, groups, slide_keys, feat_names = load_training_data()
    X_slide = get_slide_type_features(slide_keys)

    # Combine features
    X_full = np.hstack([X_base, X_rel, X_slide])
    print(f"samples={len(y)} features={X_full.shape[1]} groups={len(set(groups))}")
    print(f"labels: {dict(Counter(y))}")

    # Binary labels
    y_move = (y == "MOVE").astype(int)
    y_remove = (y == "REMOVE").astype(int)

    # CV folds
    n_splits = max(2, min(3, min(Counter(y).values()), len(set(groups))))
    sgkf = StratifiedGroupKFold(n_splits=n_splits, shuffle=True, random_state=0)
    folds = list(sgkf.split(X_full, y, groups))

    # --- Multiclass model (all 6 classes) ---
    print("\n--- Multiclass model ---")
    y_pred_mc = np.empty(len(y), dtype=object)
    for tr, te in folds:
        m = RandomForestClassifier(n_estimators=300, min_samples_leaf=2,
                                   class_weight="balanced_subsample", random_state=0, n_jobs=-1)
        m.fit(X_full[tr], y[tr])
        y_pred_mc[te] = m.predict(X_full[te])
    mc_f1 = f1_score(y, y_pred_mc, average="macro", zero_division=0)
    print(f"  macro F1: {mc_f1:.4f}")
    prf = precision_recall_fscore_support(y, y_pred_mc, labels=sorted(set(y)), zero_division=0)
    for lab, p, r, f in zip(sorted(set(y)), prf[0], prf[1], prf[2]):
        print(f"    {lab:12s} P={p:.3f} R={r:.3f} F1={f:.3f}")

    # --- Binary MOVE detector ---
    print("\n--- Binary MOVE detector ---")
    P_move = train_binary_detector(X_full, y_move, groups, "rf")
    best_move_t, best_move_f1 = 0.5, 0.0
    for t in [0.2, 0.3, 0.4, 0.5, 0.6]:
        pred = (P_move >= t).astype(int)
        f1 = f1_score(y_move, pred, zero_division=0)
        prec = precision_recall_fscore_support(y_move, pred, average="binary", zero_division=0)[0]
        print(f"  threshold={t:.2f} F1={f1:.3f} precision={prec:.3f} recall={sum(pred & y_move)/max(sum(y_move),1):.3f}")
        if f1 > best_move_f1:
            best_move_f1, best_move_t = f1, t

    # --- Binary REMOVE detector ---
    print("\n--- Binary REMOVE detector ---")
    y_remove_bin = (y == "REMOVE").astype(int)
    P_remove = train_binary_detector(X_full, y_remove_bin, groups, "rf")
    best_rem_t, best_rem_f1 = 0.5, 0.0
    for t in [0.3, 0.4, 0.5, 0.6, 0.7]:
        pred = (P_remove >= t).astype(int)
        f1 = f1_score(y_remove_bin, pred, zero_division=0)
        prec = precision_recall_fscore_support(y_remove_bin, pred, average="binary", zero_division=0)[0]
        print(f"  threshold={t:.2f} F1={f1:.3f} precision={prec:.3f} recall={sum(pred & y_remove_bin)/max(sum(y_remove_bin),1):.3f}")
        if f1 > best_rem_f1:
            best_rem_f1, best_rem_t = f1, t

    # --- Save production model ---
    print("\n--- Training final model on ALL data ---")
    final_multiclass = RandomForestClassifier(
        n_estimators=400, min_samples_leaf=2,
        class_weight="balanced_subsample", random_state=0, n_jobs=-1)
    final_multiclass.fit(X_full, y)

    final_move = RandomForestClassifier(
        n_estimators=300, min_samples_leaf=2,
        class_weight="balanced", random_state=0, n_jobs=-1)
    final_move.fit(X_full, y_move)

    final_remove = RandomForestClassifier(
        n_estimators=300, min_samples_leaf=2,
        class_weight="balanced", random_state=0, n_jobs=-1)
    final_remove.fit(X_full, y_remove_bin)

    MODELS_DIR = Path("models")
    MODELS_DIR.mkdir(exist_ok=True)

    joblib.dump({
        "multiclass": final_multiclass,
        "move_detector": final_move,
        "remove_detector": final_remove,
        "feature_names_base": feat_names,
        "feature_names_rel": RELATIONAL_FEATURES,
        "labels": sorted(set(y)),
        "schema_version": "node_model_v2",
        "move_threshold": best_move_t,
        "remove_threshold": best_rem_t,
    }, MODELS_DIR / "brandmorph_node_model_v2.joblib")

    card = {
        "schema_version": "node_model_v2",
        "created_at": datetime_now(),
        "n_samples": len(y),
        "n_features": X_full.shape[1],
        "feature_groups": {
            "base_v2": len(feat_names),
            "relational": len(RELATIONAL_FEATURES),
            "slide_type": 3,
        },
        "multiclass_macro_f1": round(mc_f1, 4),
        "move_detector": {"best_threshold": best_move_t, "best_f1": round(best_move_f1, 4)},
        "remove_detector": {"best_threshold": best_rem_t, "best_f1": round(best_rem_f1, 4)},
    }
    (MODELS_DIR / "brandmorph_node_model_v2.json").write_text(json.dumps(card, indent=1))
    print(f"\nmodel saved: {MODELS_DIR}/brandmorph_node_model_v2.joblib")
    print(json.dumps(card, indent=1))


def datetime_now():
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


from collections import Counter

if __name__ == "__main__":
    main()
