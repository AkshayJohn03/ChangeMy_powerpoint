# Phase 9 — Slide-Context Experiment Contract (DRAFT)

Author: Subagent 5 (Experimental Reviewer / contract author). Status: DRAFT for
primary-agent approval before any Phase 9 implementation. Inputs reconciled:
`research/PHASE_9_DATASET_MAP.md/.json`, `research/PHASE_9_LEAKAGE_THREAT_MODEL.md`,
`research/PHASE_9_CONTEXT_FEATURE_SCHEMA.md`. Compliance: AGENTS.md data policy —
this document and all chat output carry aggregate counts only, never deck names,
paths, or contents.

Population scope (T6 note): all results describe rows from slides inside validated
pairs only (7,350 cache rows / 301 slide_keys / 39 family groups). Deployment
population is broader; every report must repeat this caveat.

---

## 0. RESOLUTIONS BY PRIMARY AGENT (ratified — this file is now the frozen contract)

- **Q1**: Variant C is RESTRICTED to slide-BROADCAST features (G1/G3 members only,
  not just the MUST-HAVE subset). Per-node G2/G4 terms move to variant D, which
  now carries V2 + G2 + G4 (full relative/contextual set, 12+10 features).
  This restores the intended scenario mapping: C tests global slide-intent
  broadcast; D isolates relative-meaning. Optional appendix arm `E_full`
  (V2 + all 42) may be run once if C or D shows discovery signal.
- **Q2**: Confirmed. All headline pooled metrics use POST-dedupe rows only;
  excluded-family counts are documented separately in the results JSON.
- **Q3**: Raw L1 canvas-unit magnitude is the primary weight; unweighted recall
  reported side-by-side. Percentile weighting deferred (appendix only).
- **Q4**: `choose_folds` k-reduction is the default; when k drops below 5,
  macro-over-present-classes is reported as a secondary diagnostic column.
- **Q5**: Context-vs-dummy sanity guard tolerance confirmed at weak_macro_f1
  delta <= 0.01.

---

## 1. OBJECTIVE & HYPOTHESES

**Primary — slide-intent hypothesis.** Slide-level layout descriptors that the
falsified aggregate set could not express (alignment-rail structure, occupancy
shape: schema groups G1 + G3) improve node-level edit-intent classification,
especially MOVE, beyond the existing per-node V2 base vector.

**Secondary — relative-meaning hypothesis.** Node-vs-slide relational terms
(schema group G2) carry MOVE-disambiguation signal that pure slide-level vectors
cannot provide, because slide-level values broadcast identically to every node and
can only say "what kind of slide," never "where this node sits within it."

Mapping to conditions:
- B_slide_ctx alone tests the slide-intent hypothesis (vs A).
- D_relational alone tests the relative-meaning hypothesis (vs A).
- C_node_plus_ctx tests joint/interaction value of both families.
- A_node_only is the control. Discovery gates are evaluated per variant against A.

## 2. FEATURE VARIANTS

Variant definitions reference `PHASE_9_CONTEXT_FEATURE_SCHEMA.md` groups; formulas
are NOT re-listed here. Schema group references are normative.

| Variant | Definition | Purpose |
|---|---|---|
| A_node_only | Existing V2 base feature dict as produced by `propagation_cache.jsonl` rows (`base` + V2 per-node features), 52 columns | Control |
| B_slide_ctx_only | MUST-HAVE tier of G1/G3 ONLY (slide-broadcast subset): n_xbands_log1p, n_ybands_log1p, grid_regularity_score, quad_occupied_count, occ_col_frac_1 — schema MUST-HAVE items restricted to G1/G3 groups (11-item tier minus G2/G4 members) | Pure slide-intent signal |
| C_node_plus_slide_broadcast | A + ALL G1/G3 slide-broadcast features (full group members, not only MUST-HAVE) | Node + global slide context |
| D_node_plus_relative_contextual | A + G2 relative terms (12) + G4 per-node structural terms (10) | Isolated relative-meaning |
| E_full (appendix, run once if C or D shows discovery signal) | A + all 42 proposed features across G1–G4 | Kitchen-sink reference |

MUST-HAVE tier reconciliation: the schema heading says "10" but lists 11 items with
an explicit drop-first note (contain_depth_d0_frac). This contract uses ALL 11 for
variant construction (B takes its G1/G3 members; C/D take their group members);
if a strict-10 constraint is later imposed, drop contain_depth_d0_frac first.

Reference baselines (context-only comparisons, not gate competitors):
- DUMMY: DummyClassifier(strategy="most_frequent") under identical folds.
- ANCHOR historical numbers cited from `data/metadata/RELATIONAL_BENCHMARK.json`
  ANCHOR_CONTEXT random_forest: weak_macro_f1 = 0.3568; and Phase 7.5 best
  (`data/metadata/PROPAGATION_RESULTS_P75.json`): weak_macro_f1 = 0.3716,
  move_recall = 0.1088. These anchor populations differ from the Phase 9 row set;
  they contextualize results and feed only the promotion gate's weak_delta term.

## 3. FOLDING PROTOCOL

Rebuild NOT required: reuse `data/processed/propagation_cache.jsonl` as-is.

Pre-fold steps (mandatory, in order):
1. Duplicate sample_id check: assert 0 duplicates (dataset map found 0); if any
   appear, drop repeats and log counts removed.
2. Template-hash dedupe pre-pass: load `data/metadata/FINGERPRINT_INDEX.json`.
   For every exact-hash cluster spanning >1 family group (map found 8 such
   clusters), keep ONE family's instances — the family with the lowest family
   token — and EXCLUDE the other families' instances from evaluation sets
   entirely. Document per-cluster and total counts removed in the report. This
   resolves the T5 guard ("keep one representative OR force same group") in favor
   of family-level exclusion, which preserves grouped-CV semantics while removing
   cross-family exact-hash collisions.

Fold derivation:
- StratifiedGroupKFold(k=5, shuffle=True, random_state=0), groups = family derived
  through ONE shared helper `family_of(pair_row)` (`name_key` fallback `raw_deck`),
  shared by every Phase 9 row builder (guard 6).
- k bound rationale: RECOLOR (support=22) appears in exactly 5 family groups →
  k ≤ 5; use k=5, reduced via existing `choose_folds(y, groups)` if a class has
  support < 2 in any fold.

Post-checks (assert, else halt):
- Zero families shared between train and test in EVERY fold. Do NOT assert "every
  family in exactly one fold" — grouped CV assigns folds per family at each split.
- Class support ≥ 2 per fold per class, or fold count reduced via choose_folds.
- Every fingerprint-exact deck cluster lies within a single post-dedupe group.
- Report per-fold max train/test slide-context similarity AND cross-fold template
  overlap next to results (T5 detection test).

## 4. MODELS

Fixed model zoo, defined LOCALLY in `slide_context_bench.py` (do NOT import the
shared `bench_classifiers.model_zoo`, whose params drift from this contract):

| Model | Constructor |
|---|---|
| dummy_most_frequent | DummyClassifier(strategy="most_frequent") |
| decision_tree | DecisionTreeClassifier(max_depth=8, class_weight="balanced", random_state=0) |
| random_forest | RandomForestClassifier(n_estimators=300, min_samples_leaf=2, class_weight="balanced_subsample", random_state=0, n_jobs=-1) |
| hist_gbdt | HistGradientBoostingClassifier(max_depth=4, max_iter=250, learning_rate=0.1, random_state=0) |

All seeds fixed at 0. Determinism check MANDATED: run the full benchmark twice;
all pooled metrics must be byte-equal between runs, else halt (Section 9).

Note (conflict resolved): this zoo intentionally deviates from
`bench_classifiers.model_zoo` v2 defaults (RF n_estimators 200 vs 300 here; DT
min_samples_leaf 5 unspecified there) — contract params win.

## 5. METRICS

Pooled across folds (out-of-fold predictions concatenated):
- macro_f1 (all 6 classes)
- weak_class_macro_f1: mean pooled per-class F1 over RESTYLE, RESIZE, REMOVE, MOVE
- Per-class precision/recall/F1 for all classes, reporting MOVE P/R/F1 and
  UNCHANGED recall explicitly
- unsafe_rate: (wrong MOVE + wrong REMOVE predictions) / n

NEW utility metric — displacement-weighted MOVE recall:
- Join cache `sample_id` → `data/pairs/transformation_records.jsonl` on
  `raw_node_id` (verified identical key format); weight each true-MOVE row by its
  L1 displacement magnitude from `geometry.{x,y}.delta`; weighted recall =
  sum(weights of correctly predicted MOVE) / sum(all true-MOVE weights). Report
  raw-L1 weighting plus unweighted recall beside it.
- FORENSIC-ONLY: this join is permitted exclusively inside evaluation/reporting
  code. Features must NEVER touch transformation records (guard 1).

Report headline metrics TWICE: all rows and content-deduplicated rows (guard 8).

## 6. DECISION GATES (two tiers)

Tier 1 — DISCOVERY_SIGNAL (research continue):
- move_recall_delta >= +0.05 OR move_f1_delta >= +0.05, where deltas are
  BEST(A,B,C,D) minus independent baseline A_node_only RF;
- AND unchanged_recall_drop <= 0.03 vs A;
- AND unsafe_rate <= A's unsafe_rate.

Tier 2 — PROMOTION (production):
- move_recall >= 0.25 AND move_f1 >= 0.20;
- AND weak_class_macro_f1 delta vs ANCHOR_CONTEXT weak_macro (0.3568) >= +0.10;
- AND unchanged_recall_drop <= 0.03 and unsafe_rate <= A (same constraints).

Failure handling:
- No discovery signal → FREEZE the slide-context hypothesis; recommend Pool A/B
  data collection targeting MOVE-dense slides (225 of 301 slides currently have
  zero MOVE rows) and template-diverse decks; do not proceed to production work.
- Signal present but below promotion → route to Phase 10 refinement path
  (feature pruning within winning variant, threshold tuning on MOVE scores,
  displacement-weighted error analysis).

## 7. LEAKAGE GUARDS

### IMPLEMENTER GUARDS (from PHASE_9_LEAKAGE_THREAT_MODEL.md, verbatim)

1. Compute slide aggregates ONLY from cache `"base"` blocks (or raw ast_v2 slide
   JSON) of nodes whose ids resolve to the SAME `slide_key`; never from
   transformation records, alignments, chrome diffs, or any `after`/`delta` field.
2. Member list for aggregation MUST be `flatten_nodes(raw_slide.nodes)`; assert
   `len(members) == len(cache_rows_for_slide)` before aggregating.
3. ASSERT no feature/column name produced by Phase 9 matches
   `(after|delta|branded|target|truth|tag|label|record)` case-insensitively; wire
   this into the existing static-scan test.
4. UNIT TEST: shuffle labels across rows -> all slide context vectors unchanged
   (byte-equal). Second unit test: predict labels from context block alone under
   grouped CV; must not beat the majority-class dummy beyond a documented epsilon.
5. NEVER encode `sample_id`, `slide_key`, `deck_id`, pair names, or slide indices
   into X (no hashing/ordinal/embedding of identifiers); reject any candidate
   feature whose distinct-value count exceeds half the number of slides.
6. Derive CV groups through ONE shared helper (`family_of(pair_row)`); assert every
   `name_key` maps to exactly one group string and log groups formed purely by the
   deck-id fallback.
7. Before splitting, resolve cross-family exact-hash collisions from
   `FINGERPRINT_INDEX.json`: either deduplicate or force colliding decks into one
   group; publish per-fold max train/test slide-context similarity beside results.
8. Report headline metrics TWICE: all rows and content-deduplicated rows; assert
   every fingerprint-exact deck cluster lies within a single group.
9. Neighbor/local features must aggregate over the FULL raw-slide graph adjacency
   (`build_slide_graph` output), never over truth-bearing or matched-only subsets;
   assert neighbor index sets equal graph edge sets per row.
10. Fit and persist normalization statistics on train folds only; inference loads
    them (no refit); document the survivorship population ("valid-pair slides")
    in the report header.
11. Keep oracle/anchor blocks in their own dict keys and route columns strictly by
    block (preserve `make_X` sentinel-expansion behavior); extend
    `test_relational_guard.py` to cover the Phase 9 context block.
12. Synthetic smoke fixtures (0-node, 1-node, off-canvas, duplicate-position slides)
    must run the full context pipeline without exception and with finite floats
    (guard divisions: density, fractions, spans already use epsilons — keep it so).

### Contract additions

13. "Labels shuffled -> identical context matrix" unit test implemented and wired
    into CI-equivalent test module (materializes guard 4 clause 1 as a named,
    runnable assertion over the full 42-feature context matrix).
14. "Context-only model must not beat dummy" sanity check: train every zoo model
    on B_slide_ctx ALONE under the Section 3 folds; if any model's weak_class_macro_f1
    exceeds the dummy by more than a documented epsilon, halt (T3 breach).
15. Banned-token static scan extension over new module source
    (`morphlite/training/slide_context.py`, `slide_context_bench.py`, and any
    Phase 9 test modules): forbid identifiers
    `after|branded|delta|match_confidence` (extending the existing scan pattern),
    in addition to the column-name regex of guard 3. The forensic-only join of
    Section 5 lives in the benchmark's REPORTING layer and must be isolated behind
    its own function so the scan can whitelist it explicitly.

## 8. RUN COMMANDS & ARTIFACT PATHS

```
python -m morphlite.training.slide_context        # extraction (variants B/C/D matrices + guards)
python -m morphlite.training.slide_context_bench  # folding, models, gates, artifacts
```

Outputs:
- `data/metadata/PHASE_9_CONTEXT_RESULTS.json` — pooled metrics, per-fold template
  overlap, dedupe removal counts, gate evaluations, determinism-check result.
- `research/PHASE_9_EXPERIMENT_REPORT.md` — narrative report incl. survivorship
  caveat (Section header note), population-shift table (T6), both all-rows and
  content-deduplicated headline tables.

## 9. FAILURE CONDITIONS / STOP RULES

Halt BEFORE benchmarking if any of:
- Any Section 7 guard test fails (incl. banned-token scan, shuffle test,
  context-vs-dummy sanity, member-list assertion, cardinality audit).
- Folding post-checks fail (family leakage across folds, class support < 2 without
  choose_folds reduction, exact-hash cluster spanning groups post-dedupe).

Halt AT ANY POINT if:
- Determinism rerun produces non-identical metrics.
- The template-overlap report is missing from results artifacts.

Any halt writes a failure record into `PHASE_9_CONTEXT_RESULTS.json` and stops;
no partial conclusions may be published.

## 10. OPEN QUESTIONS FOR PRIMARY AGENT (max 5)

1. Q1 Variant C includes G4 per-node terms (align_degree, nn_same_type_ratio) even
   though they are node-level rather than broadcast — confirm C should carry the
   full 42-feature set as specified, or exclude per-node G4 terms to keep C purely
   "V2 + slide-broadcast context"?
2. Q2 Confirm pooled-metric denominators after the template-hash pre-pass are
   POST-DEDUPE rows only (excluded families' rows dropped from all folds), with no
   separate all-rows-including-excluded table required beyond documenting counts.
3. Q3 Displacement-weighted recall weighting: raw L1 canvas-unit magnitude as
   specified — or percentile-bucket weights to limit outlier dominance? Default:
   raw L1 + unweighted reported side by side.
4. Q4 If RECOLOR support < 2 in some fold at k=5, prefer choose_folds k-reduction
   (default) or macro-over-present-classes-only at k=5?
5. Q5 Epsilon values for guards 4 and 14 (shuffle-test byte equality needs none;
   context-vs-dummy tolerance proposed: weak_class_macro_f1 delta <= 0.01) —
   confirm 0.01 or specify stricter.
