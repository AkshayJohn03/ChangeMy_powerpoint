# Models

All trained intent/node models are currently **NOT_PROMOTED**. Promotion is
decided by gates (min CV score, minority-class F1, size, latency), never by
best-mean alone.

## Features

- Base node features (`features/node_features.py`): geometry, typography,
  color, position — 33 feats.
- v2 adds relational + effective features (`node_features_v2.py`,
  `graph/features.py`): 14 relational over 9 slide-graph edge types
  (axis alignment, nearest neighbours, same-group, contains, overlaps) +
  effective-typography features — 49 feats total (`FEATURE_SCHEMA.json`).
- Deck/slide features (`deck_features*.py`), geometry fingerprints
  (`fingerprint.py`), slide-context variants (ablated, see verdicts).

## Datasets (aggregate only)

- Node dataset v2: **7,888 rows**, label mix approx UNCHANGED ~67%,
  RESIZE ~12%, REMOVE ~9%, ADD ~7%, MOVE ~6%, RESTYLE/RECOLOR <1%.
- Intent set: 74 slide groups. Slide-type set: 422 slides / 30 decks.
- Split: grouped by deck (train/val/test), zero leakage by construction;
  `tests/test_no_leakage.py` is the gate.

## Bake-off (grouped 5-fold, macro F1)

| Model | Macro F1 | Note |
|---|---|---|
| xgboost (300 trees, d6) | 0.469 | tie best |
| RF-200 (baseline) | 0.469 | baseline |
| lightgbm | 0.468 | — |
| HistGBDT | 0.442 | smallest sklearn (~2MB), best MOVE among sklearn |
| mlp_small (128,64) | 0.410 | ~128k params, close to RF |
| logreg | 0.329 | floor |
| dummy | 0.114 | sanity |

Strong classes: REMOVE ~0.63–0.66, RESIZE ~0.55, UNCHANGED ~0.84.
Weak classes: MOVE/RESTYLE/RECOLOR (tiny support) drag macro down.

## Small neural variants (code-ready)

`training/model_bakeoff.py` contains GNN (2-layer GCN, ~12k params), LSTM
(~40k), Tiny Transformer (~50k, scalable to ~5M) — all CPU-sized (<50MB,
<1s/slide). Pending: torch install + synthetic-augmented retrain.

## Key experimental verdicts

- **Phase 7:** OOF-probability propagation — NO-GO at current seed quality.
- **Phase 7.5/7.7:** MOVE misses are axis-pure small displacements of
  non-text shapes; raw-side signal weak (AUC ≤ 0.64).
- **Phase 8/9:** micro-nudge and slide-context hypotheses falsified;
  misses are medium structural moves with uniform ambiguity.
- **Phase 12–12.7:** end-to-end pipeline + mutation truth layer; REMOVE
  dominates verified mutations (~58%), RECOLOR never fires.
- **Phase 13:** slide-type classifier wired into template pipeline.
- **Phase 14:** per-node v2 (relational) — REMOVE F1 0.66 @ 0.50.

## Promotion gates (`bench_classifiers*.py`)

Intent: min CV 0.55, minority 0.40, ≤5MB, ≤20ms. Node: 0.45 / 0.30 /
≤25MB / ≤20ms. Track per-class F1: ship only when MOVE ≥ 0.20 and
RESTYLE ≥ 0.30.

## Recommended next training step

Synthetic 3x from golden pairs (content shuffle, plausible archetype swap,
style jitter; flagged `synthetic=1`) → class-weighted/focal + SMOTE on
minorities → ensemble HGB + GNN → re-gate.
