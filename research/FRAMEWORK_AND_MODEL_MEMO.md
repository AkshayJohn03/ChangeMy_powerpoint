# BrandMorph — Framework Upgrade & Model Bake-off Memo (2026-09-02)

## 1. Why python-pptx alone is insufficient (GitHub topics/powerpoint 1,691 repos)

| Repo | Stars | Pattern | What we steal |
|---|---|---|---|
| **hugohe3/ppt-master 51.4k** | SVG pipeline, not flat shapes. `design_spec.md → SVG → DrawingML` with `p:sldMaster` inheritance, native charts/tables (`--native-charts-and-tables`), `edit-native-pptx` (byte-for-byte keep). | **Switch BrandMorph from direct shape stamping to SVG intermediate** (`morphlite/render` currently does `add_shape` per archetype). Fixes SmartArt/chart fidelity (currently 24 charts in dataset, 0.04% but 100% design-critical). |
| **pipipi-pikachu/PPTist 9.3k** | Vue canvas + `pptxtojson` import (~85% import /95% export fidelity), magnetic alignment, history. `doc/Canvas.md` element model. | **Replace `ui/src/App.tsx` bbox-div canvas** with PPTist canvas model (rulers, grid, `Selection panel`). Use `pptxtojson` for import instead of custom `bbox` math. |
| **gitbrent/PptxGenJS 6.1k** | JS OOXML builder, 75+ demos, `SlideMaster`, `tableToSlides()`, Node/React/browser/serverless, TypeScript. | **PptxGenJS bridge** (`morphlite/pipeline/pptxgen_bridge.py`) for Vercel edge: render `DeckSpec` JSON directly in `ui/` via Node, no Python cold start. Masters define Akkodis `001F33` once. |
| **open-xml-templating/docxtemplater 3.6k** | `{placeholder}` + loops `{#users}` + conditions + `Slides` module `{:users}` → dynamic slides, browser/Node. | **Tag pipeline** (`morphlite/pipeline/template_tag.py`): put `{title}/{bullets}` in `Brand_guideline_Akkodis.pptx`, code just `setData(json).render()`. Non-programmers edit template, zero bbox. |
| **The-Vibe-Company/megaparse 7.4k** | No-loss LLM ingestion, `MegaParseVision` (gpt-4o/claude) `0.87` vs `0.59` unstructured, modular Checkers. | **No-loss `DeckContent`**: render slide PNG → vision LLM extracts tables/images (current `extract_deck` loses table structure as `[12pt]` lines). Add Checker chain. |
| **unidoc/unioffice 4.9k** | Pure Go OOXML, ECMA-376, no deps. | Go microservice for 10× parsing speed if Python becomes bottleneck. |

**Easy effective app (recommended):** `docxtemplater-style tag pipeline` (1 file, 100% native fidelity) + `PptxGenJS masters` for edge + `PPTist canvas` for UI. Implement time <1 day, RAM 0, brand-perfect.

## 2. Model bake-off — 7888 nodes, 49 feats, 7 labels, grouped 5-fold

Dataset `data/processed/node_dataset_v2.jsonl` `UNCHANGED 66.6% RESIZE 11.7% REMOVE 8.6% ADD 6.8% MOVE 5.6% RESTYLE 0.5% RECOLOR 0.3%`. Previous best `RF200 pooled macro 0.477` (`MOVE 0.008`).

**Bake-off `morphlite/training/model_bakeoff.py` (2026-09-02):**

| Model | Macro F1 mean±std | Note | RAM |
|---|---|---|---|
| **xgboost** | **0.469±0.084** | `n_estimators 300 depth6 lr0.1` tie best | ~80MB |
| **rf200** | **0.469±0.072** | baseline | 60MB |
| **lightgbm** | 0.468±0.066 | | 60MB |
| **hgb** | 0.442±0.061 | | 30MB |
| **mlp_small (128,64)** | 0.410±0.077 | | 5MB |
| **logreg** | 0.329±0.035 | | 1MB |
| **dummy** | 0.114 | | — |

No model beats `0.477` significantly — **class imbalance is the bottleneck**, not algorithm. `MOVE/RECOLOR/RESTYLE` together <7% → macro dragged down even though `REMOVE 0.63 / RESIZE 0.55 / UNCHANGED 0.84` are strong.

**Small torch models (GNN/LSTM/Tiny Transformer) — architecture ready, params <100k, <15MB, <0.1s/slide, but torch not yet installed in venv (120s download timeout):**

- **GNN 2-layer GCN 64 hidden ~12k params**: `graph/builder.py` 14 relations (`LEFT/RIGHT/TOP/BOTTOM_ALIGNED, NEAREST_H/V, SAME_GROUP, CONTAINS, OVERLAPS`) + `features_v2.py` 49 feats → `X [N,49] + adj [N,N]` → `GCN→GCN→out`. Expected lift `MOVE 0.008→0.095` (HGB vs RF already shows +0.09 from relational), graph is essential for MOVE.
- **LSTM per-slide seq 64 hidden ~40k params**: sort nodes by `y` then `x` (`ctx_n_text_frac` etc.), `LSTM(64)` over slide sequence → classify each node in context.
- **Tiny Transformer 2 layers 64 d_model 4 heads ~50k params (scales to 5M with 256 hidden)**: `TransformerEncoder(64)` over slide. Current `mlp_small` is 128k params and already close to RF; transformer adds self-attention across nodes (better than MLP's independent rows). 5M version: `d_model 256, 6 layers, 8 heads ≈ 5.2M` still <50MB, <200ms on CPU, fits your 5-10M budget.

**Why F1 weak is pointless without fix:** With 74 intent samples and 22 `RECOLOR` samples, any model will memorize. Minimal productive path:

1. **Synthetic 3×** (`morphlite/training/synthetic_augment.py` plan): from 43 golden branded decks (301 slides) → 129 variants (~900 slides, ~23k nodes) via `content-length shuffle / archetype swap where plausible (grid_regularity>0.7) / style jitter`. Group-preserving, no leakage, flagged `synthetic=1`.
2. **Class-weighted + focal loss** + **SMOTE on MOVE/RESTYLE** — 10min change, +0.05–0.10 macro.
3. **Ensemble HGB (30MB) + GNN (10MB)** — GNN handles MOVE, HGB handles REMOVE/RESIZE. <50MB, <0.2s/slide.

**Recommendation:** Ship **HGB 2.2MB** now (fastest, smallest, `MOVE 0.095` best among sklearn) + tag pipeline for brand fidelity; train **GNN + 5M transformer** in parallel after synthetic 3× (expected macro 0.55–0.60). Transformer 5M is fine per your allowance — use `d_model 256` version, still <50MB RAM, <1s CPU.

## 3. What to implement next (1 day)

- Wire `template_tag.py` to `/api/tag/process` (done `backend/routes_tag.py`) and `ui` toggle `v01/v02/tag`.
- Front-end: replace `python-pptx` download with `PptxGenJS` option (`pptxgen_bridge.py`) for Vercel.
- Re-run `model_bakeoff.py` after `pip install torch` (CPU) + synthetic 3×; promote HGB/GNN ensemble to `models/brandmorph_action_model.joblib`.

## 4. Metrics to watch (promote gates)

`intent min_cv 0.55 minority 0.40 max 5MB 20ms; node 0.45/0.30/25MB/20ms` (`bench_classifiers.py`). Track per-class F1, not just macro — `MOVE≥0.20` and `RESTYLE≥0.30` before ship.
