"""Phase 10: train the production action model.

Steps:
  1. final grouped OOF evaluation (StratifiedGroupKFold k=5, family groups)
  2. per-class confidence-threshold derivation from winning OOF probabilities
  3. refit winner on ALL approved rows
  4. serialize versioned artifact + model card + feature schema + thresholds

    python -m morphlite.training.train_production
"""
from __future__ import annotations

import json
from datetime import datetime, timezone

import joblib
import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.metrics import f1_score, precision_recall_fscore_support
from sklearn.model_selection import StratifiedGroupKFold

from .. import config
from .propagation import load_rows

SCHEMA_VERSION = "action_model_v1"
WEAK = ["RESTYLE", "RESIZE", "REMOVE", "MOVE"]
NON_APPLY_CLASSES = {"UNCHANGED"}
MIN_CLASS_F1_FOR_AUTO_APPLY = 0.15
THRESHOLD_GRID = [round(float(x), 2) for x in np.arange(0.30, 0.96, 0.05)]
MODELS_DIR = config.BRANDMORPH_ROOT / "models"


def _rf():
    return RandomForestClassifier(
        n_estimators=400, min_samples_leaf=2,
        class_weight="balanced_subsample", random_state=0, n_jobs=-1,
    )


def _hgb():
    return HistGradientBoostingClassifier(max_depth=4, learning_rate=0.08, random_state=0)


def load_matrix():
    rows = load_rows()
    feat_names = sorted(rows[0]["base"].keys())
    X = np.array([[float(r["base"].get(k) or 0.0) for k in feat_names] for r in rows])
    y = np.array([r["label"] for r in rows])
    groups = np.array([r["group"] for r in rows])
    labels = sorted(set(y))
    return X, y, groups, feat_names, labels


def oof_probabilities(X, y, groups, factory, labels):
    P = np.zeros((len(y), len(labels)))
    sgkf = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=0)
    for tr, te in sgkf.split(X, y, groups):
        m = factory()
        m.fit(X[tr], y[tr])
        cols = [list(m.classes_).index(c) for c in labels]
        P[te] = m.predict_proba(X[te])[:, cols]
    return P


def pooled_metrics(y, pred, labels):
    prf = precision_recall_fscore_support(y, pred, labels=labels, zero_division=0)
    wi = [labels.index(l) for l in WEAK if l in labels]
    mi = labels.index("MOVE") if "MOVE" in labels else None
    return {
        "macro_f1": round(f1_score(y, pred, average="macro", zero_division=0), 4),
        "weak_macro_f1": round(float(np.mean([prf[2][i] for i in wi])), 4) if wi else None,
        "move_precision": round(prf[0][mi], 4) if mi is not None else None,
        "move_recall": round(prf[1][mi], 4) if mi is not None else None,
        "move_f1": round(prf[2][mi], 4) if mi is not None else None,
        "per_class_f1": {lab: round(prf[2][i], 4) for i, lab in enumerate(labels)},
    }


def derive_thresholds(y, P, labels):
    argmax_pred = np.array([labels[i] for i in P.argmax(axis=1)])
    out = {}
    for ci, lab in enumerate(labels):
        if lab in NON_APPLY_CLASSES:
            out[lab] = {"auto_apply_threshold": None, "reason": "non_apply_class"}
            continue
        truth = y == lab
        support = int(truth.sum())
        best_t, best_f1, best_prec = None, -1.0, 0.0
        for t in THRESHOLD_GRID:
            sel = P[:, ci] >= t
            tp = int((sel & truth).sum())
            fp = int((sel & ~truth).sum())
            prec = tp / max(tp + fp, 1)
            rec = tp / max(support, 1)
            f1v = 2 * prec * rec / max(prec + rec, 1e-9)
            if f1v > best_f1:
                best_f1, best_t, best_prec = f1v, t, prec
        base_recall = round(float((argmax_pred == lab)[truth].mean()), 4) if support else 0.0
        argmax_f1 = round(f1_score(y == lab, argmax_pred == lab, zero_division=0), 4)
        if best_f1 < MIN_CLASS_F1_FOR_AUTO_APPLY or best_t is None:
            out[lab] = {
                "auto_apply_threshold": None,
                "reason": "max_oof_f1_below_floor",
                "max_oof_f1_at_grid": round(best_f1, 4),
                "argmax_f1": argmax_f1,
                "base_argmax_recall": base_recall,
                "policy_class": "REVIEW_ONLY",
            }
        else:
            out[lab] = {
                "auto_apply_threshold": best_t,
                "oof_f1_at_threshold": round(best_f1, 4),
                "oof_precision_at_threshold": round(best_prec, 4),
                "argmax_f1": argmax_f1,
                "base_argmax_recall": base_recall,
                "policy_class": "APPLY_ELIGIBLE",
            }
    return out


def main() -> None:
    X, y, groups, feat_names, labels = load_matrix()
    print(f"[data] rows={len(y)} features={len(feat_names)} labels={labels}", flush=True)

    oof = {}
    metrics = {}
    for name, fac in (("random_forest", _rf), ("hist_gbdt", _hgb)):
        P = oof_probabilities(X, y, groups, fac, labels)
        pred = np.array([labels[i] for i in P.argmax(axis=1)])
        oof[name] = (P, pred)
        metrics[name] = pooled_metrics(y, pred, labels)
        print(f"[oof:{name}] {metrics[name]}", flush=True)

    winner_name = max(metrics, key=lambda k: metrics[k]["weak_macro_f1"] or -1)
    winner_fac = _rf if winner_name == "random_forest" else _hgb
    P_win = oof[winner_name][0]
    thresholds = derive_thresholds(y, P_win, labels)

    final_model = winner_fac()
    final_model.fit(X, y)

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    artifact_path = MODELS_DIR / "brandmorph_action_model.joblib"
    joblib.dump(
        {
            "model": final_model,
            "feature_names": feat_names,
            "labels": labels,
            "schema_version": SCHEMA_VERSION,
            "winner": winner_name,
            "trained_on": "full approved corpus (7350 raw-side nodes)",
        },
        artifact_path,
    )

    now = datetime.now(timezone.utc).isoformat()
    card = {
        "artifact": str(artifact_path),
        "schema_version": SCHEMA_VERSION,
        "created_at": now,
        "winner_model": winner_name,
        "trained_on_all_approved_data": True,
        "n_rows": len(y),
        "n_features": len(feat_names),
        "labels": labels,
        "selection_metric": "weak_class_macro_f1 (grouped OOF)",
        "oof_evaluation": metrics,
        "threshold_source": "winning model's grouped-OOF probabilities",
    }
    (config.METADATA_DIR / "MODEL_CARD.json").write_text(json.dumps(card, indent=1), encoding="utf-8")
    (config.METADATA_DIR / "FEATURE_SCHEMA.json").write_text(
        json.dumps({"schema_version": SCHEMA_VERSION, "feature_names": feat_names,
                    "source": "propagation_cache.base dicts (source-deck only)"}, indent=1),
        encoding="utf-8")
    policy_payload = {
        "schema_version": SCHEMA_VERSION,
        "derived_from": f"{winner_name} grouped-OOF probabilities",
        "min_class_f1_for_auto_apply": MIN_CLASS_F1_FOR_AUTO_APPLY,
        "classes": thresholds,
        "non_apply_classes": sorted(NON_APPLY_CLASSES),
    }
    (config.METADATA_DIR / "POLICY_THRESHOLDS.json").write_text(json.dumps(policy_payload, indent=1), encoding="utf-8")

    print(json.dumps({"winner": winner_name, "weak_macro_f1": metrics[winner_name]["weak_macro_f1"],
                      "artifact": str(artifact_path),
                      "apply_eligible": [l for l, v in thresholds.items() if v.get("policy_class") == "APPLY_ELIGIBLE"],
                      "review_only": [l for l, v in thresholds.items() if v.get("policy_class") == "REVIEW_ONLY"]}, indent=1))


if __name__ == "__main__":
    main()
