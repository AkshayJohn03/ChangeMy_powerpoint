"""Phase 5: V2 benchmark run using the identical V1 protocol.

    python -m morphlite.training.bench_classifiers_v2
"""
from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score

from .. import config
from .bench_classifiers import (
    MODELS_DIR,
    load_rows,
    model_zoo,
    promotion_decision,
    repeated_group_cv,
    vectorize,
)

PROCESSED = config.DATA_DIR / "processed"


def benchmark(task: str) -> tuple[dict, dict]:
    meta = json.loads((PROCESSED / "dataset_meta_v2.json").read_text(encoding="utf-8"))[task]
    rows = load_rows(f"{task}_dataset_v2.jsonl")
    feat_names = meta["features"]
    labels = sorted(meta["labels"])

    X, y, splits, groups = vectorize(rows, feat_names)
    tr, va, te = splits == "train", splits == "val", splits == "test"

    results = {}
    cv_by_name = {}
    best = None
    repeats = 3 if task == "intent" else 1
    for name in model_zoo(task):
        cv = repeated_group_cv(lambda n=name: model_zoo(task)[n], X, y, groups, repeats=repeats)
        cv_by_name[name] = cv["cv_macro_f1_mean"]
        t0 = time.time()
        model = model_zoo(task)[name]
        model.fit(X[tr], y[tr])
        fit_s = time.time() - t0

        pred_te = model.predict(X[te])
        acc = accuracy_score(y[te], pred_te)
        macro_f1 = f1_score(y[te], pred_te, average="macro", zero_division=0)

        tmp = Path(config.METADATA_DIR / f".bv2_{task}_{name}.joblib")
        joblib.dump(model, tmp)
        size_kb = round(tmp.stat().st_size / 1024, 1)
        tmp.unlink()

        rep = classification_report(y[te], pred_te, output_dict=True, zero_division=0)
        cm = confusion_matrix(y[te], pred_te, labels=labels)
        results[name] = {
            "cv": cv,
            "fit_sec": round(fit_s, 2),
            "test_accuracy": round(acc, 4),
            "test_macro_f1": round(macro_f1, 4),
            "per_class_f1": {c: round(rep[c]["f1-score"], 4) for c in labels if c in rep},
            "confusion_matrix": cm.tolist(),
            "confusion_labels": labels,
            "model_size_kb": size_kb,
        }
        print(f"[{task}] {name:22s} cv={cv['cv_macro_f1_mean']:.3f}±{cv['cv_macro_f1_std']:.3f} pooled={cv['pooled_macro_f1']:.3f} test_f1={macro_f1:.3f}")
        if best is None or cv["cv_macro_f1_mean"] > best[1]:
            best = (name, cv["cv_macro_f1_mean"], model)

    winner_name, win_cv, winner_model = best
    promoted, reasons = promotion_decision(
        task,
        {**results[winner_name], "latency_ms_per_predict": 0.0},
        cv_by_name.get("dummy_most_frequent", 0.0),
    )

    metadata = {
        "model_name": f"morphlite_{task}_v2",
        "winner": winner_name,
        "promoted": promoted,
        "not_promoted_reasons": reasons,
        "selection_metric": "grouped_cv_macro_f1_mean",
        "cv_macro_f1": win_cv,
        "feature_schema_version": "2.0.0",
        "classes": labels,
        "training_samples": int(tr.sum()),
        "total_samples": len(rows),
        "synthetic_samples": 0,
        "test_macro_f1": results[winner_name]["test_macro_f1"],
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    if promoted:
        joblib.dump(winner_model, MODELS_DIR / f"morphlite_{task}_v2.joblib")
    else:
        (MODELS_DIR / f"morphlite_{task}_v2.NOT_PROMOTED").write_text(json.dumps(reasons), encoding="utf-8")
    (MODELS_DIR / f"morphlite_{task}_v2.json").write_text(json.dumps(metadata, indent=1), encoding="utf-8")
    return results, metadata


def main() -> None:
    out_path = config.METADATA_DIR / "ML_BENCHMARKS_V2.json"
    all_results = {}
    for task in ("intent", "node"):
        print(f"=== {task.upper()} (v2) ===", flush=True)
        res, meta = benchmark(task)
        all_results[task] = {"results": res, "selected_metadata": meta}
    out_path.write_text(json.dumps(all_results, indent=1), encoding="utf-8")
    print(f"written {out_path}")


if __name__ == "__main__":
    main()
