# Phase 9A — SlideContext + Relative-Feature Schema (DESIGN ONLY)

Status: proposal. No implementation in this phase.
Compliance: all features below are computed from source-deck geometry only
(propagation-cache `base` dicts: `x/y/w/h/cx/cy`, type flags, `text_len_log1p`,
`container_depth`, `eff_size_pt`, `overlap_frac_max`, plus `nbrs` edge lists
and slide-wide aggregation of the same fields). Nothing is derivable from a
branded deck or a transformation record → no leakage path.

## Grounding

- Existing per-node V2 vector (`node_features_v2.py`) already contains:
  `nn3_mean, align_x_resid, align_y_resid, overlap_frac_max, same_type_frac,
  grid_occupancy` (+ base `x_rank_frac, y_rank_frac, nn_dist`). NONE of the
  features below duplicate these.
- Falsified slide aggregates (Phase 8.6/8.7 `context_ablation.slide_context`,
  ~22 features): type fracs, cx/cy mean+std, x/y span, occupied_area, density,
  align_x_conc/align_y_conc, overlap_mean, area mean/std, eff-size mean/max,
  bold_frac, largest_frac, short/long_text_frac. These are DEAD; nothing below
  re-proposes them.

Notation: slide member list `B = {b_1..b_n}` (base dicts), per node centroid
`c_i = (cx_i, cy_i)`. "Band" = maximal cluster of nodes whose rounded
coordinate agrees within tol (tol_x = 0.02 canvas units unless noted).

---

## G1 global_slide_features (slide-shape descriptors beyond dead aggregates)

```yaml
- n_xbands_log1p | MUST | G1 | log1p(count of distinct x-centroid bands via gap-clustering rounded cx) | source_only=yes | deployable=yes | leakage=none (pure source geometry) | signal=slide-intent (grid-structured slides vs freeform)
- n_ybands_log1p | MUST | G1 | log1p(count of distinct y-centroid bands) | source_only=yes | deployable=yes | leakage=none | signal=slide-intent
- band_size_entropy_x | G1 | Shannon entropy of x-band membership sizes / log2(n); high = evenly distributed columns | source_only=yes | deployable=yes | leakage=none | signal=slide-intent
- band_size_entropy_y | G1 | same over y-bands | ... | signal=slide-intent
- grid_regularity_score | MUST | frac of nodes within tol of ANY detected x- or y-band line (consensus alignment, not max-concentration) | deployable=yes | leakage=none | signal=both
- quad_occupied_count | MUST | count of 2x2 quadrants containing >=1 node centroid (0..4) whitespace proxy inverse | deployable=yes | leakage=none | signal=slide-intent
- content_quad_balance | G1 | L1 imbalance across quadrant occupancy fractions sum(|q_k - 0.25|)/2 ; distribution-SHAPE, not coordinate std | deployable=yes | leakage=none | signal=slide-intent
- coloc_text_image | G1 | frac of image centroids with a text centroid within r=0.15 (type co-location) | deployable=yes | leakage=none | signal=slide-intent (image-caption structure)
- title_zone_frac | G1 | frac of text nodes whose bbox intersects top strip y<0.2 and w>0.3 (canonical title zone) | deployable=yes | leakage=none | signal=slide-intent
- margin_symmetry_h | G1 | 1 - |left_content_margin - right_content_margin| / content_width | deployable=yes | leakage=none | signal=slide-intent
- contain_depth_weighted_mean_slide | G1 -> see G4 d0/d1/d2plus; slide-level scalar = mean(container_depth)+1 | deployable=yes | leakage=none | signal=slide-intent
```

## G2 relative_node_features (node-vs-slide relational terms)

```yaml
- rel_x_med | MUST | G2 | cx_i - median_j(cx_j) over same-slide nodes | deployable=yes | leakage=none | signal=relative-meaning (MOVE displacement anchor)
- rel_y_med | MUST | G2 | cy_i - median_j(cy_j) | deployable=yes | leakage=none | signal=relative-meaning
- width_ratio_content | G2 | w_i / content_width (content_width = x_span of slide content) | deployable=yes | leakage=none | signal=relative-meaning
- height_ratio_content | G2 | h_i / content_height | deployable=yes | leakage=none | signal=relative-meaning
- st_rank_x | G2 | rank of cx among SAME-TYPE siblings / sibling_count (global x_rank_frac exists; this is type-conditioned) | deployable=yes | leakage=none | signal=relative-meaning
- st_rank_y | MUST | G2 | rank of cy among same-type siblings / sibling_count (e.g., "3rd bullet of 5") | deployable=yes | leakage=none | signal=relative-meaning (list-position semantics)
- dist_nearest_text | MUST | G2 | min Euclidean centroid distance from node i to any OTHER text node (0 if none) | deployable=yes | leakage=none | signal=both
- dist_nearest_image | G2 | min distance to nearest image node | deployable=yes | leakage=none | signal=relative-meaning
- dist_centroid_norm | G2 | ||c_i - slide_content_centroid|| / max_j ||c_j - slide_content_centroid|| | deployable=yes | leakage=none | signal=relative-meaning
- isolation_index | MUST | G2 | nn_dist_i / mean_pairwise_slide_distance (ratio form; base nn_dist alone is scale-blind across sparse vs dense slides) | deployable=yes | leakage=none | signal=relative-meaning
- edge_margin_min | G2 | min(x, 1-x-w, y, 1-y-h) distance to nearest canvas edge | deployable=yes | leakage=none | signal=both (edge-hugging decorations vs core content)
- centrality_score | G2 | 1 - dist_centroid_norm (complement kept separate for monotone interpretability) | deployable=yes | leakage=none | signal=relative-meaning
```

## G3 spatial_distribution_features (occupancy vectors, radial shape)

```yaml
- occ_row_frac[0..3] | G3 | 4 values: frac of nodes whose cy falls in row k of a 4x4 grid (row marginal of occupancy histogram) | deployable=yes | leakage=none | signal=slide-intent (top-heavy/bottom-heavy layouts)
- occ_col_frac[0..3] | MUST(occ_col_frac_1 only) | G3 | column marginals of same histogram | deployable=yes | leakage=none | signal=slide-intent
- corner_mass | G3 | frac of centroids in the 4 corner cells of the 4x4 grid | deployable=yes | leakage=none | signal=slide-intent
- radial_mean | G3 | mean normalized radial distance from content centroid (unit-free ring position profile) | deployable=yes | leakage=none | signal=slide-intent
- radial_gini | G3 | Gini coefficient of radial distances (spread SHAPE; robust vs plain std, invariant to shift) | deployable=yes | leakage=none | signal=slide-intent
- ring_inner_frac | G3 | frac of nodes within half the max radius (core vs shell split) | deployable=yes | leakage=none | signal=slide-intent
- edge_margin_mean_slide | G3 | slide-level mean of per-node edge_margin_min | deployable=yes | leakage=none | signal=slide-intent
```

## G4 structural_features (graphs: overlap, containment, bands, siblings)

```yaml
- overlap_deg_mean_slide | MUST | G4 | mean over nodes of (#neighbors with IoU>0.05) using nbrs.ALL + IoU check; degree of overlap GRAPH (falsified set had overlap VALUE stats only, never degree) | deployable=yes | leakage=none | signal=slide-intent
- overlap_deg_max_node | G4 | max overlap-graph degree in slide | deployable=yes | leakage=none | signal=slide-intent
- contain_depth_d0_frac | MUST | G4 | frac of nodes at container_depth==0 (top-level) | deployable=yes | leakage=none | signal=both
- contain_depth_d1_frac | G4 | frac at depth==1 | deployable=yes | leakage=none | signal=both
- contain_depth_deep_frac | G4 | frac at depth>=2 | deployable=yes | leakage=none | signal=slide-intent
- band_member_frac | MUST | G4 | frac of nodes belonging to an alignment band of size>=2 (membership, not concentration) | deployable=yes | leakage=none | signal=both
- largest_band_frac | G4 | frac of members in the single largest band | deployable=yes | leakage=none | signal=slide-intent
- group_edge_frac | G4 | frac of nodes with >=1 GROUP nbrs edge | deployable=yes | leakage=none | signal=slide-intent
- align_degree | G4 | per-node #ALIGNMENT edges (from propagation-cache nbrs.ALIGNMENT, currently unused as a feature) | deployable=yes | leakage=none | signal=relative-meaning
- nn_same_type_ratio | G4 | per-node dist to nearest same-type node / nn_dist (inf-like cap 5.0 when none) — ratio form new vs base nn_dist and V2 nn3_mean | deployable=yes | leakage=none | signal=relative-meaning
```

Total proposed: **42** (G1=11, G2=12, G3=10 flattened, G4=10 incl. per-node
align_degree/nn_same_type_ratio). Under the 45 cap.

## MUST-HAVE tier (minimal Phase 9A experiment, 10)

rel_x_med, rel_y_med, st_rank_y, dist_nearest_text, isolation_index,
n_xbands_log1p, n_ybands_log1p, grid_regularity_score, quad_occupied_count,
overlap_deg_mean_slide, contain_depth_d0_frac  *(11 listed — drop
contain_depth_d0_frac first if a strict 10 needed)*

## WHY THIS EXCEEDS THE FALSIFIED SET

- **G1**: dead aggregates summarized coordinates as scalars (mean/std/span);
  they could not express *multi-modal layout structure* — how many distinct
  alignment rails exist, whether nodes sit ON those rails, or which canvas
  regions are empty.
- **G2**: the falsified set was slide-level only, so it gave every node in a
  slide the SAME value and could never score one node against its slide;
  relative terms make context node-specific, which is exactly what MOVE
  disambiguation needs.
- **G3**: dead set reduced distribution to first two moments; histograms,
  radial profiles and corner masses preserve WHERE mass sits, not just how
  spread it is.
- **G4**: falsified `overlap_mean` averaged pairwise IoU VALUES; graph DEGREE,
  containment-depth composition, band membership fractions, and sibling-ratio
  structure were never represented anywhere.
