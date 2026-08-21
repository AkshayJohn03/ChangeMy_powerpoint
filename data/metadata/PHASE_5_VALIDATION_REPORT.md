# MorphLite Phase 5 Validation Report

Scope: representation-quality experiment (AST V1 -> V2) and architecture justification.
Protocol: StratifiedGroupKFold grouped by deck **family** (leakage-safe), adaptive fold
count, repeated where supported (intent x3). Selection metric = grouped-CV macro F1.
Effective sample size is treated as the number of deck/template families (~40-50),
**not** the 7,888 node rows.

## 1. AST V2 quality (`AST_V2_AUDIT.json`)

- 261 decks / 2,323 slides enriched; text nodes fully covered by the resolver.
- Effective-property resolution ~100% for family & size (chain:
  run -> paragraph -> shape lstStyle -> layout ph -> master ph -> master txStyles -> theme).
- Origin mix shows real inheritance usage: thousands of theme-resolved families,
  master/layout-placeholder sizes, not just explicit runs.
- Suspicious defaults tracked separately (18pt theme/otherStyle signatures).
- Unmatched shape joins: 209 nodes (<0.5%).

## 2. Dataset integrity (`DATASET_INTEGRITY.json`)

- v2: intent 74 samples (43 golden + 31 variant twins); node 7,888.
- Groups spanning splits: **0**; duplicate sample ids: **0**.
- Label skew: REBUILD 57 / PRESERVE 12 / MIXED 5 (intent).
- Template-family clusters (fingerprint exact-hash): 41 clusters / 154 decks -
  confirms heavy template sharing; treated as context, not identity.
- Hash-split degeneracy detected for intent (one class confined to test);
  mitigated by relying on repeated grouped CV only.

## 3. Node transformation: V1 vs V2 (RandomForest, pooled grouped CV)

| Class | V1 F1 | V2 F1 | delta |
|---|---|---|---|
| UNCHANGED | 0.849 | 0.857 | +0.008 |
| ADD | 0.750 | 0.791 | +0.041 |
| REMOVE | 0.635 | 0.601 | -0.034 |
| RESIZE | 0.556 | 0.544 | -0.012 |
| RESTYLE | 0.186 | 0.186 | 0.000 |
| MOVE | 0.008 | 0.073 | +0.065 |
| **macro CV** | **0.477** | **0.485** | **+0.008** |

## 4. Intent feature ablation (`INTENT_ABLATION.json`, repeated grouped CV)

| Set | best model | cv macro F1 |
|---|---|---|
| A v1 full (contains name-derived keys) | RF/HGB | 0.609 |
| B v1 minus names | RF | 0.576 |
| C fingerprints only | HGB | 0.222 |
| D structural stats only | RF | 0.330 |
| E v2 all (name-free) | HGB | 0.211 |

Dummy baseline reaches 0.32-0.58 depending on folds - i.e. class-skew noise.
No leakage-safe set separates classes.

## 5. Model promotion decisions

All four candidates **NOT PROMOTED**:
- intent v1: name-leakage features + minority recall < gate
- intent v2: does not beat dummy
- node v1/v2: minority-class recall below threshold (v1 also over latency budget)
Deterministic fallback remains the production path. No model files overwritten.

## 6. Answers to the mandated questions

1. **Did effective typography improve classification?**
   Only marginally at macro level (+0.008). RESTYLE stayed exactly flat (0.186)
   and RESIZE did not improve (-0.012): the bottleneck is *not* missing inherited
   fonts but the absence of relational/contextual signal that decides *which*
   nodes change.
2. **Did invariant fingerprints improve intent generalization?**
   No - nothing does at N=74. Name-free sets sit at/below dummy; the apparent V1
   lift is layout-name memorization. Intent prediction needs many more labeled
   pairs or an explicit user signal; it must not be auto-applied.
3. **Which classes remain impossible with independent node features?**
   MOVE (0.07) and ADD-by-classification are structurally out of reach for
   per-node vectors; REMOVE/RESIZE partially depend on neighbor fate as well.
4. **Is a graph/message-passing model empirically justified?**
   Yes, narrowly and specifically: relational features alone moved MOVE off zero
   (+0.065) with trivial effort, and RESTYLE's ceiling is a context problem.
   Justified next step: small message-passing over slide graphs for
   {RESTYLE, RESIZE, REMOVE, MOVE} - not a general "MorphNet".
5. **What should MorphNet contain (evidence-based)?**
   - Deck-intent head: **dropped until >=200 validated pairs** or user-in-loop signal.
   - Node head: GNN/light GBM over graph features (neighbor typography deltas,
     alignment bands, group fate) targeting the four weak classes.
   - ADD handled as separate set-prediction head, postponed.
   - Chrome/layout policy stays deterministic preserve-first (0.864 accuracy).

## 7. Inference architecture shipped (Phase E)

`morphlite/inference/`: promotion-gated `model_loader`, rule/ML fusion in
`confidence.py` (rule>=0.90 wins; agreement window 0.60-0.90; ml-solo>=0.85;
else preserve), `safety_gate.py` vetoing MOVE/ADD ops and stale before-values,
and pure `hybrid_planner.build_hybrid_plan()` emitting per-op provenance
(`source: rule|ml|agreement|fallback_preserve`). With no models promoted, the
planner deterministically reduces to the rules engine + preserve-first vetting.

## 8. Explicit blockers

- REBUILD/PRESERVE auto-detection: blocked on data volume (>=200 pairs target).
- MOVE application: blocked until a predictor beats min-recall gate.
- ADD application: blocked (set-prediction design required).
- Studio UI integration: deferred until hybrid plan is validated end-to-end
  (Phase 8 evaluation harness against golden branded decks).
