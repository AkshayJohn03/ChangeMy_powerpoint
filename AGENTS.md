# BrandMorph / MorphLite — Engineering Notes (persistent memory)

## DATA COMPLIANCE POLICY (highest priority, always applies)

1. **Never display real deck filenames, file paths, slide text, client names,
   or any deck contents** in chat output, tool arguments, or logs.
2. All decks in `data/source/**` are physically renamed to opaque ids
   (`deck_0001.pptx`, ...). Always refer to decks by these opaque ids.
3. The ONLY mapping from opaque id to original identity is
   `data/metadata/deck_registry.json` — RESTRICTED: never print, cat, grep,
   or transmit this file. It is gitignored.
4. Python pipelines may read full contents locally for feature extraction and
   training. The assistant may only see **aggregate statistics** (counts,
   distributions, metrics) or **synthetic verification decks** built in tests.
5. No deck content may be sent to any cloud service / external API.
6. Before committing anything under `data/` (whitelisted aggregates only),
   run the leakage self-check:
   `python -m morphlite.tests.test_no_leakage` — it must PASS.

## Project map

- App: `backend/` FastAPI decompiler/builder + `ui/` React/Tauri studio.
- Intelligence: `morphlite/` package.
  - `ast/` extractor (+v2 effective typography), `chrome.py`, `effective.py`
  - `features/` node/deck features (+fingerprint)
  - `rules/` brand tokens, learned rules engine
  - `training/` inventory → extract → discovery → alignment → diff → datasets → benchmarks
- Data workspace: `data/source/<bucket>/<batch>/deck_NNNN.pptx`,
  derived trees `data/extracted/{ast,ast_v2,chrome}`, manifests in `data/pairs/`,
  reports in `data/metadata/`.

## Canonical commands (venv: backend\venv\Scripts\python.exe)

```
python -m morphlite.training.inventory --apply      # ingest + anonymized sort
python -m morphlite.training.extract_asts           # AST v1 (schema has shape_id)
python -m morphlite.training.build_ast_v2           # AST v2 + effective typography
python -m morphlite.training.extract_chromes        # chrome v1.1 geometry structures
python -m morphlite.training.pair_discovery         # validate pairs / alternation
python -m morphlite.training.pair_alignment         # object-level alignment
python -m morphlite.training.ast_diff               # transformation records + taxonomy
python -m morphlite.rules.learn                     # LEARNED_RULES.json
python -m morphlite.training.evaluate_baseline      # deterministic baseline scoring
python -m morphlite.training.fingerprint_stats      # gate 3 stats
python -m morphlite.training.dataset_builder        # V1 datasets
python -m morphlite.training.dataset_builder_v2     # V2 datasets
python -m morphlite.training.bench_classifiers all  # V1 benchmark protocol
python -m morphlite.training.bench_classifiers_v2   # V2 benchmark protocol
python -m morphlite.tests.test_no_leakage           # leakage self-check (gate)
```

## Verification-gate discipline

Commit only after the corresponding gate passes; name the gate in the commit
message. Gates 1–2 (inheritance resolver, AST v2 enrichment) are done.
