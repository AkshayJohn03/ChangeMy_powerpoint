# Propagation Experiment Report (Phase 7)

Aggregate statistics only; no deck or client identifiers.

## Protocol

- rows: 7350
- groups: 39
- CV splits: 5
- seed: 0
- labels (7): ADD, MOVE, RECOLOR, REMOVE, RESIZE, RESTYLE, UNCHANGED

## Baselines

| metric | base_rf_round0 |
|---|---|
| pooled_macro_f1 | 0.3800 |
| weak_macro_f1 | 0.3502 |
| move_precision | 0.1333 |
| move_recall | 0.0045 |
| move_f1 | 0.0088 |
| unchanged_recall | 0.9598 |
| unsafe_rate | 0.0156 |
| brier | 0.0544 |

Anchor reference (RELATIONAL_BENCHMARK ANCHOR_CONTEXT random_forest): cv_macro_f1_mean=0.4191, weak_macro_f1=0.3568 (mean of pooled per-class F1 over RESTYLE, RESIZE, REMOVE, MOVE present).

## Grid summary

192 configs evaluated; TOP 10 by weak_macro_f1 desc:

| rounds | alpha | edges | head | macro | weak | moveP | moveR | moveF1 | unchanged_recall | unsafe_rate | brier |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.7000 | GROUP | argmax | 0.3805 | 0.3508 | 0.1333 | 0.0045 | 0.0088 | 0.9604 | 0.0155 | 0.0543 |
| 2 | 0.9000 | GROUP | argmax | 0.3804 | 0.3508 | 0.1333 | 0.0045 | 0.0088 | 0.9602 | 0.0154 | 0.0543 |
| 2 | 0.8000 | GROUP | argmax | 0.3805 | 0.3508 | 0.1333 | 0.0045 | 0.0088 | 0.9604 | 0.0155 | 0.0543 |
| 3 | 0.9000 | GROUP | argmax | 0.3805 | 0.3508 | 0.1333 | 0.0045 | 0.0088 | 0.9604 | 0.0155 | 0.0543 |
| 1 | 0.8000 | GROUP | argmax | 0.3803 | 0.3506 | 0.1333 | 0.0045 | 0.0088 | 0.9600 | 0.0155 | 0.0543 |
| 1 | 0.6000 | GROUP | argmax | 0.3803 | 0.3506 | 0.1333 | 0.0045 | 0.0088 | 0.9606 | 0.0155 | 0.0543 |
| 2 | 0.7000 | GROUP | argmax | 0.3803 | 0.3506 | 0.1333 | 0.0045 | 0.0088 | 0.9606 | 0.0155 | 0.0543 |
| 2 | 0.6000 | GROUP | argmax | 0.3803 | 0.3506 | 0.1333 | 0.0045 | 0.0088 | 0.9606 | 0.0155 | 0.0543 |
| 3 | 0.8000 | GROUP | argmax | 0.3803 | 0.3506 | 0.1333 | 0.0045 | 0.0088 | 0.9606 | 0.0155 | 0.0543 |
| 3 | 0.7000 | GROUP | argmax | 0.3803 | 0.3506 | 0.1333 | 0.0045 | 0.0088 | 0.9606 | 0.0155 | 0.0543 |

## Best configuration & promotion decision

- best config: rounds=1 alpha=0.7 edges=GROUP head=argmax weak_macro_f1=0.3508
- promoted: False
- failure reasons: weak_delta_vs_anchor_below_min, move_recall_below_min, move_f1_below_min

| gate | measured | op | threshold -> verdict |
|---|---|---|---|
| weak_delta_vs_anchor_min | -0.0060 | >= | 0.1000 -> FAIL |
| move_recall_min | 0.0045 | >= | 0.2500 -> FAIL |
| move_f1_min | 0.0088 | >= | 0.2000 -> FAIL |
| unchanged_recall_drop_max | -0.0006 | <= | 0.0300 -> PASS |

## Interpretation guidance

NO-GO: iterative propagation of OOF predicted probabilities does not recover oracle-context performance at current label/model quality; do not proceed to neural MorphNet. Recommended investment: more validated pairs, better correspondence, manual review loop.

## Safety & calibration

- unsafe rate: base=0.0156 vs best=0.0155 (delta -0.0001)
- brier: round0=0.0544 vs best=0.0543 (delta -0.0001)
- unchanged recall delta vs base: 0.0006

## Determinism & integrity

- determinism_check: True
- v2 node dataset: n_samples=7888 unique_groups=39 duplicate_sample_ids=0 groups_spanning_splits=0
- gate no_leakage: PASS
