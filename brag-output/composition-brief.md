# Hyperframes Composition Brief: BrandMorph — whiteboard lecture

## Objective
Create a long-form whiteboard explainer lecture (NOT a launch video) for
BrandMorph, following TUTOR_BRIEF's --tone paragraph and section 8 outline.

## Output
- Composition directory: `brag-output/composition/`
- Rendered video: `brag-output/brag.mp4`
- Format: landscape — 1920x1080
- Duration: ~360–400 seconds (11 scenes; scene durations = measured narration WAV durations + padding)

## Source Material
- Project root: `D:\aria\Projects\BrandMorph`
- Primary files read: `README.md`, `docs/V2_DESIGN.md`, `TUTOR_BRIEF.md` (§8),
  `backend/brands/akkodis.yaml`, `backend/brandmorph/engine/*.py`, `backend/examples/report/morph_report.md`
- Product name: BrandMorph
- Tagline / strongest claim: "the robot that re-skins PowerPoint decks — in place, with a receipt"
- Key visuals to recreate: paint tin vs hand-painted walls; RGB-vs-Lab comparison (navy #030C1E vs black #000000); role arrows (red text → brand danger color); shrink ladder; change-log receipt rows; zip-bomb ratio gauge; stat wall (43 tests, 65 changes: 18/29/18)
- Copy that must appear verbatim:
  - "40 decks" / "the 3am chart with the old blue"
  - "rebuilding is the bug" / "the original deck is the substrate"
  - "navy #030C1E vs black #000000" / "ΔE"
  - "red text stays text" / "ΔE < 8" / "run it twice — nothing changes"
  - "65 audited changes · 18 color remaps · 29 font roles · 18 theme slots"
  - "43 tests"

## Creative Direction
- Tone preset: polished, delivered as a lecture
- Creative direction: patient senior engineer at a whiteboard teaching one system to a smart junior; every keyword defined on screen in one plain sentence at first use (kcard rail, like sibling episodes); long-form pacing; zero hype
- Angle: the repo's own story arc — v1 rebuilt decks and destroyed them; v2 transforms in place
- Hook: the rebrand memo and the number 40 (decks)
- Outro / punchline: recap ending "now you can explain it to someone else"
- Avoid:
  - Generic SaaS language, hype adjectives, launch energy
  - Abstract filler visuals
  - Flashing text; every readable line holds long enough (0.3s/word floor)

## Visual Identity
- Background: #081632 with #030C1E depth (the deck is painted in BrandMorph's own applied brand)
- Text: #F2F6FC primary, #93A5C4 muted (both pass WCAG AA on the navy)
- Accent: #FFB81C gold, #00E5FF cyan; dark chip text #241A06 on gold, #062028 on cyan
- Display font: Ink Free (assets/fonts/Inkfree.ttf), body: system-ui
- Visual references from the project: brand YAML roles, morph report change-log table, theme clrScheme slot names (dk1/lt1/accent1–6)

## Storyboard
Use the storyboard in `brag-output/brag-plan.md` as the creative contract.
11 scenes, each with a left "main" whiteboard area and a right rail of 2–5
kcards defining keywords (term + one plain sentence). Scene-tag bottom-left.

1. The rebrand memo — ~38s — memo card, "40 decks" counter, missed 3am chart; kcards: PPTX, rebrand
2. V1's fatal flaw — ~42s — before/after: rich deck (chart+table+groups) → flattened boxes; kcards: rebuild-vs-inplace, fidelity sentinel, slide master/layout
3. Paint tin & hand-painted walls — ~46s — theme tin with 12 clrScheme slots + arrows from shapes; hand-painted hex chips; kcards: OOXML/ZIP archive, theme, clrScheme, srgbClr, python-pptx/lxml
4. Lab color distance — ~44s — two swatches navy/black: RGB far apart, eyes identical; ΔE number; kcards: RGB, CIE Lab, Delta-E (dE76), perceptual color distance
5. Role-preserving mapping — ~40s — role arrows red text→danger color, white bg→brand bg; kcards: role-preserving mapping, role classification, schemeClr/srgbClr distinction, change log
6. Fit guard — ~40s — text box, wrapped lines, shrink ladder steps −1pt ×2, then review flag; bleed ruler; kcards: PIL font metrics, word-wrap simulation, shrink ladder, horizontal bleed/wrap-off
7. Idempotence — ~30s — run twice diagram, second pass 0 changes; kcards: idempotence, ΔE<8 band
8. The receipt — ~34s — real change-log rows from morph_report.md; dry-run badge; kcards: morph report, review flag, dry run
9. Hostile decks — ~42s — 40KB → petabytes gauge, slip path, entity tree; kcards: zip bomb, compression ratio, zip-slip, XML entity bomb, upload cap/batch processing
10. The numbers — ~36s — stat wall: 43 tests, 65 audited changes (18/29/18), fidelity preserved; kcards: fidelity test, fixture deck
11. Recap — ~40s — 6 numbered recap rows, end line; kcard: "now explain it to someone else — GLOSSARY.md"

## Audio
- Audio role: quiet steady bed under narration (lecture)
- Audio arc: constant low bed; sparse soft SFX at the biggest landings only
- Music: `assets/music/happy-beats-business-moves-vol-12-by-ende-dot-app.mp3` (looped back-to-back per scene math)
- Music treatment: data-volume 0.13 on all loops; no ducking needed (no competing audio)
- Music cue guidance: bed only — narration owns pacing; no beat-locking (lecture)
- Audio-reactive treatment: none
- Audio-coupled moments:
  - Scene 3 paint tin landing — soft interface drop
  - Scene 10 stat wall — soft impact
- SFX selection guidance: use skill sfx-analysis.md; low high-frequency-risk, sparse (4 cues total)
- Exact SFX choice: Hyperframes chooses filenames/timestamps after animation exists (siblings used interface/drop_001.ogg and impact/impactSoft_medium_*.ogg — copy from skill assets)
- Audio files: copy music into `composition/assets/music/`, SFX into `composition/assets/sfx/`, narration WAVs (Kokoro af_heart, per scene) into `composition/assets/voiceover/`
- Narration: `data-track-index` per scene, volume 1, start = scene start + 0.35s; scene `data-duration` = narration duration + padding

## Hyperframes Instructions
Requirements:
- Single-file composition `index.html` following the proven sibling pattern
  (HVAC-Copilot/Model-Distillery): `#root[data-composition-id]`, scenes as
  `<section class="clip" data-start data-duration>`, GSAP timeline registered as
  `window.__timelines["brandmorph-lecture"]`, all animation on inner wrappers — never on `.clip` elements.
- Narration ON (TUTOR_BRIEF): one WAV per scene, scene timings derived from ffprobe durations.
- Every keyword defined on screen at first use (kcard rail).
- Show real project material: the actual change-log rows, actual hexes, actual counts.
- All text readable; WCAG AA contrast on every element (sibling bar: 77–105/105, gate is 0 errors).
- Keep total duration within 4–7 minutes.
- Run `npx hyperframes check` before render — it is brag's single gate; fix ALL layout and contrast errors.
- Render with `--quality delivery`.
