# BrandMorph Deck Engine

Hybrid layout-intelligence engine that converts raw, unformatted PowerPoint decks into brand-compliant decks (Akkodis visual system: dark navy `#001F33`, gold `#FFB81C`, 13.33 x 7.5 in) while preserving content, shapes, diagrams, and images.

- **Backend:** `backend/` — FastAPI decompiler / brand pipelines / native `.pptx` export.
- **Studio:** `brandmorph-studio/` & `ui/` — Modern React + Vite canvas creative tool.
- **Intelligence:** `morphlite/` — slide AST extraction, features, rules, trained classifiers, hybrid planning, evaluation harness.

Backend version: `0.6.0` — pipelines: `v01_template_styled`, `v02_intelligent`, `tag_docxtemplater`, `golden_morph`.

---

## 1. How It Works

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
   |                           the brand master template (pixel-perfect master)
   |
   +-- golden (Golden-Morph) - retrieval + Hungarian alignment + vector icons
   |
Native branded .pptx
```

---

## 2. Repository Layout

```text
.
├── backend/                       # Python FastAPI backend
│   ├── builder.py                 # Native PPTX constructor with contrast resolver
│   ├── decompiler.py              # Shape & image extractor
│   ├── main.py                    # FastAPI application with safe endpoints
│   └── routes_*.py                # API pipeline routers
├── brandmorph-studio/             # Modern web studio interface (React 19 + Vite)
├── ui/                            # Web studio & desktop client
├── morphlite/                     # Layout intelligence, rules, models & tests
├── vercel.json                    # Unified single-domain deployment config
└── requirements.txt               # Serverless Python dependencies
```

---

## 3. Quickstart

### Backend
```bat
.\backend\venv\Scripts\python.exe backend/main.py
```
Serves `http://localhost:8000`.

### Frontend Studio
```bat
cd brandmorph-studio
npm install
npm run dev
```

### Build & Deploy
```bat
Deploy_And_Build.bat
```
Runs test suite and builds frontend studio bundle.
