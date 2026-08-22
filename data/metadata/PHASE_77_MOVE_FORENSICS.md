# Phase 7.7 - MOVE Error Forensics

True MOVE nodes: **441** | detected: **48** | missed: **393**

## Detected vs missed distributions

| Feature | detected median | missed median | AUC(det vs miss) |
|---|---|---|---|
| disp | 0.05181 | 0.03678 | 0.4871 |
| dx | 0.0 | 0.01007 | 0.4529 |
| dy | 0.05181 | 0.03066 | 0.6288 |
| overlap_before_after | 0.48715 | 0.4356 | 0.4383 |
| match_confidence | 0.9775 | 0.9801 | 0.5875 |
| group_size | 1.0 | 1.0 | 0.4885 |
| group_move_frac | 0.0 | 0.0 | 0.4975 |
| depth | 0.0 | 0.0 | 0.4885 |
| text_len_log | 2.8029 | 0.0 | 0.5738 |

## Missed-MOVE taxonomy

| Bucket | Count | Share of misses |
|---|---:|---:|
| vertical_only_move | 177 | 0.45 |
| other | 138 | 0.351 |
| horizontal_only_move | 67 | 0.17 |
| large_displacement | 11 | 0.028 |

**Dominant failure mode:** `vertical_only_move` (45% of misses)

**Recommended action:** Axis-specific signal -> add directional displacement features

Fold-safety audit note: D_hybrid OOF predictions derive exclusively from fold-safe component models; forensic deltas above use branded-deck ground truth and are marked non-deployable.

## Interpretation correction (post tie-safe AUC fix)

With proper tie-handled AUCs the picture sharpens considerably:

| Feature | AUC | Reading |
|---|---:|---|
| group_size | 0.489 | NO separation |
| depth | 0.489 | NO separation |
| overlap_before_after | ~0.47-0.53 | none |
| match_confidence | ~0.60 | mild |
| dy | 0.629 | weak |
| text_len_log | 0.574 | weak |

Miss taxonomy: vertical-only 45%, horizontal-only 17% (axis-pure combined 62%),
'other' 35% of which 60% are NON-TEXT shapes at depth 0 (not nested/grouped).

### Evidence-based conclusion

The missed MOVE population consists mostly of SMALL AXIS-PURE DISPLACEMENTS OF
TOP-LEVEL NON-TEXT SHAPES whose raw-deck appearance does not encode the future
designer displacement. Separation between detected and missed on ALL available
raw-side signals is weak (AUC <= 0.64).

Per the decision tree:
- Correspondence failure? NO (match confidence identical both sides).
- Missing deployable representation? PARTIALLY - no raw-side directional
  displacement signal exists by definition; axis/type context adds little.
- No separable signal? YES - this is the dominant finding.
- Strong relational dependency? NOT INDICATED (grouping rare in misses).

Therefore the next investment is TARGETED LABEL COLLECTION of non-text shape
repositioning cases plus acceptance that MOVE carries an irreducible ambiguity
floor at current data scale. Neural MorphNet remains BLOCKED; a GNN cannot
recover input signal that does not exist in the raw representation.
