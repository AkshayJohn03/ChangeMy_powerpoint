# BrandMorph V2 — Diagnosis & Design

> Status: approved design. The v2 engine implements exactly this. Nothing here is aspirational.

## 1. Root-cause diagnosis (why v1 "can't do it properly")

v1's pipeline is `PPTX → AST → rebuild-from-blank-layout`. That decision causes every failure below.

| # | Defect | Where | Consequence |
|---|--------|-------|-------------|
| D1 | **Rebuild destroys fidelity.** Every slide is recreated from `slide_layouts[6]` (blank) and re-drawn as generic rounded rectangles / textboxes. | `backend/builder.py:22-31` | Original masters, layouts, placeholders, charts, tables, SmartArt, groups, gradients, shadows, images-in-place, speaker notes are silently dropped or flattened. Output looks nothing like a "re-branded" deck — it looks like a different, worse deck. |
| D2 | **Hardcoded brand.** 5 colors + 2 fonts live as class attributes on `BrandTokens`; exactly 4 are overridable via the API (`bgColor, cardBg, titleFont, bodyFont`). GOLD/CYAN/TEXT_WHITE are constants. | `backend/builder.py:6-14`, `backend/main.py:64-72` | "Brand morph" is actually "re-paint in the one dark theme shipped with the repo." A second company's brand cannot be expressed. |
| D3 | **Crude role heuristics.** Title vs body decided by `bbox.top < 1.5 and bbox.height < 1.2`; font size for titles is a constant `Pt(24)` regardless of original size. | `backend/builder.py:86-92` | Misclassified roles cascade: titles styled as body, body as titles, and text overflows because measured sizes are replaced by guesses. |
| D4 | **Data loss is silent.** The decompiler emits `nodes` for shapes/text it understands; everything else vanishes (charts, tables, grouped shapes) with no warning channel. | `backend/decompiler.py` | Users only discover lost content after presenting. |
| D5 | **Environment hardcoding.** `/api/parse_test_ppt` points at a personal OneDrive path; CORS is `*` with credentials. | `backend/main.py:46-56, 15-20` | Breaks on any other machine; insecure by default. |
| D6 | **No brand guideline ingestion at all.** The user's actual input is a brand guideline (PDF/website/YAML). v1 accepts only 4 JSON keys typed into a UI. | entire backend | The product premise — "give it my brand guideline" — is unimplemented. |

**Verdict:** v1 is not a re-branding engine; it is a lossy deck-to-template transcoder with a fixed theme. The fix is not to tune the builder — it is to stop rebuilding.

## 2. V2 architecture: in-place transformation

Core principle (mirrors professional template-inheritance doctrine): **the original deck is the substrate. We transform the formatting layers — theme, explicit formatting, fonts, copy tone — and touch nothing else.** Shape geometry, charts, tables, images, groups, notes, animations stay byte-identical unless a rule explicitly changes them.

```
                ┌────────────────────────────────────────────────────────┐
 brand guideline│  ① BrandProfile ingestion                              │
 (YAML/JSON/    │  YAML/JSON → validated BrandDNA (pydantic)             │
  PDF+LLM opt.) │  palette w/ semantic roles, typography, tone, glossary │
                └───────────────┬────────────────────────────────────────┘
                                │  BrandDNA
 raw deck.pptx ──► ② DeckAnalyzer ──► DeckInventory (JSON report)
                                │
                                ▼
        ┌───────────────────────────────────────────────────────────┐
        │ ③ ThemeTransformer   ④ DirectFormatMapper                 │
        │ rewrite ppt/theme/   explicit srgbClr/font runs →         │
        │ theme1.xml schemes    role-aware nearest-brand mapping    │
        │ (dk1..folHlink,       (ΔE in Lab space, role-preserving)  │
        │ majorFont/minorFont)  fills, lines, text, table cells     │
        └───────────────┬───────────────────────────────────────────┘
                        │
                ⑤ FontRoleMapper (placeholder/size/bold heuristics → DNA fonts)
                ⑥ CopyToneRewriter (optional LLM, length-budgeted, offline no-op)
                ⑦ FitGuard (PIL text metrics, orig_len×1.1 budget, shrink ladder)
                        │
                        ▼
        transformed.pptx + ⑧ MorphReport (JSON+MD: every change, before→after,
                                          confidence, review flags)
                        │
                ⑨ Visual QA (optional): soffice → PNG contact sheet + diff pairs
```

### 2.1 Stage specs

**① BrandProfile ingestion** — `brandmorph/brand/profile.py`
- `BrandDNA` pydantic model: `palette: dict[Role, BrandColor]` where `Role ∈ {background, surface, text_primary, text_muted, accent_primary, accent_secondary, success, warning, danger, link}`; each `BrandColor` has hex + `usage` notes. `typography: {heading: FontSpec(family, weights), body: FontSpec}`, `logo: {primary_path, light_variant_path}`, `tone: {voice, formality 0-1, glossary: dict[str,str], banned_words: list}`, `rules: {min_contrast: 4.5, preserve_all_caps: bool}`.
- Ship `brands/akkodis.yaml` (navy `#030C1E`, surface `#081632`, gold `#FFB81C`, cyan `#00E5FF` — continuity with v1 tokens) and `brands/corporate_light.yaml` (a light theme, proving v1's hardcode was the limit).
- PDF ingestion is **optional + pluggable**: `PDFBrandExtractor` protocol, `LLMPDFExtractor` impl behind an env-guarded import. Never a test dependency.

**② DeckAnalyzer** — `brandmorph/engine/analyzer.py`
- Walk slides, groups (recurse, `shape_type == 6`), tables, chart series, and the XML tree. Record per element: theme refs (`schemeClr`) vs explicit (`srgbClr`), fonts, sizes, placeholder identity, image parts. Output `DeckInventory` — also exposed as `/api/deck/inventory` so the UI can show "what will change."

**③ ThemeTransformer** — `brandmorph/engine/theme.py` (raw OOXML, python-pptx can't reach here)
- Rewrite `ppt/theme/theme1.xml`: `<a:clrScheme>` children (`dk1, lt1, dk2, lt2, accent1..6, hlink, folHlink`) and `<a:fontScheme>` (`majorFont`, `minorFont` latin/ea/cs).
- Mapping from DNA: `dk1→text_primary`, `lt1→background`, `accent1→accent_primary`, `accent2→accent_secondary`, `dk2→surface`, `lt2→surface_alt`, rest of accents → generated shades of `accent_primary` (Lab lightness ladder, hue-true).
- Respect each master's `<p:clrMap>`; write `theme2.xml+` if present. Everything theme-referenced updates with zero shape surgery — this is the pass that makes the result look native.

**④ DirectFormatMapper** — `brandmorph/engine/format_mapper.py` (the hard 60%)
- For every explicit `srgbClr`/`sysClr` in run properties, fill, line, gradient stops, table cells:
  1. **Classify role of the source color** (not the element): luminance+saturation + neighborhood context → one of `background | surface | text | accent | decorative`. A near-white color on a dark slide *is* text; the same hex in a chart bar *is* data ink.
  2. **Map to the DNA color playing the same role**, choosing nearest candidate in CIE Lab (implement `ΔE76` by hand — no scikit dependency). Tie-break by hue affinity.
  3. **Never map** colors that are already within `ΔE < 8` of a DNA color (idempotence), and never touch picture fills or theme refs.
- Output: change log entries `{slide, shape_id, element, before, after, role, deltaE, confidence}`.

**⑤ FontRoleMapper** — `brandmorph/engine/fonts.py`
- Role per text element: placeholder type (`ctrTitle/title/body`) > explicit size (>18pt → heading) > bold-first-paragraph heuristic. Heading font from DNA unless `rules.preserve_display_fonts` flags an element as display lock. Write latin + ea + cs typefaces on runs (python-pptx `font.name` only sets latin — patch `rPr` XML for ea/cs).

**⑥ CopyToneRewriter** — `brandmorph/engine/copy.py` (optional; offline no-op by default)
- LLM rewrites slide copy to brand voice under a **hard length budget of `orig_len × 1.1` chars** (the template-budget rule), glossary term enforcement, numbers/dates/proper nouns frozen (regex whitelist), JSON-mode structured output per text frame. Without `LLM__API_KEY` configured this stage is a documented pass-through — the engine is fully functional without it.

**⑦ FitGuard** — `brandmorph/engine/fit.py`
- PIL ImageFont measurement against shape box (word-wrap simulation at 10% slack). Violations trigger the shrink ladder: tighten spacing → −1 font size step (max 2 steps) → flag `needs_review`. Never widen boxes. Font file resolution: system fonts dir + `assets/fonts/`; if the family is missing, fall back to a metric-compatible estimator (Arial ≈ Helvetica advance widths) and mark the estimate.

**⑧ MorphReport** — JSON + Markdown: counts per stage, full change log, idempotence hash, review flags. The report IS the trust artifact for an enterprise user.

**⑨ Visual QA** — optional `render.py`: detect `soffice` on PATH; if absent, stage is skipped and the report says so (graceful, never fails the run). If present: render before/after PNG pairs, contact sheet into `report/`.

### 2.2 Interfaces (compatibility contract)

- `POST /api/brand/apply` `{deck_b64 | multipart, brand_yaml | brand_name, options{rewrite_copy, dry_run}}` → transformed deck + report. `dry_run` returns only the report.
- `GET  /api/deck/inventory` (multipart) → DeckInventory JSON.
- `POST /api/brand/extract` (multipart PDF) → draft `BrandDNA` YAML for human editing (LLM path only).
- `POST /api/parse_deck` and `POST /api/export_deck` **keep working** (legacy Tauri UI depends on them) but `export_deck` now routes through the v2 in-place engine when `tokens.mode == "inplace"` (new UI can opt in); legacy rebuild path stays available under `mode: "rebuild"` with a deprecation warning in the response.
- CLI: `python -m brandmorph apply --deck deck.pptx --brand brands/akkodis.yaml --out out.pptx [--dry-run] [--report report.md]`

### 2.3 Test strategy (offline, deterministic)

1. **Synthetic fixture decks** built in-test with python-pptx: (a) theme-referenced deck, (b) hard-coded-colors deck, (c) mixed deck with a chart + table + grouped shapes (loss sentinels), (d) overflow-prone long-title deck.
2. Theme test: after apply, `theme1.xml` contains DNA hexes; scheme-referenced shapes inherit.
3. Mapping test: red `FF0000` explicit run → nearest warm DNA accent; `FFFFFF` on dark slide → `text_primary`; no change when applying the brand twice (idempotence).
4. Fidelity test: shape/table/chart counts identical pre/post; image part hashes unchanged.
5. FitGuard test: long title flagged, shrink ladder applied within 2 steps.
6. API test: legacy endpoints still 200 on a fixture deck (UI contract).

### 2.4 Non-goals (explicit)

Image recoloring, animation edits, perfect gradient extraction (flagged for review instead), PDF guideline parsing without an LLM key (draft-from-YAML only), and layout redesign (that's the studio's job, not the morph engine's).
