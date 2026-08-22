# Phase 9 — Leakage / Correctness Threat Model (pre-implementation)

Author: Subagent 3 (read-only leakage adversary). Written BEFORE any Phase 9
code exists. Scope: planned slide-level CONTEXT vectors attached to every node,
computed from the RAW/source slide only, benchmarked under deck-family-grouped
CV against existing baselines.

Prior art inspected (read-only):
- `morphlite/training/context_ablation.py` — `slide_context(members_base)` computes
  ~26 slide aggregates (n_log1p, text_frac, cx/cy moments, x/y_span, occupied_area,
  density, align conc, overlap/area/eff_size/bold/text-length fracs) from row
  `"base"` blocks; `build_spaces()` keys them by `slide_key = nid.rsplit("__n",1)[0]`.
- `morphlite/training/relational_benchmark.py` — `build_rows()` assembles rows per
  validated pair; group = `v["name_key"] or v["raw_deck"]`; oracle/anchor blocks kept
  in separate dict blocks (guard-tested in `tests/test_relational_guard.py`).
- `morphlite/training/propagation.py` — `_build_cache()` walks `validated_pairs.jsonl`,
  extracts V2 feats from the raw deck's slides only; all nodes of a mapped slide get a
  row (missing truth => "UNCHANGED"); nbrs index into the SAME flat row list.
- `morphlite/training/dataset_builder.py` — `truth_node_labels()` reads
  `transformation_records.jsonl`; `label_from_tags` priority REMOVE > RESIZE > MOVE >
  RECOLOR > RESTYLE > UNCHANGED. `dataset_builder_v2.py` adds ADD rows with
  `side: "branded"` features extracted from the BRANDED deck.
- `morphlite/training/ast_diff.py::build_record` — transformation records carry
  `geometry.{x,y,w,h}.{before,after,delta}`, `typography.*.{before,after}`,
  `style.fill_color.before/after`, `content.chars_after/similarity`. **"after" values
  originate from the BRANDED deck.**
- `morphlite/features/node_features_v2.py` — `eff_size_pt` etc. derived from AST v2,
  which was extracted from physically separate RAW copies (extract_asts/build_ast_v2
  ran on raw-side files only). No branded field enters `"base"` dicts today.
- `morphlite/training/fingerprint_stats.py` — writes `FINGERPRINT_INDEX.json`
  (`exact_hash`, `canonical` per deck); report contains exact-duplicate clusters and
  near-dup pairs >= 0.95 similarity — i.e., cross-deck near-identical content EXISTS
  in this corpus.

Severity scale: CRITICAL = invalidates benchmark conclusion; HIGH = materially
inflates metrics or silently changes population; MED = conditional inflation;
LOW = hygiene/documentation.

---

## T1. Target-derived aggregates (branded-side values inside slide context)

**Mechanism.** Any slide statistic computed from anything other than the raw slide's
own geometry/typography pulls in target information. Concrete traps in this codebase:
(a) averaging `geometry.after` / `geometry.delta` from transformation records;
(b) joining slide members via record lists instead of the raw slide's node list;
(c) reusing `evaluate_baseline.py`-style truth structures (`entry["after"]`) as a
feature source; (d) copying chrome_diff outputs (`before->after` swap tables) into
context. Because slide context is broadcast to every node, ONE contaminated scalar
poisons an entire space (B/D) while space A stays clean — the ablation delta itself
becomes the leak signal.
**Severity:** CRITICAL.
**Detection test.** Recompute every slide-context vector twice: once from the
pipeline, once independently from `data/extracted/ast_v2/<raw>.json` slides; assert
bitwise-equal vectors. Static scan: forbid identifiers `after|delta|branded|target`
inside the context-builder module (extend the existing scan pattern of
`test_relational_guard.py`).
**Guard rule.** Slide aggregates may read ONLY the `"base"` feature blocks (or the
raw ast_v2 slide JSON) of nodes whose ids belong to the SAME `slide_key`. Never open
`transformation_records.jsonl`, `validated_pairs.jsonl` branded fields, or any
chrome_diff output inside the context builder.

## T2. Correspondence artifacts (record presence shapes the context)

**Mechanism.** Transformation records exist only where alignment MATCHED. If slide
members, counts, means, or spans are computed over the *matched subset* (e.g.,
members = record keys, or neighbors drawn from matched ids), then n_log1p, density,
spans, fracs all shift with match success — and match success correlates with how
heavily a slide was edited (i.e., with its label distribution). The model reads
"how matchable this slide was" as a proxy for "how much was changed here."
Today `propagation._build_cache` avoids this (all flattened slide nodes become rows),
but nothing enforces it for Phase 9.
**Severity:** HIGH.
**Detection test.** Build slide context twice: over ALL slide nodes vs over only
nodes possessing truth records; assert identical vectors. Additionally regress
`n_log1p` against per-slide mean label-change indicator: a strong association after
restriction-to-matched would confirm contamination.
**Guard rule.** Membership for slide aggregation = full
`extractor.flatten_nodes(slide["nodes"])` list of the raw slide; assert
`len(members) == len(rows_for_slide)` and that no truth-record lookup participates
in member selection, ordering, or filtering.

## T3. Label-derived aggregates (incl. transitive via neighbor lists)

**Mechanism.** Tempting "helpful" context features are secretly label functions:
move-fraction / restyle-fraction of the slide, "slide has any REMOVE," entropy of
slide tag distribution, or neighbor aggregates (`nbr_*`) computed over the labeled
subset rather than the full node set (nodes lacking records default UNCHANGED, so a
"neighbor move fraction" over truth-bearing neighbors encodes label presence AND
value). Even one such column makes space D an oracle in disguise; the Phase 8.6/8.7
verdict machinery would promote a leak.
**Severity:** CRITICAL.
**Detection test.** (a) Unit test: shuffle/permute labels across rows -> every slide
context vector byte-identical. (b) Train a shallow classifier to predict the LABEL
from the context block ALONE under grouped CV; AUC/macro-F1 must not beat the
class-prior dummy beyond noise (context may legitimately correlate weakly with
layout type; set a documented tolerance and investigate any breach).
**Guard rule.** Context builder imports no label/truth/tag symbol and receives no
argument containing labels. Neighbor-based features (if any) must aggregate raw
attributes over the FULL node set from the raw slide graph, never a truth-filtered
subset; assert neighbor sets == graph adjacency sets from `build_slide_graph`.

## T4. Pair/deck identity encoding through high-cardinality proxies

**Mechanism.** Exact counts and unusual constants act as fingerprints: `n_log1p`,
`density`, `align_x_conc` combos can uniquely identify a slide; worse, any accidental
encoding of `sample_id`/`slide_key`/`deck` strings (hashing ids into features,
ordinal-encoding slide order, embedding deck token) gives direct memorization of
family-specific outcomes. Grouping interaction: `StratifiedGroupKFold(groups=family)`
DOES prevent a family's slides from being co-train/co-test — verified grouping key is
`v["name_key"] or v["raw_deck"]` — BUT (a) when `name_key` is None the fallback makes
each DECK its own group, so two decks of the same logical family can land in
opposite folds; (b) variant-twin resolutions reuse `name_key` inconsistently across
builders. Residual risk: near-duplicate DECKS across different families remain legal
under grouping (see T5).
**Severity:** HIGH.
**Detection test.** Feature-cardinality audit: any context column whose number of
distinct values approaches the number of distinct slides/groups is suspect — flag
and justify. Group-integrity test: assert every row sharing a `name_key` shares one
group value; count groups whose members span >1 raw deck and review whether that is
intended family semantics.
**Guard rule.** No identifier string may be vectorized, hashed, or ordinal-encoded
into X. Cap context cardinality: reject any proposed feature whose distinct-value
count > 0.5 * n_slides unless explicitly allow-listed. Normalize group derivation
through ONE shared helper used by every Phase 9 row builder.

## T5. Fold contamination via shared templates (slide-context memorization)

**Mechanism.** The context vector is IDENTICAL for all nodes of a slide. If family F1
(train) and family F2 (test) contain near-identical template slides — and
`fingerprint_stats.py` proves exact-hash clusters and >=0.95 near-dups exist — the
model memorizes "slides shaped like this tend toward these labels" from F1 and wins
on F2 without learning node-level structure. Space A cannot exploit this; spaces
B/D can, so the ablation delta partially measures template overlap, not context
value. Exact duplicates WITHIN one family are harmless for CV but inflate pooled
counts; ACROSS families they inflate deltas.
**Severity:** HIGH.
**Detection test.** For each fold, compute max cross-family slide-context cosine
similarity between train and test slides (and cross-family exact-hash hits from
`FINGERPRINT_INDEX.json`); report per fold. Sensitivity run: drop test slides whose
train-side nearest-context similarity >= threshold (e.g., 0.98) and re-score; a large
delta-vs-A collapse indicates template memorization.
**Guard rule.** Publish the per-fold train/test template-overlap number next to every
Phase 9 result. Deduplicate exact `exact_hash` collisions across families before
splitting (keep one representative per cluster, or force colliding decks into the
same group), and state the rule in the report.

## T6. Survivorship / population mismatch

**Mechanism.** Rows exist only for slides inside VALIDATED pairs' `slide_mappings`.
Unmapped slides, skipped pairs (deck missing manifest — `n_skipped` path), and
alignment-rejected content are absent. Slide statistics over this survivor subset
(e.g., density, occupied_area distributions) describe curated, well-formed slides;
deployment inference sees arbitrary slides (cluttered, degenerate, huge). Metrics
transfer is unknown and normalization constants (means/stds fit on survivors) drift.
**Severity:** MED.
**Detection test.** Compare slide-context distributions (per-feature quantiles) for
mapped-slides vs all ast_v2 slides; report population-shift table in the Phase 9
report. Smoke-test the fitted pipeline end-to-end on synthetic degenerate slides
(0-node, 1-node, off-canvas) — must not crash and must degrade gracefully.
**Guard rule.** Document scope explicitly: "Phase 9 results describe slides inside
validated pairs only." Persist per-feature train-time normalization stats with the
model; inference must reuse them, never refit. Add a deployment-population caveat
section to every Phase 9 report.

## T7. Duplicate / near-duplicate nodes and variant-twin inflation

**Mechanism.** (a) `dataset_builder`/`dataset_builder_v2` deliberately add
variant-twin samples (`review_resolutions.jsonl`, `basis: variant_twin`) — the same
underlying content enters the corpus twice under different deck ids; (b)
exact-hash duplicate decks produce identical slides; (c) within one deck, repeated
layouts yield near-identical nodes. Under grouped CV these inflate absolute scores
(repeated evidence) and, if twins straddle groups, leak outright. Pooled confusion
matrices count the same edit many times.
**Severity:** HIGH.
**Detection test.** Node-level near-dup census: hash normalized base-feature vectors
(rounded) + slide_key-independent layout signature; report cluster sizes and their
group composition. Ablation: keep one row per dup-cluster and re-run headline
metrics; report both numbers.
**Guard rule.** Report Phase 9 metrics BOTH on all rows and on a
deduplicated-by-content view; treat twin-straddling-groups as a split bug (assert
every fingerprint-exact cluster maps to exactly one group).

## T8. Eff-typography / branded-field provenance in base dicts

**Mechanism.** CONFIRMED SAFE TODAY: `eff_size_pt`, bold, is_largest_font, etc. are
computed by `node_features_v2.extract_slide_node_features_v2` from AST v2 built
exclusively from raw copies; grep shows no branded-side write into `"base"` blocks.
The ONLY branded-side features in the repo are ADD-class rows in
`dataset_builder_v2` (`side: "branded"`), which is semantically required (ADD nodes
do not exist on the raw side). Risk is REGRESSION: Phase 9 joins more sources
(chrome, records, graphs); one careless merge reintroduces target fields, and
because context broadcasts slide-wide, contamination multiplies.
**Severity:** MED (regression risk, currently clean).
**Detection test.** Keep the existing static scan (`test_relational_guard.py`
pattern: banned tokens `after|delta|branded|target|truth|transformation_record`)
extended to every new Phase 9 module; plus a data-level assertion: rebuild one
slide's base+context dict and diff against a from-raw-only recomputation (same as
T1's test, applied to base blocks too).
**Guard rule.** New code may import feature extractors only from
`morphlite.features.*` / `morphlite.ast.*`; any import of
`evaluate_baseline`, `ast_diff`, `rules.learn`, or `chrome_diff` inside a Phase 9
feature module fails review. ADD rows keep their own side tag and are never mixed
into raw-side context aggregation.

---

## IMPLEMENTER GUARDS

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
