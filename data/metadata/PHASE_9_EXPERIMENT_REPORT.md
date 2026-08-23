# Phase 9 - Slide Context Benchmark (A/B/C/D/E)

Rows post-dedupe: 7272 | Groups: 34 | Folds: 5 | Excluded by dedupe: 78

| Space | macro | weak | MOVE P | MOVE R | MOVE F1 | UNCH R | unsafe | disp-wtd R |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| A_node_only | 0.3702 | 0.3362 | 0.1579 | 0.0068 | 0.013 | 0.9579 | 0.0128 | see json |
| B_slide_broadcast_must | 0.3626 | 0.3252 | 0.0 | 0.0 | 0.0 | 0.9602 | 0.0114 | see json |
| C_node_plus_g1g3_broadcast | 0.3594 | 0.3205 | 0.0 | 0.0 | 0.0 | 0.9638 | 0.0098 | see json |
| D_node_plus_relative_structural | 0.369 | 0.3337 | 0.0 | 0.0 | 0.0 | 0.9644 | 0.0113 | see json |

**Discovery signal:** False
**Promotion pass:** False

Displacement-weighted MOVE recall (evaluation-only join): A_node_only: 0.0032; B_slide_broadcast_must: 0.0; C_node_plus_g1g3_broadcast: 0.0; D_node_plus_relative_structural: 0.0
Deltas (RF): B_slide_broadcast_must: {'move_recall_delta_vs_A': np.float64(-0.0068), 'move_f1_delta_vs_A': np.float64(-0.013), 'unchanged_recall_drop_vs_A': 0.0, 'unsafe_rate_vs_A': -0.0014, 'weak_delta_vs_anchor': -0.0316}; C_node_plus_g1g3_broadcast: {'move_recall_delta_vs_A': np.float64(-0.0068), 'move_f1_delta_vs_A': np.float64(-0.013), 'unchanged_recall_drop_vs_A': 0.0, 'unsafe_rate_vs_A': -0.003, 'weak_delta_vs_anchor': -0.0363}; D_node_plus_relative_structural: {'move_recall_delta_vs_A': np.float64(-0.0068), 'move_f1_delta_vs_A': np.float64(-0.013), 'unchanged_recall_drop_vs_A': 0.0, 'unsafe_rate_vs_A': -0.0015, 'weak_delta_vs_anchor': -0.0231}
