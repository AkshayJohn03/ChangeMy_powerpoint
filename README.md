# BrandMorph Studio

> Enterprise presentation supply chain and brand governance engine.
> Translates OpenXML presentation decks into token-governed design systems.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Tests: 43 passed](https://img.shields.io/badge/Tests-43%20passed-success)](backend/tests)
[![Python: 3.11+](https://img.shields.io/badge/Python-3.11+-blue.svg)](backend)
[![React: 19](https://img.shields.io/badge/React-19-61dafb.svg)](brandmorph-studio)

---

## Problem Solved

Enterprises manage thousands of legacy presentation decks across distributed delivery teams. When organizations rebrand or adopt modern design tokens, manual redesign fails because:

1. Hand painting colors across hundreds of slides takes weeks and creates silent brand drift.
2. Naive converters rebuild decks from scratch, dropping native charts, tables, formulas, and grouped vector shapes.
3. Typography changes cause text box overflow and broken slide geometry.
4. Hostile upload vectors like zip bombs, zip slip paths, and XML entity expansion risk backend server stability.

BrandMorph solves this by transforming presentation decks in place. The original OpenXML package serves as the substrate. Formatting layers, color themes, font hierarchies, and text metrics update deterministically while preserving all structural geometry, charts, tables, and media assets.

---

## 4-Layer Architecture

BrandMorph operates through four decoupled layers.

```
+-------------------------------------------------------------------------+
| Layer 1: Ingestion and Decompilation (OpenXML -> JSON AST)              |
| backend/decompiler.py: Extracts slides, shapes, tables, charts, groups  |
| Recursive GroupShape traversal with parent offset accumulation          |
+-------------------------------------------------------------------------+
                                    |
                                    v
+-------------------------------------------------------------------------+
| Layer 2: Brand Governance (W3C DTCG 2.0.0 Token Specification)          |
| 3-tier token system: Primitive -> Semantic -> Component                 |
| CIE Lab Delta-E perceptual mapping and WCAG AA contrast validation      |
+-------------------------------------------------------------------------+
                                    |
                                    v
+-------------------------------------------------------------------------+
| Layer 3: Interactive Studio (React 19, Tailwind v4, Vite 8)             |
| 880x495 preview canvas with SCALE = 66 coordinate mapping               |
| Real-time element inspection, token swapping, and slide diff review     |
+-------------------------------------------------------------------------+
                                    |
                                    v
+-------------------------------------------------------------------------+
| Layer 4: Dual Compilation Engine                                        |
| 1. Backend python-pptx engine (backend/builder.py) for full fidelity    |
| 2. Client-side pptxgenjs engine for instant zero-server browser export  |
+-------------------------------------------------------------------------+
```

### 1. Ingestion Layer (`backend/decompiler.py`)
- Reads OOXML ZIP packages directly into an in-memory Document Object Model.
- Extracts slide dimensions, layout hierarchies, shapes, tables, and chart series.
- Implements recursive group shape traversal to preserve nested diagram hierarchies with parent coordinate offsets.
- Hardened against security exploits including zip-bomb expansion ratios, directory traversal paths, and XML entity injection.

### 2. Governance Layer (`W3C DTCG 2.0.0`)
- Organizes design tokens into three strict tiers:
  - Primitive tokens: raw color palettes, font families, and base spacing.
  - Semantic tokens: functional roles such as surface, text primary, accent, warning, and danger.
  - Component tokens: specific component specs such as card backgrounds, badges, and button states.
- Applies color mapping using CIE Lab Delta-E distance calculation to match human eye perception rather than raw RGB math.
- Preserves colors that are already on-brand within a Delta-E threshold of 8 to ensure idempotent transformation runs.

### 3. Interactive Studio Layer (`brandmorph-studio/`)
- Built with React 19, Tailwind CSS v4, and Vite 8 with Rolldown code splitting.
- Features a calibrated 880 by 495 preview viewport utilizing SCALE = 66 coordinate projection for pixel-accurate layout rendering.
- Provides real-time token inspection, slide navigation, and live change log streaming.
- Separates heavy runtime libraries into deferred chunks, keeping initial bundle load under 245 KB.

### 4. Dual Compilation Layer
- Server-Side Pipeline (`backend/builder.py`):
  - Uses python-pptx and direct OpenXML theme transformation.
  - Rewrites `ppt/theme/theme1.xml` color schemes and font schemes natively.
  - Applies shape-level formatting, line metrics, and table cell styles.
- Client-Side Pipeline (`pptxgenjs`):
  - Generates immediate standalone sample presentations directly inside the browser.
  - Requires zero network calls or server dependencies for rapid verification.

---

## Repository Structure

```
BrandMorph/
├── api/                           # Vercel serverless entrypoint
│   └── index.py                   # FastAPI serverless handler
├── backend/                       # Core Python engine and APIs
│   ├── brandmorph/                # Modular transformation pipeline
│   │   ├── brand/                 # Brand DNA models and profile parser
│   │   └── engine/                # Theme, format, font, and fit engines
│   ├── brands/                    # Brand recipes (YAML format)
│   │   ├── enterprise_navy.yaml   # Dark navy enterprise brand profile
│   │   └── corporate_light.yaml   # Light corporate brand profile
│   ├── examples/                  # Synthetic demo decks and sample reports
│   ├── samples/                   # Bundled pitch decks for offline demo
│   ├── tests/                     # 43 offline deterministic pytest suites
│   ├── builder.py                 # OOXML slide generation engine
│   ├── decompiler.py              # Recursive shape decompiler
│   └── main.py                    # FastAPI application with safe endpoints
├── brandmorph-studio/             # Modern web studio interface
│   ├── src/                       # React 19 source with canvas and token lab
│   ├── package.json               # Frontend dependencies and scripts
│   └── vite.config.ts             # Vite 8 config with manual chunk splitting
├── ui/                            # Cross-platform desktop Tauri client
├── vercel.json                    # Unified single-domain deployment config
└── requirements.txt               # Serverless Python dependencies
```

---

## Local Setup and Testing

### Prerequisites
- Python 3.11 or newer
- Node.js 20 or newer
- npm 10 or newer

### Backend Setup and Verification

```bash
cd backend
python -m venv .venv
# Activate environment:
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt

# Run complete test suite (43 offline tests)
pytest
```

Expected test result:
```
============================= test session starts =============================
platform win32 -- Python 3.11.9, pytest-9.1.1
collected 43 items

tests/test_api.py ........                                               [ 18%]
tests/test_cli.py ...                                                    [ 25%]
tests/test_colorutil.py ......                                           [ 39%]
tests/test_fidelity.py ....                                              [ 48%]
tests/test_fit.py ...                                                    [ 55%]
tests/test_mapping.py ........                                           [ 74%]
tests/test_safety.py ........                                            [ 93%]
tests/test_theme.py ...                                                  [100%]

============================= 43 passed in 5.75s ==============================
```

### CLI Batch Execution

```bash
cd backend
python -m brandmorph apply --deck examples/demo_raw.pptx --brand enterprise_navy --out examples/demo_branded.pptx --report examples/report
```

### Frontend Studio Build

```bash
cd brandmorph-studio
npm install
npm run build
```

Expected production build output:
```
dist/index.html                             1.29 kB
dist/assets/index.css                      57.52 kB
dist/assets/rolldown-runtime.js             1.29 kB
dist/assets/motion.js                     136.93 kB
dist/assets/index.js                      243.53 kB
dist/assets/pptx-engine.js                374.78 kB
```

---

## Deployment

The project includes root level configuration for Vercel deployment:
- `vercel.json` maps frontend routing to Vite static assets and `/api/*` requests to `api/index.py`.
- Both frontend and backend deploy under one origin, eliminating cross-origin resource sharing complexities.
