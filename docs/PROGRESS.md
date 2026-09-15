# Progress history (Phases 1–14, v0.1–v0.3)

Source of truth for dates/authors: `git log`. Headline trail:

## Foundations

- Compliance layer: opaque deck ids, restricted registry, leakage gate.
- AST v2 with effective-typography enrichment (gates 1–2 verified).
- Training chain: inventory → AST/chrome extraction → pair discovery →
  alignment → diff → datasets v1/v2 → grouped-CV harness with promotion
  gates → intent ablation → hybrid inference layer.

## Falsification arc (Phases 6–9)

- Phase 6: slide-graph package + relational benchmark — GO for scoped
  label-propagation experiment.
- Phase 7: OOF-probability propagation — **NO-GO** (seed-quality limit).
- Phase 7.5/7.7: MOVE forensics — misses are small axis-pure displacements
  of non-text shapes; seed-recovery gives 24x MOVE recall seeds but
  propagation stays NO-GO.
- Phase 8/8.6/8.7/9: slide-context and local-aggregation representations
  **falsified** as MOVE recovery paths; unfalsified residue is medium
  structural moves with uniform ambiguity.

## Product arc (v0.1–v0.3, Phases 10–14)

- v0.1 (Phases 10–12): production action model (RF winner, OOF-evaluated),
  thresholds, predictor/policy/decision layer, model card + frozen schema,
  end-to-end pipeline + FastAPI v01 routes.
- v0.2 (Phases 12.5–12.7): BrandProfile abstraction, review UI, deterministic
  brand layer, integrity verifier, mutation truth layer, batch validation.
- v0.3 (Phases 13–14): template-driven pipeline + TemplateFiller, ML
  slide-type classifier (HistGBDT) wired in, connector/arrow preservation,
  contrast/logo fixes, per-node v2 relational model (REMOVE F1 0.66).

## v02 / tag / edge session (current head)

- ContentModel → DeckSpec → BrandRenderer stack with offline-safe
  Mock/heuristic fallback; FastAPI v02 routes; backend `0.5.0`.
- Docxtemplater-style tag pipeline + tag injector + `/api/tag/*` routes.
- PptxGenJS bridge for edge rendering; multi-model bake-off
  (`training/model_bakeoff.py`); framework survey memo
  (`research/FRAMEWORK_AND_MODEL_MEMO.md`).
- Vercel wiring (`vercel.json`, `api/index.py`), env-based API base in UI,
  tri-pipeline UI work in progress.

## What is NOT done

- Tag-injected brand master copy (template currently has no `{tags}`).
- Synthetic 3x + minority-class retraining + gated promotion.
- Tri-pipeline studio toggle + feedback capture loop.
- Canvas upgrade (PPTist-style) and edge-render cutover.
