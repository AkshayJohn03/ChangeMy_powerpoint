# Phase 8.6/8.7 - Context Representation Ablation & Conditional Ambiguity

Rows: 7350 | Groups: 39 | Folds: 5

## Ablation (RandomForest pooled)

| Space | dims | macro F1 | weak macro F1 | MOVE recall | MOVE F1 | UNCH recall |
|---|---:|---:|---:|---:|---:|---:|
| A_node_only | 49 | 0.3787 | 0.3484 | 0.0045 | 0.0088 | 0.9621 |
| B_node_slide | 74 | 0.3747 | 0.3424 | 0.0 | 0.0 | 0.9623 |
| C_node_local | 57 | 0.3872 | 0.3606 | 0.0272 | 0.0523 | 0.9663 |
| D_full | 82 | 0.3772 | 0.3454 | 0.0 | 0.0 | 0.9669 |

## Conditional ambiguity (true-MOVE nodes)

| Space | kNN acc (all) | MOVE entropy | MOVE nbr-move-frac |
|---|---:|---:|---:|
| A_node_only | 0.7752 | 0.9818 | 0.166 |
| B_node_slide | 0.797 | 0.8811 | 0.2029 |
| C_node_local | 0.7886 | 0.9916 | 0.198 |
| D_full | 0.7992 | 0.8909 | 0.2111 |

Deltas vs A (RF): weak -0.003, MOVE recall -0.0045, entropy drop 0.0909 bits

**VERDICT: OUTCOME_1_GENUINE_AMBIGUITY**

NO-GO reinforced: neither slide context nor local aggregation reduces ambiguity or improves MOVE. Targeted label collection (Pool A/B) is the next investment.
