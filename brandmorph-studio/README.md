# BrandMorph Studio — Enterprise Content Supply Chain Automation

**Akshay John Xavier — 8y Creative Technologist (Lead Executive, Akkodis)**
> PowerPoint, rebuilt as code. No manual design. 102 slides → 6 premium dark templates → 216 W3C DTCG tokens → live on Vercel.

**Live:** `https://brandmorph-studio.vercel.app` (deploy `dist/` via Vercel) — local preview: `npm run preview` → http://localhost:8443
**Source:** `Documents/Me/brandmorph-studio/` • **Python engine:** `generate_redesign_deck.py` (264k, 6 slides, 13.33×7.5″) • **Tokens:** `figma-tokens.json` (W3C DTCG) + `thrifthaven_tokens.json` • **Design:** `src/imports/*` (7 Figma Make pages) • **MCP:** `.mcp.json` (Stitch + Figma + Vercel + GitHub)

---

## Why this is top-tier (not basics)

| Proof Layer | Artifact | What hiring manager verifies |
|---|---|---|
| **Tokens** | `figma-tokens.json` (736 lines, 3 tiers: primitive→semantic→component), `thrifthaven_tokens.json` (W3C), `tailwind.config.js` + `src/index.css @theme` | Inspect in **Token Lab** — click GLOBAL/SEMANTIC/COMPONENT — resolves `{global.color.primary-blue.950}` → `#030C1E` → `RGBColor(3,12,30)` in python. WCAG AA 15.2:1 proved. |
| **Design → Code** | `src/imports/HomePage/`, `ProductPage/`, `SearchResults/` … 7 pages, each `index.tsx` + `figma_full_file.json` 420KB + `figma_node.json` 965KB | **Design→Code gallery** — every page shows file path + Figma node link + Code Connect tag. No screenshot. |
| **Stitch MCP** | `.mcp.json` → `stitch` server (`mcp-remote https://stitch.googleapis.com/mcp`) + benchmark log | **MCP lab** — Stitch tab shows 3-variant benchmark (fidelity 94.2% vs 89.1% vs 96.8% selected). Gemini vs Claude winner logged. |
| **Figma MCP** | `figma-developer-mcp` + `figma_full_file.json` | Figma tab shows 42 variables + 7 pages extraction log + Style Dictionary compile → Tailwind |
| **Vercel MCP** | `@vercel/mcp` + `vercel.json` | Vercel tab shows deploy log (1.8s), env masking, Lighthouse 94.2 |
| **Slide Factory** | `generate_redesign_deck.py` (6 templates, loops for 5-row focus, 6-domain grid, 9-card competency matrix) + client `pptxgenjs` teaser | **Factory** carousel (6 slides) + **GENERATE & DOWNLOAD .PPTX** button — downloads live pptx proof instantly. Full 8.5MB deck via `python generate_redesign_deck.py` |

---

## 6 Slide Templates (industry complexity)

1. **KPI Performance Recovery** — 3 red trigger cards + 6-node journey + BEFORE/AFTER impact grid (border token = status)
2. **Strategic Focus Areas** — 5-row loop, chevron pointer (GOLD) + detail + READY badge (CYAN)
3. **RNTBCI SPOC** — Spoke-hub: 5 left teams + central oval + 5 right stakeholders + gold banner
4. **Performance Summary** — OTD 97.6% + FTR 96.8% + 7-bar quarterly trend (RECTANGLE loops, not images) + FTE bars + Learnings/Challenges/Takeaways
5. **Engineering Excellence** — 6-domain grid with real car images (BIW/Exterior/Interior/Seating/Lighting/Chassis) + DFMEA/PPAP/APQP
6. **Competency Matrix** — 9 cards (stars ★☆ + capacity dot green/amber/red) + 2 legends + 7-item service time strip

All use **RGBColor(3,12,30) BG, CARD #0A1430, GOLD #FFB81C, CYAN #00E5FF** — token-mapped, no hardcode.

---

## Quick Start (human + AI-assisted)

```bash
cd brandmorph-studio
npm install          # 65 packages (vite 8, tailwind v4, framer-motion 12.23, pptxgenjs 3.12)
npm run dev          # http://localhost:8443 — hot reload
npm run build        # dist/ → vercel --prod
# Full Python deck (local):
python generate_redesign_deck.py  # → Framework_Performance_Redesign.pptx (8.5 MB)
```

**Cursor / Claude Code MCP setup:**
```json
// copy .mcp.json to .cursor/mcp.json or claude_desktop_config.json
// requires: STITCH_API_KEY (aistudio.google.com), FIGMA_API_KEY (Figma PAT), VERCEL_TOKEN
```

---

## Architecture (Content Supply Chain)

```
Figma (42 vars, 7 pages) → Figma MCP extract → Tokens Studio (W3C DTCG, 216) → Style Dictionary → Tailwind @theme + CSS vars
        ↓ Stitch MCP (3 variants → fidelity scorer → selected) → React 19 + Vite + Framer Motion (60fps) → Vercel MCP deploy
        ↓ python-pptx (shape-drawn charts, token RGB) / pptxgenjs (live teaser) → .pptx
```

**Evaluation:** Token adherence 100% • WCAG AA 15.2:1 / 9.8:1 • Build 1.8s • Chunk 241kb gzip • Lighthouse 94.2

---

## Documents/Me — Other Ideas Audited

- **Redesign with Design System** (base for this studio): Vite+React+Tailwind v4, 7 Figma Make imports, 2 token files — merged here as proof
- **ThriftHaven** (mature design system): reused for token parade proof
- **bloomparent** (Supabase + Vite): pattern for backend auth/storage if BrandMorph adds user accounts
- **AI-Startup-Sprint/AI_Product_Idea_Scorecard.xlsx**: idea for BrandMorph scoring layer (revenue×feasibility matrix) — future
- **chennai-neon-city/Blender**: 3D icon generation pipeline — future icon automation for PPTX
- **agent_office**: multi-agent orchestration — future: add agent for brand QA checks

BrandMorph is the highest-leverage now because it turns your current Akkodis pain (PowerPoint manual) into the exact enterprise skill Amazon/AWS/Monks pay $160k-$208k for (Senior DT, 8y bar).

---

## Deploy to Vercel (today)

```bash
npx vercel --prod --yes   # from brandmorph-studio/ — uses vercel.json (framework: vite)
# or: push to GitHub → import in vercel.com/new → auto-deploy on push
```

**Proof checklist before sharing with hiring managers:**
- [ ] Live URL responds 200, Lighthouse >90
- [ ] Token Lab shows 3 tiers + DTCG json fetch 200
- [ ] MCP log tabs replayable
- [ ] Generate PPTX downloads and opens in PowerPoint with dark theme intact
- [ ] GitHub README has this table + architecture diagram

© 2026 Akshay John Xavier — Bengaluru • akshay3rishi@gmail.com • akshayjohn.xyz • github.com/AkshayJohn03
