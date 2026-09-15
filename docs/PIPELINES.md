# Pipelines

## v01 — TemplateStyled (fidelity)

Module: `morphlite/pipeline/template_styled.py`, `brand_profile.py`.

Opens the raw deck, preserves every shape/arrow/image, and applies the brand
system: master background swap per slide role, brand typography tiers,
brand fills for cards/containers, gold line colors, logo application,
contrast validation, integrity verification (before/after hash).

Use when the deck has custom diagrams, flows or arrows that must survive
byte-for-byte structurally.

## v02 — Intelligent restructure

Modules: `models/content_model.py`, `llm/spec_builder.py`,
`llm/provider.py`, `render/renderer.py`, `render/fit.py`,
`pipeline/integrated_v2.py`, `inference/`.

1. `extract_deck` — GROUP recursion, connector/line skip, splash detection,
   visual-order sort.
2. `SpecBuilder` — ContentModel -> DeckSpec (12 archetypes: title, bullets,
   two/three-column, cards, metrics hero, process flow, …). LLM providers
   (Azure/OpenAI, allowlisted endpoints) or offline heuristic/Mock fallback.
3. `BrandRenderer` — deterministic archetype renderers on dark `001F33`
   with two-column bullet splitting and shrink-to-fit.
4. ML gating (optional) — node action model + policy engine + per-slide
   REMOVE budget from `inference/`.

Use for dense text/bullet slides that need modern card restructuring.
Output is intentionally new geometry (smaller files, uniform system).

## tag — Docxtemplater-style master fill

Modules: `pipeline/template_tag.py`, `pipeline/tag_injector.py`.

Placeholders (`{title}`, `{subtitle}`, `{#bullets}`, `{card_1_title}`,
`{card_1_body}`, …) are injected into a *copy* of the brand master template;
at runtime the pipeline resolves tags from raw content while preserving run
styling. Requires a tag-injected template copy — a static master with no
tags returns slides unchanged.

Use for executive decks requiring 100% pixel-perfect master layout.

## TemplateFiller / template-driven (v0.3 line)

Modules: `pipeline/template_filler.py`, `pipeline/template_driven.py`.

Duplicates brand-template slides per raw-slide mapping (slide-type
classifier, HistGBDT) and replaces text inside existing shapes, preserving
all template styling, borders and transparency.

## Edge rendering bridge

Module: `pipeline/pptxgen_bridge.py` — renders `DeckSpec` JSON through
PptxGenJS (`defineSlideMaster` + `addText`/`addTable`) via Node subprocess,
so Vercel/edge targets can render without a Python cold start.
