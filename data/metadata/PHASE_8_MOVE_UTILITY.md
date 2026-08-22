# Phase 8 - MOVE Utility Boundary & Ambiguity Report

Questions: are missed MOVEs meaningful failures? Is the label boundary noisy? Is there irreducible ambiguity in deployable input space?

## 1. Magnitude stratification (D_hybrid OOF predictions, n=441 true MOVEs)

| Bucket | disp range | Events | Event recall | Displacement mass share |
|---|---|---:|---:|---:|
| MICRO | <0.01 | **0** | - | 0% |
| SMALL | 0.01-0.03 | 112 | 0.179 | 12% |
| MEDIUM | 0.03-0.08 | 290 | 0.086 | **62%** |
| LARGE | >0.08 | 39 | 0.077 | 26% |

- The MICRO bucket is EMPTY: sub-0.01 normalized moves do not exist in this corpus.
- Misses are dominated by **MEDIUM structural repositioning** (66% of events, 62% of movement mass).
- Recall is uniformly poor across all non-empty buckets (0.077-0.179).

## 2. Utility-weighted metrics

| Metric | Value |
|---|---:|
| Event recall | 0.104 |
| Weighted displacement recall | 0.105 |
| Movement energy missed | **89.5%** |

The micro-nudge hypothesis is **FALSIFIED**: weighting by visual impact does not soften the failure. The model misses large-and-meaningful repositioning at the same rate as small nudges. The MOVE objective is NOT mislabelled noise.

## 3. Counterfactual ambiguity test (Phase 8.5)

k=10 nearest neighbours in deployable feature space (cross-slide only):

| Scope | Mean neighbour entropy (bits) | Mean neighbour MOVE fraction |
|---|---:|---:|
| Global H(Y) baseline | 1.347 | 0.060 (class prior) |
| All true-MOVE nodes | 0.994 | 0.175 |
| SMALL bucket | 0.961 | 0.139 |
| MEDIUM bucket | 1.018 | 0.199 |
| LARGE bucket | 0.907 | 0.105 |

Entropy remains high (≈1.0 bits) and nearly uniform across every magnitude scale.
Similar deployable inputs map to substantially different designer outcomes even at
LARGE displacements.

Combined with Phase 6 (oracle neighbour state within-slide IS predictive), the
ambiguity localizes precisely:

> Transformation intent is coherent WITHIN a slide but diverges ACROSS slides for
> similar raw patterns. Per-node classification from raw features cannot express
> slide-level intent.

## 4. Verdict against the decision tree

- Label-boundary noise? **NO - falsified** (no micro bucket; medium moves dominate misses).
- Utility illusion? **NO** - weighted recall equals event recall.
- Irreducible cross-slide ambiguity? **YES - demonstrated empirically** (H(Y|kNN) ~1.0 bit everywhere).

## 5. Consequences

1. MOVE F1 remains blocked as a promotion metric; current labels are semantically valid.
2. The one unfalsified hypothesis is Direction A: slide-level latent transformation
   intent ("layout compaction", template-level reflow) driving per-node moves.
   Testing it requires a NEW problem formulation - slide-pair latent state modelling -
   which is explicitly out of scope until more validated pairs exist.
3. Targeted collection priorities (Phase 9 preview): Pool A = similar-source/
   divergent-outcome slide pairs to bound the ambiguity; Pool B = recurring
   learnable patterns (icon/title, hero image, CTA groups).
4. Neural MorphNet / GNN: remains BLOCKED. No representation currently in evidence
   recovers the signal, and the ambiguity result shows why: the information is not
   node-local in deployable space.
