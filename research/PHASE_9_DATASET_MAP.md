# Phase 9 Dataset Map (Subagent 2 — READ-ONLY cartography)

Primary sources: `data/processed/propagation_cache.jsonl`, `data/pairs/validated_pairs.jsonl`, `data/pairs/transformation_records.jsonl`, `data/metadata/FINGERPRINT_INDEX.json`, `data/metadata/DATASET_INTEGRITY.json`, `data/metadata/MOVE_FORENSICS.json` (external citation only).

## 1. Counts

| Metric | Value |
|---|---|
| Total cache rows | 7350 |
| Distinct slide_keys | 301 |
| Distinct family groups | 39 |
| Rows/slide min–med–p90–max | 1 / 19.0 / 46.0 / 137 |
| Slides/family min–med–p90–max | 1 / 2.0 / 24.2 / 53 |

Slides-per-family histogram: `1`: 19, `11+`: 10, `2`: 5, `3-5`: 2, `6-10`: 3

## 2. Labels

**No `split` field in cache rows** → Phase 9 must re-derive CV folds from scratch.

| Class | Rows |
|---|---|
| MOVE | 441 |
| RECOLOR | 22 |
| REMOVE | 675 |
| RESIZE | 922 |
| RESTYLE | 39 |
| UNCHANGED | 5251 |

## 3. MOVE-specific map

| Metric | Value |
|---|---|
| MOVE rows | 441 (6.00% of rows) |
| Slides with 0 MOVE | 225 |
| Slides with 1 MOVE | 24 |
| Slides with 2+ MOVE | 52 |

MOVE nodes by container_depth bucket: `0`: 432, `1`: 8, `2-3`: 1

MOVE text vs non-text (`base.is_text`): text=227, non-text=214 (51.5% text).

> **Displacement magnitude buckets are NOT derivable** from the propagation cache (no geometry deltas stored). External citation — `data/metadata/MOVE_FORENSICS.json`: true_move_nodes=441, detected=48, missed=393; disp detected_median=0.05181 vs missed_median=0.03678 (AUC 0.4871).

## 4. Family/group boundaries

| Metric | Value |
|---|---|
| Families | 39 |
| Largest / smallest family (slides) | 53 / 1 |
| Variant-twin slide_keys (same key under 2+ groups) | 0 |
| Duplicate sample_ids | 0 |

DATASET_INTEGRITY claims `node.groups_spanning_splits=0`; cache carries no split column so this was NOT re-verifiable here — the slide-level twin scan found no cross-family slide_keys.

## 5. Template-family clusters (FINGERPRINT_INDEX)

| Metric | Value |
|---|---|
| Exact-hash clusters (all, incl. singletons) | 148 |
| Shared clusters (>=2 decks) | 41 (matches DATASET_INTEGRITY claim=41) |
| Decks in shared clusters / indexed decks | 154 / 261 (integrity claims 154) |
| Singleton clusters | 107 |
| Decks unmapped to any family | 133 |
| Shared clusters spanning MULTIPLE family groups | **8** |
| Max families inside one cluster | 3 |

## 6. Pair coverage

| Metric | Value |
|---|---|
| Validated pairs | 43 |
| Pairs contributing ≥1 cache row | 43 |
| Orphan pairs (0 cache rows) | 0 |
| Slide mappings total | 301 |
| Distinct raw slides mapped | 301 |
| Cache slides matched by mappings | 301 / 301 |
| Slides_evaluated (sum of matched alignments) | 301 |

## 7. Integrity cross-check vs DATASET_INTEGRITY.json

**No unexplained mismatches.** All comparable numbers reconcile.

Explainable deltas (structural, not corruption):

- node.n_samples: integrity=7888 cache=7350 (delta=538) — EXPLAINABLE: cache is the raw-side node substrate; ADD-class rows exist only on the branded side and are absent by construction.
- label ADD=538 present in integrity but absent in cache — EXPLAINABLE (branded-side-only rows; all other classes match exactly).

## 8. Recommendations for Phase 9 folding

| Item | Recommendation |
|---|---|
| Rarest class | `RECOLOR`, support 22 (5 family groups, 10 slides) |
| Max safe StratifiedGroupKFold k | **5** (recommended k=5) |
| Dedup pre-pass | YES — see note below |

- StratifiedGroupKFold needs every fold testable for the rarest class (RECOLOR, support=22); it appears in 5 family groups, so k must be <= 5. Family sizes range 1-53 slides, so grouped folds are well-formed up to that bound.
- No dedup-by-slide needed: 0 variant-twin slide keys, 0 duplicate sample ids. Dedup-by-template-hash pre-pass RECOMMENDED: 41 exact-hash clusters (>=2 decks) cover 154 of 261 indexed decks (107 singleton clusters) and 8 shared clusters span multiple family groups -> near-duplicate leakage risk across grouped folds.
