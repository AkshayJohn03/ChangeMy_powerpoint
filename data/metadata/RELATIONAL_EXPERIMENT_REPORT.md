# Relational Experiment Report (Phase 6)

Question under test: *Does relational/contextual information materially improve prediction of RESTYLE, RESIZE, REMOVE, MOVE versus independent node features — enough to justify a learned message-passing model?*

## Protocol

- Data: 7,350 raw-side node samples across 43 golden deck pairs; **39 effective groups** (deck/template families); ADD excluded (set-prediction scope).
- CV: StratifiedGroupKFold grouped by family token, 5 folds (auto-selected via min-class/group constraints), pooled predictions reported.
- Models: Dummy / DecisionTree / RandomForest(300) / HistGBDT.
- Experiments: `BASE_NODE_ONLY` (V2 features) · `ORACLE_CONTEXT` (+ TRUE neighbor labels — research-only upper bound) · `ANCHOR_CONTEXT` (+ deterministic rule anchors, deployable) · geometry/typography/group relational ablations · `ALL_RELATIONAL`.
- Commands executed:
  - `python -m morphlite.training.relational_benchmark --rebuild`
  - `python -m morphlite.training.intent_ablation` (prior phase)
  - harness: `run_evaluation()` full 43 pairs
  - gates: `test_graph`, `test_evaluation`, `test_relational_guard`, `test_no_leakage`

## Validity checks before trusting results

- Oracle features non-degenerate: 99.7% of rows carry neighbor signal; neighborhood homophily is strong (MOVE nodes: mean weak-neighbour fraction 0.828; REMOVE 0.862; UNCHANGED 0.069).
- A zero-column plumbing bug (sentinel `"__oracle__"` never expanded) was caught because ORACLE == BASE exactly; fixed, regression test added (`test_relational_guard.py` pins it).
- Adversarial review found **no oracle/truth path into deployable code**; guards added for schema-drift and source-scan containment.

## Headline results (RandomForest, pooled grouped CV)

| Experiment | cv macro F1 | weak-class macro F1 | MOVE F1 |
|---|---|---|---|
| BASE_NODE_ONLY | 0.4145 | 0.350 | 0.009 |
| **ORACLE_CONTEXT** | **0.6007** | **0.625** | **0.745** |
| ANCHOR_CONTEXT (deployable) | 0.4191 | 0.357 | 0.026 |
| ALL_RELATIONAL (static edges) | 0.4155 | 0.353 | 0.035 |

MOVE recall: BASE 0.004 -> ORACLE **0.660**; ANCHOR 0.014. DecisionTree oracle: weak 0.550 / MOVE recall 0.689 (consistent).

Feature-ablation: geometry-only, typography-only and group-only relational blocks each add <= +0.003 macro — static hand-crafted edge statistics carry almost nothing; the signal lives in *labelled neighbour state*.

## Answers to the six mandated questions

1. **Does oracle context materially improve weak classes?** YES — weak macro +0.275, macro +0.186, MOVE recall +0.656. Far beyond the +0.10 interest threshold.
2. **Does predicted anchor context capture that gain?** NO — +0.007 weak / +0.017 MOVE-F1 (~3%). Deterministic anchors cover only 7.2% of nodes and emit no RESIZE/MOVE ops.
3. **Does MOVE improve enough to justify message passing?** The *information* is proven present (oracle MOVE F1 0.745). Since deployable input cannot contain true neighbour labels, the justified mechanism is iterative propagation of *predicted* soft labels — i.e., exactly what message passing does.
4. **Which relational features contribute most?** None statically. Discriminative power comes from labelled neighbourhood state (homophily), which static aggregates without labels cannot express.
5. **Unsafe destructive predictions increase?** Deployable variants show no increase (MOVE/REMOVE application remains safety-gate-blocked). Full-harness deterministic baseline records 4.63/pair approved-but-wrong-node operations — quantified motivation to keep confidence gating strict.
6. **Small message-passing experiment justified?** **GO** — narrowly scoped.

## GO decision — scoped Level-3 experiment

Implement 2-round label propagation over the existing graph edges (alignment/group/containment), seeded by **out-of-fold confident predictions** of any promoted/base model (NOT rule anchors alone, NOT true labels). Framework-free first (numpy/sklearn). Promotion gate vs `ANCHOR_CONTEXT` baseline under identical CV:

```text
weak_class_macro_f1_delta >= +0.10   AND
MOVE recall               >= 0.25    AND
unsafe destructive rate   <= deterministic baseline
```

If propagation fails these gates despite the oracle evidence, stop and invest in labels/correspondence instead (more validated pairs, manual loop).

## Deck intent

Stays human-in-the-loop ("Keep layout / Apply brand / Rebuild" UI choice). ML intent not pursued at N=74; every future user decision becomes a labelled example.

## Files created (Phase 6)

`morphlite/graph/{__init__,relations,builder,features,oracle_features}.py`,
`morphlite/evaluation/{__init__,plan_metrics,property_metrics,slide_metrics,safety_metrics,harness}.py`,
`morphlite/training/relational_benchmark.py`, `morphlite/tests/{test_graph,test_evaluation,test_relational_guard}.py`.

Test results: GRAPH GATE PASSED · EVALUATION GATE PASSED · RELATIONAL GUARD PASSED · NO LEAKAGE GATE PASSED.

Artifacts: `RELATIONAL_BENCHMARK.json`, `EVALUATION_HARNESS.json` (43 pairs / 301 slides aggregate only).
