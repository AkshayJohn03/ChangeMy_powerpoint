# BrandMorph Deck Engine

Hybrid layout-intelligence engine that converts raw, unformatted PowerPoint decks
into brand-compliant decks (Akkodis visual system: dark navy `001F33`, gold
`FFB81C`, 13.33 x 7.5 in) while preserving content, shapes, diagrams and images.

- **Backend:** `backend/` — FastAPI decompiler / brand pipelines / native `.pptx` export.
- **Studio:** `ui/` — React + Vite canvas app (Tauri desktop wrapper in `ui/src-tauri`).
- **Intelligence:** `morphlite/` — slide AST extraction, features, rules, trained
  classifiers, hybrid planning, evaluation harness.

Backend version: `0.5.0` — three pipelines: `v01_template_styled`,
`v02_intelligent`, `tag_docxtemplater`.

---

## 1. How it works

```text
Raw .pptx
   |
   +-- v01 (TemplateStyled) -- direct brand styling on the raw deck,
   |                           all shapes/arrows/images preserved
   |
   +-- v02 (Intelligent) ----- ContentModel -> DeckSpec -> BrandRenderer
   |                           (restructures dense text into card grids)
   |
   +-- tag (Docxtemplater) --- fills {title}/{bullets} tags inside a copy of
                               the brand master template (pixel-perfect master)
   |
Native branded .pptx
```

### Pipeline comparison

| Pipeline | Endpoint | Mechanism | Best for | Status |
|---|---|---|---|---|
| v01 TemplateStyled | `POST /api/v01/process` | Recolors fonts/fills, swaps backgrounds, keeps every raw shape | Decks with custom diagrams, flows, arrows | Ready, tested end-to-end |
| v02 Intelligent | `POST /api/v02/process` | `ContentModel` (visual-order text) -> `DeckSpec` JSON (LLM or heuristic) -> deterministic `BrandRenderer` | Dense text/bullet slides needing restructure | Ready, tested end-to-end |
| tag Docxtemplater | `POST /api/tag/process` | Injects `{title}/{subtitle}/{bullets}/{card_*}` tags into brand template, then fills from raw content | Executive decks needing 100% master fidelity | Ready; requires a tag-injected template copy |

Health: `GET /api/health`. Spec export: `POST /api/v02/export`.
Tag spec preview: `POST /api/tag/spec`. Vercel serverless entry: `api/index.py`.

---

## 2. Repository layout

```text
backend/            FastAPI app (main.py, decompiler.py, builder.py,
                    routes_v02.py, routes_tag.py, requirements.txt)
ui/                 React + Vite studio (src/App.tsx), Tauri wrapper,
                    .env.example (VITE_API_URL)
api/                Vercel serverless entry (index.py, requirements.txt)
morphlite/          Intelligence package
  ast/              Slide AST extractor, effective-typography enrichment,
                    chrome (geometry) structures, node ids
  features/         Node/deck features, geometry fingerprints
  graph/            Slide-graph builder, relations, oracle features
  rules/            Brand tokens, deterministic rules engine, rule learner
  training/         inventory -> extract -> discovery -> alignment -> diff ->
                    datasets -> benchmarks -> bake-off
  inference/        Hybrid planner, confidence, safety gate, model loader,
                    v2 engine, policy/decision layer
  evaluation/       Metrics harness (slide/plan/property/safety) + guards
  render/           BrandRenderer (archetype renderers, fit-to-shape)
  spec/             DeckSpec schema (12 slide archetypes)
  llm/              Provider abstraction (Azure/OpenAI, endpoint allowlist)
                    + MockLLM heuristic fallback (offline-safe)
  models/           ContentModel extractor
  pipeline/         v01/v02/tag/integrated pipelines, brand profile,
                    template filler, tag injector, PptxGenJS bridge
  tests/            Leakage, inheritance, graph, propagation/relational guards
  models/           Trained artifacts metadata (all NOT_PROMOTED, see docs)
data/               Local-only research workspace (NEVER committed, gitignored):
                    source/ extracted/ pairs/ processed/ metadata/
                    annotations/ synthetic/
models/             Local-only trained binaries (gitignored *.joblib)
research/           Framework survey + model bake-off memo
docs/               Architecture, pipelines, models, compliance, progress
```

---

## 3. Quickstart

### Backend (Windows)

```bat
.\backend\venv\Scripts\python.exe backend/main.py
```

Serves `http://localhost:8000`. Logs to `backend.log`.

### Frontend

```bat
cd ui
npm install
npm run dev
```

Open `http://localhost:5173`. Point it at the backend with `VITE_API_URL`
(see `ui/.env.example`; default `http://localhost:8000`).

### CLI (offline, no LLM needed)

```bat
.\backend\venv\Scripts\python.exe -m morphlite raw_deck.pptx --no-llm
```

Extracts `ContentModel`, builds a `DeckSpec` with the heuristic/Mock path,
renders a branded deck deterministically.

### One-click runner

See the runner script at repo root (`BrandMorph.bat`) which starts backend + UI.

### Vercel (portfolio deploy)

`vercel.json` builds `ui/dist` and rewrites `/api/*` to `api/index.py`
(python3.11). Set `VITE_API_URL` to the deployed backend URL.

---

## 4. MorphLite intelligence — what was built

Pipeline stages (canonical commands use `backend\venv\Scripts\python.exe`):

1. **Inventory** — ingest + anonymize decks to opaque ids
   (`python -m morphlite.training.inventory --apply`).
2. **AST extraction** — v1 AST + v2 AST with effective-typography enrichment
   (gates 1–2 verified: inheritance resolver, v2 enrichment).
3. **Chrome extraction** — slide geometry structures.
4. **Pair discovery / alignment** — raw-to-branded slide pairing + object-level
   alignment from golden pairs.
5. **AST diff** — transformation records + edit taxonomy
   (ADD / REMOVE / MOVE / RESIZE / RESTYLE / RECOLOR / UNCHANGED).
6. **Rules + baseline** — learned brand rules (`rules/learn`), deterministic
   baseline scoring.
7. **Datasets + benchmarks** — v1/v2 dataset builders, grouped-CV harness with
   promotion gates, intent ablation, hybrid inference layer.
8. **Relational track** — slide-graph package, relational benchmark
   (oracle/anchor), context ablations, propagation experiments.

Research outcomes (see `docs/MODELS.md`, `docs/PROGRESS.md`):

- Label propagation at current seed quality: **NO-GO** (Phase 7).
- Slide-context and local-aggregation representations falsified as MOVE
  recovery paths (Phases 8–9).
- Model bake-off on 7,888 nodes / 49 features: xgboost and RF tie at macro
  F1 ~0.47; class imbalance (not algorithm) is the bottleneck; per-node v2
  model reaches REMOVE F1 0.66 (Phase 14).
- All trained intent/node models are **NOT_PROMOTED** — promotion gates
  (`min_cv`, minority-class F1, size, latency) decide promotion, not best-mean.
- Slide-type classifier (HistGBDT, F1 ~0.51 on 422 slides / 30 decks) routes
  the template-driven pipeline.

---

## 5. Dataset (aggregate only)

Local research workspace only — never committed. Decks are anonymized to
opaque ids (`deck_0001.pptx`, …). Current scale (aggregates):

- **261 decks / 2,323 slides / ~54k nodes**
  (TEXT ~46%, SHAPE ~25%, IMAGE ~19%, GROUP ~7%, plus lines/tables/arrows/charts)
- **43 golden raw-to-branded pairs → 301 golden slide pairs**
- Node dataset v2: **7,888 rows**; slide-type set: **422 slides / 30 decks**

See `docs/COMPLIANCE.md` for the binding data-compliance policy.

---

## 6. Product state (v0.1 -> v0.3)

- **v0.1** — end-to-end pipeline (decompile -> features -> model -> policy ->
  mutate -> export), FastAPI v01 routes, production action model, model card +
  frozen feature schema + policy thresholds.
- **v0.2** — deterministic brand layer (backgrounds/fonts/colors/fills),
  integrity verifier, review UI with brand/ML/integrity breakdown, mutation
  truth layer, batch validation.
- **v0.3** — template-driven pipeline (brand template layouts as base, slide-type
  classification, content import preserving template styling), TemplateFiller,
  connector/arrow preservation fixes, contrast fixes, logo application.

See `docs/PROGRESS.md` for the full phase history (Phases 1–14).

---

## 7. Roadmap

1. Tag-inject the brand master copy (`pipeline/tag_injector.py`) so the `tag`
   pipeline replaces text inside 100% native masters.
2. Synthetic 3x augmentation from golden pairs + class-weighted/focal training
   to lift minority classes (MOVE/RESTYLE/RECOLOR).
3. Train GNN + small transformer variants in parallel (code ready in
   `training/model_bakeoff.py`); promote HGB/GNN ensemble through the gates.
4. Studio review UX: tri-pipeline toggle (Fidelity / Restructure / Master),
   per-slide reconciliation, feedback capture loop.
5. Replace bbox-div canvas with a PPTist-style canvas model; PptxGenJS bridge
   for edge rendering.

---

## 8. Docs

- `docs/ARCHITECTURE.md` — components, data flow, API contract
- `docs/PIPELINES.md` — the three pipelines in detail
- `docs/MODELS.md` — features, datasets, bake-off, promotion gates
- `docs/COMPLIANCE.md` — data-compliance policy (binding)
- `docs/PROGRESS.md` — phase history (Phases 1–14, v0.1–v0.3)
- `AGENTS.md` — engineering notes, canonical commands, gate discipline
- `research/FRAMEWORK_AND_MODEL_MEMO.md` — framework survey + bake-off memo
