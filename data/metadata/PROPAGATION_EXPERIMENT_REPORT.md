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

---

## Phase 7.5 addendum — Seed Recovery Experiment

### What Phase 7 disproved
Naive propagation of the base model's OOF probability vectors produces no deployable improvement.

### What Phase 7 did NOT disprove
Graph learning, message passing, one-hop aggregation, or relational information itself.
Phase 6 proved true neighbour labels are highly predictive (oracle MOVE F1 0.745).

### Seed strategies tested (OOF, deck-family grouped)

| Seed | MOVE P | MOVE R | MOVE F1 | weak recall | UNCH recall | unsafe | macro F1 |
|---|---:|---:|---:|---:|---:|---:|---:|
| A base RF | 0.313 | 0.011 | 0.022 | 0.441 | 0.962 | 0.011 | 0.382 |
| B weighted RF | 0.250 | 0.095 | 0.138 | 0.406 | 0.952 | 0.019 | 0.348 |
| C binary detectors | **0.522** | 0.054 | 0.099 | 0.481 | 0.949 | 0.018 | 0.392 |
| D hybrid ensemble | 0.286 | **0.109** | **0.158** | 0.450 | 0.951 | 0.021 | **0.394** |

Geometry detector used raw-only deployable signals (no before/after correspondence).
Ensemble weights tuned on inner grouped folds only.

### Narrowed propagation re-run (Phase 7.6)

Best config: D_hybrid / GROUP edges / round 1 / any alpha / argmax ->
weak macro **0.3716**, macro **0.3936**, MOVE recall **0.109**, MOVE F1 **0.158**,
UNCHANGED drop 0.011, deterministic across alphas/rounds (propagation is a pass-through
of the improved seed distribution).

### Verdict

- Seed recovery: **PARTIAL SUCCESS** - 24x base MOVE recall at usable precision, best macro so far.
- Propagation amplification: **NO-GO again** - the graph adds ~nothing on top of good seeds;
  predicted-probability neighbourhoods carry no exploitable structure beyond per-node knowledge.
- Promotion gates: FAILED (weak delta +0.015 < +0.10; MOVE recall 0.109 < 0.25; MOVE F1 0.158 < 0.20).

### Consequence

The oracle gap decomposes into: (a) seed quality - partially recovered; (b) information that
exists ONLY in true neighbour state - unreachable without end-to-end learned message passing.
With two consecutive strict NO-GOs, the relational track is frozen: invest in more validated
pairs + manual review loop to raise base predictor quality. Revisit a small GNN only if base
weak-class recall improves materially (target: MOVE recall >= 0.30 from the node model alone).
