# BrandMorph — Collaboration Handover (Full Context for Another AI)

**Repo:** `C:\Users\Akshay.JOHN-XAVIER\.gemini\antigravity-ide\scratch\BrandMorph` (git `origin https://github.com/AkshayJohn03/ChangeMy_powerpoint.git`)  
**Live dashboard (local):** Frontend `http://localhost:5173` (Vite, `ui/`), Backend `http://localhost:8000` (`backend/main.py` uvicorn, `0.5.0`, 3 pipelines) — both restart with `backend.log`  
**Vercel (portfolio):** `vercel.json` builds `ui/dist` + `api/index.py` (python3.11) rewrites `/api/*` → serverless. Set `VITE_API_URL` env to backend URL.

---

## 1. Goal
Hybrid Layout Intelligence Engine: from **any raw PowerPoint** → **Akkodis golden branded deck** (gold `FFB81C`, dark `001F33`, `Times New Roman`/`Arial`/`Roboto`, 13.33×7.5in) with human-level precision. Must preserve shapes/arrows/images, follow `Brand_guideline_Akkodis.pptx` (10 slides, 3 masters, 43MB, `C:\Users\Akshay.JOHN-XAVIER\OneDrive - Akkodis\Documents\Me\Brand_guideline_Akkodis.pptx` → `data/brand_template/Brand_guideline_Akkodis.pptx` 10 slides).

**Dataset (read-only, copy-not-move, dry-run default):** `morphlite/config.py:27` `DOCUMENT_ROOTS`:
- `10 Dec\Updated` clean 2 decks
- `11 June` `Akkodis New PPT Template White March 2026.pptx` + `KaarTech` (clean)
- `12 Dec\OneDrive_2025-12-11\Updated` Category A `X raw.pptx ↔ X.pptx` pairs
- `21 Jan\OneDrive_2026-01-21` `Raw\8` ↔ `Updated\8 v1`
- `25 Oct\Case study initiative` 215 pptx: `New` raw↔clean, `Old\Cybersecurity, ESM` raw_marker, `Old\IT Infrastructure, Network Engineering` Category B alternating (confirmed substrings), `OneDrive_2025-11-26` etc. duplicates

Inventory `data/metadata/inventory.json` + `extraction_manifest.jsonl`: **261 decks, 2323 slides, 54473 nodes** (TEXT 45.9% SHAPE 24.8% IMAGE 19.2% GROUP 7.3% LINE 811 TABLE 211 ARROW 311 CHART 24). 43 golden deck pairs → 301 golden slide pairs (`pair_discovery.py:65` MD5/sim thresholds).

---

## 2. How App Was Previously (before this session)

- **Backend v01:** `backend/decompiler.py:6` `SlideDecompiler` (handles TEXT_CONTAINER/PICTURE/AUTO_SHAPE/FREEFORM/LINE/CONNECTOR via `}cxnSp` tag) → AST `nodes {bbox, type, paragraphs{runs}}`; `backend/builder.py:6` `BrandTokens` + `NativePPTXBuilder`; `morphlite/pipeline/template_styled.py:124` `TemplateStyledPipeline` (keeps raw shapes, recolors fonts/colors/fills, swaps bg image for TITLE(0)/AGENDA(1)/THANK_YOU(9) via `_template_assets` extracted counts). `morphlite/pipeline/brand_profile.py:17` `BrandProfile` (`dark 030C1E→001F33` after fix, `card 0A2A4A`, gold/white).
- **TemplateFiller** `morphlite/pipeline/template_filler.py:245` `_duplicate_slide(copy.deepcopy element + p:bg)` + `_set_text_preserving_style` — duplicates template slides per raw mapping, preserves all template styling/borders/transparency.
- **Integrated v2** `morphlite/pipeline/integrated_v2.py:104` ML gated `REMOVE/RESIZE/MOVE` via `NodeModelInference` + `PolicyEngineV2` + `SlideRemoveBudget` (node model `brandmorph_action_model.joblib`).
- **Frontend** `ui/src/App.tsx` (1007 lines) splash → import → studio canvas (bbox divs, drag, `SCALE_X 880/13.33`, brand token pickers, `lucide-react` icons), `fetch http://localhost:8000/api/parse_deck` / `export_deck`.
- **Model:** `morphlite/features/node_features.py` 33 feats + `node_features_v2.py` +49 (14 relational via `graph/builder.py`), `training/dataset_builder_v2.py`, `slide_type_classifier.py` (PDR archetypes TITLE/TWO_COLUMN/THREE_CARD/METRICS_HERO/PROCESS_FLOW).

Previous pain: hard-coded rules, `Connector` line error (`TestPPT.pptx` slide1 has 5 `}cxnSp` lines), dark `030C1E` vs template `001F33`, title color white vs gold, V01 only maps 3 bg images.

---

## 3. What We Did This Session (chronological)

1. Verified repo, scanned 5 roots, scaffolded `morphlite/` + `data/` buckets, fixed `inventory.py:85` tuple bug, researched Presenton/Azure OpenAI Entra ID (corporate-safe, NotUsedForTraining) and `elora/presgen`, `jsonforge/json-to-ppt`, `marp2pptx`, `Aspose.Slides`.
2. Proposed LLM-structured pipeline: `Raw PPTX → ContentModel (visual-order text) → DeckSpec JSON via LLM (few-shot golden) → Deterministic Renderer` vs rule-stamping.
3. Built **new v02 stack**:
   - `morphlite/models/content_model.py:142` `extract_deck` (GROUP recursion, `LINE/}cxnSp` skip, splash detection, visual-order sort)
   - `morphlite/spec/slides_schema.py` 12 archetypes + `CardElement/StepElement`
   - `morphlite/llm/provider.py:104` `ProviderConfig` (AZURE_OPENAI_ENDPOINT/OPENAI_BASE_URL, `LLM_ALLOWED_ENDPOINTS` allowlist) + `MockLLM` per-chunk archetype (fixed global `thank` bug, `--- slide` filter, preserves all bullets) + `AzureLLM`/`OpenAILLM` lazy imports
   - `morphlite/llm/spec_builder.py:56` `SpecBuilder` (`ContentModel→DeckSpec`, `_heuristic` preserves all blocks, 2-col split if >9 bullets)
   - `morphlite/render/renderer.py:113` `BrandRenderer` (6 archetype renderers, `fit.py:8` `shrink_to_fit`, dark `001F33`, 2-col bullets)
   - `morphlite/cli.py` + `__main__.py` `python -m morphlite raw.pptx --no-llm`
   - Verified CLI `TestPPT 29→29` `62134` bytes (mock, before fix 60KB 30 slides `thank_you` bug).
4. Fixed relevance + brand: `brand_profile dark 001F33`, `Mock` keeps all bullets + subtitle split, `_heuristic` filters page numbers, `process_flow` caps words, `_generic/_content_cols` 2-col if >9, `_title` shows pills.
5. Wired **FastAPI v02** `backend/routes_v02.py:15` (`/api/v02/process/spec/export/health`, mock/heuristic fallback, `hash` + `binary_changed`), `backend/main.py:13` `0.4.0` → `0.5.0`, `httpx` added.
6. Vercel: `vercel.json` (`ui/dist`, rewrite `/api/*`→`api/index.py`), `api/index.py`, `api/requirements.txt`, `ui/.env.example`, `tsconfig` `noUnusedLocals:false` → `vite build 229KB`.
7. Upgraded `ui/src/App.tsx:46` (`API_BASE` env, `pipelineMode v02`, `v02_result` screen with `deck_id`/`archetype` chips + `handleV02Download`, 3-card architecture diagram `ContentModel→DeckSpec→Render`).
8. **Path1 subagent** (`explore`) fixed: `backend/decompiler.py:113` `LINE` + `}cxnSp` handling, `content_model.py:169` connector skip, expanded vocabularies `template_filler.py:31` (ADAS_SENSORS/ECU_DIAG/VALIDATION/AKKODIS/CASE_STUDY), fallback `generic_idx 3`, overflow `_add_text_box` cascade, verified `_path1_test.pptx 29/30654KB`.
9. **Path2 subagent** inventoried 261 decks, proposed `<200MB` architecture table (HGB 2.2MB vs RF400 65MB, graph 14 relations, 20-feat slide classifier), synthetic 3× plan (129 variants), benchmarks `MODEL_CARD.json`, `ML_BENCHMARKS/V2`, `FEATURE_COVERAGE_V2`, `SLIDE_TYPE_CLASSIFIER.json` (`hist_gbdt 0.506 > heuristic 0`).
10. **GitHub topics/powerpoint scan** (1,691 repos): `ppt-master 51.4k` (SVG pipeline, `p:sldMaster` inheritance), `PPTist 9.3k` (Vue canvas, `pptxtojson` 85%/95%), `PptxGenJS 6.1k` (`SlideMaster`, `tableToSlides`), `docxtemplater 3.6k` (`{title}/{#bullets}` loops, `Slides` module), `megaparse 7.4k` (vision `0.87`), `unioffice` Go. Memo `research/FRAMEWORK_AND_MODEL_MEMO.md`.
11. **Framework upgrade** `template_tag.py` (docxtemplater-style `{title}/{bullets}` tag resolution, `_replace_tag_in_shape` preserving run style) + `pptxgen_bridge.py` (PptxGenJS `defineSlideMaster` + `addText`/`addTable`, Node `pptxgenjs` via `subprocess`), `model_bakeoff.py` (xgboost/lightgbm/mlp + GNN/LSTM/TinyTransformer stubs, 5-10M budget). Bakeoff `data/metadata/BAKEOFF_REPORT.json`: `xgboost/rf200 0.469` tie, `lightgbm 0.468`, `hgb 0.442`, `mlp 0.41`, `logreg 0.329` — torch not yet installed (120s timeout), so GNN/LSTM/Transformer pending but code ready (~12k/40k/50k params, <15MB).
12. Wired `/api/tag` `backend/routes_tag.py` (`/health/spec/process` via `TemplateTagPipeline`), `backend/main.py 0.5.0` now 3 pipelines, `research/FRAMEWORK_AND_MODEL_MEMO.md` completed. Restarted backend, verified via `TestClient`: `v02 29/62134`, `v01 29/2017891` (2MB with template images), `tag` returns FileResponse (pptx) 29 slides but 0 tags (template has no `{title}` yet — needs designer to inject tags).

---

## 4. Models — detailed

- **Features:** `graph/builder.py` 9 edge types (`LEFT/RIGHT/TOP/BOTTOM_ALIGNED, NEAREST_H/V, SAME_GROUP, CONTAINS, OVERLAPS` `ALIGN_EPS 0.005 OVERLAP_IOU 0.15`) → `graph/features.py` 14 relational (`neighbor_count, same_type_frac 0.59` etc.) + 35 base + 8 effective =49 `FEATURE_SCHEMA.json`.
- **Datasets:** `data/processed/node_dataset_v2.jsonl` 7888 rows, `intent 74` groups, `slide_type 422/30 decks`. Grouped split `train 0-5 val 6-7 test 8-9`, 0 leakage.
- **Baselines:** `data/metadata/ML_BENCHMARKS.json` intent RF `CV 0.609 test 0.60 MIXED 0.0 PRESERVE 0.8 REBUILD 1.0` NOT_PROMOTED; node RF `CV 0.477 pooled 0.426 ADD 0.749 MOVE 0.008 UNCHANGED 0.849` NOT_PROMOTED; `V2` RF `CV 0.484 MOVE 0.073` lift; `MODEL_CARD.json` HGB vs RF `MOVE 0.095 vs 0.008`; `SLIDE_TYPE` `hist_gbdt 0.506`.
- **Slide classifier** `models/slide_type_classifier.joblib 0.78MB` maps PDR `TITLE_SLIDE→TITLE` etc.

---

## 5. How We Do It Now (which pipeline to use)

- **Brand fidelity (shapes/arrows/bg images 100%):** `POST /api/tag/process` (once template has `{title}` tags) or `POST /api/v01/process` (`TemplateStyledPipeline` keeps raw shapes, 2MB preserves images) — use for `TestPPT` now.
- **Restructured (new geometry):** `POST /api/v02/process` (`ContentModel→MockLLM/heuristic→BrandRenderer` dark `001F33`, 2-col bullets, 62KB minimal) — irrelevant before fix, now preserves all 29 titles/bullets but loses original shapes by design.
- **JS edge:** `pptxgen_bridge.render_via_pptxgen(deck_spec, out)` for Vercel (needs `node` + `pptxgenjs` in `ui/node_modules`).

---

## 6. How to Run & Test

```bash
# backend
.\backend\venv\Scripts\python.exe backend/main.py  # :8000, logs backend.log
# frontend
cd ui; npm run dev  # :5173, VITE_API_URL env or defaults to http://localhost:8000
# CLI
$env:PYTHONPATH="C:\Users\Akshay.JOHN-XAVIER\.gemini\antigravity-ide\scratch\BrandMorph"
.\backend\venv\Scripts\python.exe -m morphlite "C:\...\TestPPT.pptx" --no-llm -o out.pptx
# tag pipeline
python -c "from morphlite.pipeline.template_tag import TemplateTagPipeline; TemplateTagPipeline('data/brand_template/Brand_guideline_Akkodis.pptx').process('raw.pptx','out.pptx')"
# bakeoff (needs torch for GNN/LSTM)
.\backend\venv\Scripts\python.exe morphlite/training/model_bakeoff.py  # → data/metadata/BAKEOFF_REPORT.json
```

**TestPPT expectation:** `v02` → 29 slides `Automotive ADAS…` etc., 62KB; `v01` → 29 slides `2017891` bytes with template images; `tag` → 29 slides but currently irrelevant (0 tags → template text) until tags added.

---

## 7. Next for 3 Paths (what’s left)

- **Path1 hard-coded:** inject `{title}/{subtitle}/{bullets}` tags into template copy via script, update `ui` toggle to include `tag`, verify 29-slide relevance.
- **Path2 model:** `pip install torch --index-url https://download.pytorch.org/whl/cpu` (retry, 300s timeout), run `model_bakeoff.py` → GNN/LSTM/Transformer F1, synthetic 3× `synthetic_augment.py` (23k nodes), promote `HGB+GNN` ensemble `<50MB`.
- **Path3 automation:** implement `Subagent-1 code / Subagent-2 validation (pair_discovery) / Subagent-3 manager (match rate + feedback to 1+2)` as described; current `Task` subagents: Path1 done, Path2 done, Path3 pending cert error — re-spawn with `general` type.

All absolute paths, commit `origin/main`, and logs in `backend.log`/`backend_err.log` for replay.
