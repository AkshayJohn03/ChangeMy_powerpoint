"""Benchmark lightweight classifiers for the two MorphLite ML tasks.

Protocol (PDR sections 4, 23, 24):
    - deck-family-grouped train/val/test splits (no slide leakage)
    - models: Dummy baseline, DecisionTree, RandomForest, HistGradientBoosting
    - metrics: accuracy, macro F1, per-class F1, confusion, model size,
      load time, inference latency
    - winning models saved to morphlite/models/ with metadata sidecars

    python -m morphlite.training.bench_classifiers [intent|node|all]
"""
from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.tree import DecisionTreeClassifier

from .. import config
from ..features.node_features import FEATURE_SCHEMA_VERSION

PROCESSED = config.DATA_DIR / "processed"
MODELS_DIR = config.BRANDMORPH_ROOT / "morphlite" / "models"


def load_rows(name: str) -> list[dict]:
    rows = []
    with open(PROCESSED / name, encoding="utf-8") as fh:
        for line in fh:
            rows.append(json.loads(line))
    return rows


def vectorize(rows: list[dict], feature_names: list[str]):
    X = np.array([[r["features"].get(f, 0.0) or 0.0 for f in feature_names] for r in rows], dtype=float)
    y = np.array([r["label"] for r in rows])
    splits = np.array([r["split"] for r in rows])
    groups = np.array([r["group"] for r in rows])
    return X, y, splits, groups


def choose_folds(y, groups, max_folds: int = 5) -> int:
    from collections import Counter

    counts = Counter(y)
    n_groups = len(set(groups))
    return max(2, min(max_folds, min(counts.values()) or 1, n_groups))


def repeated_group_cv(model_factory, X, y, groups, n_splits: int | None = None, repeats: int = 1):
    if n_splits is None:
        n_splits = choose_folds(y, groups)
    sgkf_kwargs = dict(n_splits=n_splits, shuffle=True)

    fold_f1s_all = []
    y_true_all, y_pred_all = [], []
    for rep in range(repeats):
        sgkf = StratifiedGroupKFold(random_state=rep, **sgkf_kwargs)
        for tr_idx, te_idx in sgkf.split(X, y, groups):
            m = model_factory()
            m.fit(X[tr_idx], y[tr_idx])
            pred = m.predict(X[te_idx])
            fold_f1s_all.append(f1_score(y[te_idx], pred, average="macro", zero_division=0))
            y_true_all.extend(y[te_idx])
            y_pred_all.extend(pred)

    import numpy as _np

    y_true = _np.array(y_true_all)
    y_pred = _np.array(y_pred_all)
    labels = sorted(set(y_true) | set(y_pred))
    cm = confusion_matrix(y_true, y_pred, labels=labels)
    recalls = {}
    for i, lab in enumerate(labels):
        denom = cm[i].sum()
        recalls[lab] = round(cm[i][i] / denom, 4) if denom else 0.0
    present = [lab for lab in labels if (y_true == lab).any()]
    return {
        "n_splits": n_splits,
        "repeats": repeats,
        "cv_macro_f1_mean": round(float(_np.mean(fold_f1s_all)), 4),
        "cv_macro_f1_std": round(float(_np.std(fold_f1s_all)), 4),
        "pooled_macro_f1": round(f1_score(y_true, y_pred, average="macro", zero_division=0), 4),
        "pooled_accuracy": round(accuracy_score(y_true, y_pred), 4),
        "pooled_per_class_f1": {
            lab: round(f1_score(y_true == lab, y_pred == lab, zero_division=0), 4) for lab in present
        },
        "min_class_recall": min(recalls[lab] for lab in present) if present else 0.0,
        "pooled_labels": labels,
        "pooled_confusion": cm.tolist(),
    }


PROMOTION = {
    "intent": {"min_cv_macro_f1": 0.55, "min_minority_recall": 0.40, "max_size_mb": 5, "max_latency_ms": 20},
    "node": {"min_cv_macro_f1": 0.45, "min_minority_recall": 0.30, "max_size_mb": 25, "max_latency_ms": 20},
}


def promotion_decision(task: str, entry: dict, dummy_cv_f1: float) -> tuple[bool, list[str]]:
    pol = PROMOTION[task]
    reasons = []
    if entry["cv"]["cv_macro_f1_mean"] <= dummy_cv_f1:
        reasons.append("does_not_beat_dummy")
    if entry["cv"]["cv_macro_f1_mean"] < pol["min_cv_macro_f1"]:
        reasons.append("cv_macro_f1_below_threshold")
    if entry["cv"]["min_class_recall"] < pol["min_minority_recall"]:
        reasons.append("minority_recall_below_threshold")
    if entry["model_size_kb"] > pol["max_size_mb"] * 1024:
        reasons.append("model_too_large")
    if entry["latency_ms_per_predict"] > pol["max_latency_ms"]:
        reasons.append("latency_over_budget")
    return (not reasons), reasons


def model_zoo(task: str) -> dict:
    if task == "intent":
        return {
            "dummy_most_frequent": DummyClassifier(strategy="most_frequent"),
            "decision_tree": DecisionTreeClassifier(max_depth=4, class_weight="balanced", random_state=0),
            "random_forest": RandomForestClassifier(n_estimators=300, min_samples_leaf=2, class_weight="balanced", random_state=0, n_jobs=-1),
            "hist_gbdt": HistGradientBoostingClassifier(max_depth=3, max_iter=200, learning_rate=0.1, random_state=0),
        }
    return {
        "dummy_most_frequent": DummyClassifier(strategy="most_frequent"),
        "decision_tree": DecisionTreeClassifier(max_depth=8, min_samples_leaf=5, class_weight="balanced", random_state=0),
        "random_forest": RandomForestClassifier(n_estimators=200, min_samples_leaf=2, class_weight="balanced_subsample", random_state=0, n_jobs=-1),
        "hist_gbdt": HistGradientBoostingClassifier(max_depth=4, max_iter=250, learning_rate=0.1, random_state=0),
    }


def benchmark_task(task: str) -> tuple[dict, dict | None]:
    meta = json.loads((PROCESSED / "dataset_meta_v1.json").read_text(encoding="utf-8"))[task]
    rows = load_rows(f"{task}_dataset_v1.jsonl")
    feat_names = meta["features"]
    labels = sorted(meta["labels"])

    X, y, splits, groups = vectorize(rows, feat_names)
    tr = splits == "train"
    va = splits == "val"
    te = splits == "test"

    results = {}
    cv_by_name = {}
    best = None
    repeats = 3 if task == "intent" else 1
    for name in model_zoo(task):
        cv = repeated_group_cv(lambda n=name: model_zoo(task)[n], X, y, groups, repeats=repeats)
        cv_by_name[name] = cv["cv_macro_f1_mean"]
        model = model_zoo(task)[name]
        t0 = time.time()
        model.fit(X[tr], y[tr])
        fit_s = time.time() - t0

        pred_val = model.predict(X[va]) if va.any() else model.predict(X[te])
        ref_val = y[va] if va.any() else y[te]
        macro_val = f1_score(ref_val, pred_val, average="macro", zero_division=0)

        pred_te = model.predict(X[te])
        acc = accuracy_score(y[te], pred_te)
        macro_f1 = f1_score(y[te], pred_te, average="macro", zero_division=0)

        tmp = Path(config.METADATA_DIR / f".bench_{task}_{name}.joblib")
        joblib.dump(model, tmp)
        size_kb = round(tmp.stat().st_size / 1024, 1)

        t0 = time.time()
        _ = joblib.load(tmp)
        load_ms = round((time.time() - t0) * 1000, 1)

        sample = X[te][:1] if te.any() else X[:1]
        reps = 50
        t0 = time.time()
        for _ in range(reps):
            _ = model.predict(sample)
        lat_ms = round((time.time() - t0) * 1000 / reps, 3)
        tmp.unlink()

        rep = classification_report(y[te], pred_te, output_dict=True, zero_division=0)
        cm = confusion_matrix(y[te], pred_te, labels=labels)
        results[name] = {
            "cv": cv,
            "fit_sec": round(fit_s, 2),
            "val_macro_f1": round(macro_val, 4),
            "test_accuracy": round(acc, 4),
            "test_macro_f1": round(macro_f1, 4),
            "per_class_f1": {c: round(rep[c]["f1-score"], 4) for c in labels if c in rep},
            "confusion_matrix_labels": labels,
            "confusion_matrix": cm.tolist(),
            "model_size_kb": size_kb,
            "load_time_ms": load_ms,
            "latency_ms_per_predict": lat_ms,
        }
        print(f"[{task}] {name:22s} cv={cv['cv_macro_f1_mean']:.3f}±{cv['cv_macro_f1_std']:.3f} pooled={cv['pooled_macro_f1']:.3f} test_f1={macro_f1:.3f}")
        if best is None or cv["cv_macro_f1_mean"] > best[1]:
            best = (name, cv["cv_macro_f1_mean"], model)

    winner_name, win_cv, winner_model = best
    promoted, reasons = promotion_decision(
        task,
        {**results[winner_name], "latency_ms_per_predict": results[winner_name]["latency_ms_per_predict"]},
        cv_by_name.get("dummy_most_frequent", 0.0),
    )
    real_samples = int(sum(1 for r in rows))
    metadata = {
        "model_name": f"morphlite_{task}_v1",
        "winner": winner_name,
        "promoted": promoted,
        "not_promoted_reasons": reasons,
        "selection_metric": "grouped_cv_macro_f1_mean",
        "cv_macro_f1": win_cv,
        "feature_schema_version": FEATURE_SCHEMA_VERSION if task == "node" else "deck_v1",
        "classes": labels,
        "training_samples": int(tr.sum()),
        "total_samples": real_samples,
        "real_samples": real_samples,
        "synthetic_samples": 0,
        "test_macro_f1": results[winner_name]["test_macro_f1"],
        "test_accuracy": results[winner_name]["test_accuracy"],
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    if promoted:
        joblib.dump(winner_model, MODELS_DIR / f"morphlite_{task}_v1.joblib")
    else:
        (MODELS_DIR / f"morphlite_{task}_v1.NOT_PROMOTED").write_text(json.dumps(reasons), encoding="utf-8")
    (MODELS_DIR / f"morphlite_{task}_v1.json").write_text(json.dumps(metadata, indent=1), encoding="utf-8")

    return results, metadata


def main() -> None:
    which = (Path(__file__).name and (__import__("sys").argv[1] if len(__import__("sys").argv) > 1 else "all"))
    tasks = ["intent", "node"] if which == "all" else [which]
    all_results = {}
    for task in tasks:
        print(f"\n=== {task.upper()} ===")
        res, meta = benchmark_task(task)
        all_results[task] = {"results": res, "selected_metadata": meta}
    out = config.METADATA_DIR / "ML_BENCHMARKS.json"
    existing = json.loads(out.read_text(encoding="utf-8")) if out.exists() else {}
    existing.update(all_results)
    out.write_text(json.dumps(existing, indent=1), encoding="utf-8")
    print(f"\nwritten {out}")


if __name__ == "__main__":
    main()
