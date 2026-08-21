"""Phase C: intent feature-set ablation under repeated grouped CV.

Sets:
    A_v1_full                 original v1 deck features
    B_structural_no_names     v1 minus name-derived keys
    C_fingerprint_only        template-similarity blocks + layout usage count
    D_structural_stats_only   aggregate deck statistics (no sims, no names)
    E_v2_all                  full leakage-safe v2 vector

    python -m morphlite.training.intent_ablation
"""
from __future__ import annotations

import json

import numpy as np
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier

from .. import config
from ..features.deck_features import DECK_FEATURE_NAMES as V1_NAMES
from ..features.deck_features_v2 import DECK_BASE_NAMES, DECK_FEATURE_NAMES_V2
from .bench_classifiers import PROCESSED, choose_folds, repeated_group_cv

NAME_KEYS = {"frac_slides_known_rebuild_source", "divider_frac", "titleish_frac"}

SETS = {
    "A_v1_full": ("v1", list(V1_NAMES)),
    "B_structural_no_names": ("v1", [f for f in V1_NAMES if f not in NAME_KEYS]),
    "C_fingerprint_only": ("v2", ["n_used_layouts", "sim_topo_max", "sim_theme_max", "sim_master_max", "sim_ladder_max", "sim_weighted_max", "sim_weighted_mean"]),
    "D_structural_stats_only": ("v2", list(DECK_BASE_NAMES)),
    "E_v2_all": ("v2", list(DECK_FEATURE_NAMES_V2)),
}


def load(task_version: str) -> list[dict]:
    return [json.loads(l) for l in open(PROCESSED / f"intent_dataset_{task_version}.jsonl", encoding="utf-8")]


def main() -> None:
    data = {"v1": load("v1"), "v2": load("v2")}
    out = {}
    for set_name, (ver, feats) in SETS.items():
        rows = data[ver]
        X = np.array([[r["features"].get(f) or 0.0 for f in feats] for r in rows], dtype=float)
        y = np.array([r["label"] for r in rows])
        groups = np.array([r["group"] for r in rows])
        folds = choose_folds(y, groups)
        entry = {}
        for mname, factory in {
            "dummy": lambda: DummyClassifier(strategy="most_frequent"),
            "random_forest": lambda: RandomForestClassifier(n_estimators=300, min_samples_leaf=2, class_weight="balanced", random_state=0, n_jobs=-1),
            "hist_gbdt": lambda: HistGradientBoostingClassifier(max_depth=3, max_iter=200, learning_rate=0.1, random_state=0),
        }.items():
            cv = repeated_group_cv(factory, X, y, groups, repeats=3)
            entry[mname] = {k: cv[k] for k in ("n_splits", "repeats", "cv_macro_f1_mean", "cv_macro_f1_std", "pooled_macro_f1", "min_class_recall")}
            print(f"{set_name:26s} {mname:14s} folds={cv['n_splits']} cv={cv['cv_macro_f1_mean']:.3f}±{cv['cv_macro_f1_std']:.3f} min_recall={cv['min_class_recall']:.3f}", flush=True)
        out[set_name] = entry

    (config.METADATA_DIR / "INTENT_ABLATION.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(f"written {config.METADATA_DIR / 'INTENT_ABLATION.json'}")


if __name__ == "__main__":
    main()
