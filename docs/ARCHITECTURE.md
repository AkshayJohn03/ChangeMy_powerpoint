# Architecture

## Components

### Backend (`backend/`, FastAPI `0.5.0`)

- `main.py` — app assembly, `GET /api/health`, mounts v01/v02/tag routers.
- `decompiler.py` — `SlideDecompiler`: reads `.pptx` (python-pptx + lxml),
  handles text containers, pictures, auto-shapes, freeforms, lines and
  connectors into a slide AST of nodes `{bbox, type, paragraphs{runs}}`.
- `builder.py` — `BrandTokens` + `NativePPTXBuilder`: applies the brand system
  and writes a native `.pptx`.
- `routes_v02.py` — `POST /api/v02/process|spec|export`, heuristic/Mock
  fallback, content hash + binary-changed flag.
- `routes_tag.py` — `POST /api/tag/health|spec|process` via
  `TemplateTagPipeline`.

### Studio (`ui/`, React + Vite, Tauri wrapper)

Splash -> import -> studio canvas (bbox overlays, drag, brand token pickers)
-> export download. Talks to the backend over `VITE_API_URL`
(`ui/.env.example`). `api/index.py` is the Vercel serverless entry that
rewrites `/api/*`.

### Intelligence (`morphlite/`)

- `ast/` — extractor, effective-property inheritance resolver, chrome
  geometry, stable node ids.
- `features/` — node/deck features, geometry fingerprints.
- `graph/` — slide-graph builder (9 edge types), relational features.
- `rules/` — brand tokens, deterministic engine, rule learner.
- `training/` — inventory, extraction, discovery, alignment, diff, datasets,
  benchmarks, bake-off.
- `inference/` — hybrid planner, confidence, safety gate, model loader,
  policy/decision layer, v2 engine.
- `evaluation/` — slide/plan/property/safety metrics + adversarial guards.
- `render/` + `spec/` — deterministic `BrandRenderer` over a 12-archetype
  `DeckSpec` schema.
- `llm/` — provider abstraction (Azure/OpenAI behind an endpoint allowlist)
  plus an offline-safe Mock/heuristic path.
- `models/` — `ContentModel` extractor (visual-order text, connector skip).
- `pipeline/` — v01 (`template_styled`), template-driven/filler, v02
  (`integrated_v2`), tag (`template_tag`, `tag_injector`), `brand_profile`,
  `pptxgen_bridge` (PptxGenJS edge rendering via Node subprocess).

## Data flow (v02 intelligent path)

```text
.pptx -> SlideDecompiler -> ContentModel (visual order)
      -> SpecBuilder (LLM or heuristic) -> DeckSpec JSON
      -> BrandRenderer -> branded .pptx
```

v01 short-circuits rendering: it keeps raw shapes and only swaps
backgrounds, typography, fills and line colors. The tag path keeps the brand
master untouched and only fills `{placeholders}`.

## API contract (stable)

- `GET  /api/health` -> `{status, version, pipelines[]}`
- `POST /api/v01/process` (multipart deck) -> branded `.pptx` download
- `POST /api/v02/process` (multipart deck) -> `{deck_id, slides[], archetypes[]}`
- `POST /api/v02/export` (DeckSpec JSON) -> branded `.pptx` download
- `POST /api/tag/process` (multipart deck) -> branded `.pptx` download
- `POST /api/tag/spec` (multipart deck) -> tag-fill preview JSON

## Deployment

- Local: uvicorn backend on `:8000` + Vite dev server on `:5173`.
- Desktop: PyInstaller spec for the backend (`backend/*.spec`); Tauri wraps
  the UI (`ui/src-tauri`).
- Portfolio: `vercel.json` builds `ui/dist`, `/api/*` -> `api/index.py`.
