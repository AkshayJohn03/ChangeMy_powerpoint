# BrandMorph GLOSSARY.md — every keyword in this repo, in plain English

> Study companion to the whiteboard explainer video (`brag-output/brag.mp4`).
> Every term the engine and the video use, defined in one to three plain
> sentences, grouped by theme, each with a "why it matters here" note.

---

## 1. PowerPoint & OOXML — what a deck actually is

**PPTX**
A PowerPoint file. Despite the single-file look, it is a folder of XML parts and media zipped together and given a `.pptx` extension.
*Why it matters here: BrandMorph never "opens a document" the way PowerPoint does — it operates on the parts inside the package.*

**OOXML**
Office Open XML — the Microsoft spec that defines what those XML parts contain: slides, themes, relationships, everything. Every visual feature of a deck is text in an XML file somewhere.
*Why it matters here: theme surgery (stage ③) edits `ppt/theme/theme1.xml` directly, because python-pptx cannot reach that layer.*

**ZIP archive**
The container format holding a PPTX: compressed entries, each with a name (path), a compressed size, and an uncompressed size. Also the attack surface for hostile decks.
*Why it matters here: the safety layer reads those sizes before extraction to stop zip bombs, and checks entry paths to stop zip-slip.*

**Theme**
The deck-wide "paint tin": one named set of colors and fonts that many shapes point at by reference instead of carrying their own copy.
*Why it matters here: repainting the tin (the theme) re-skins every referencing shape at once — the pass that makes a morph look native.*

**clrScheme**
The color scheme element inside `theme1.xml`, with twelve named slots: `dk1, lt1, dk2, lt2, accent1–6, hlink, folHlink`.
*Why it matters here: stage ③ rewrites these slots from the brand DNA — `dk1→text_primary`, `lt1→background`, `accent1→accent_primary` — so theme-referenced shapes update with zero shape surgery.*

**fontScheme**
The font scheme element inside the theme, holding `majorFont` (headings) and `minorFont` (body), each with three typeface slots: `latin`, `ea`, `cs`.
*Why it matters here: the ThemeTransformer rewrites it so every theme-referenced font in the deck switches to the brand fonts.*

**schemeClr**
A color reference in OOXML that says "use theme slot `accent2`" rather than naming a color. The pointer, not the paint.
*Why it matters here: DeckAnalyzer records which colors are theme references; those inherit from the repainted theme and are never touched individually.*

**srgbClr**
An explicit color literal in OOXML — a hand-picked hex like `1F4E79` written directly on a shape, run, fill, or line.
*Why it matters here: these ignore the theme, so stage ④ (DirectFormatMapper) finds each one, classifies its role, and remaps it in Lab space.*

**sysClr**
A system color reference (e.g. "window text") that resolves at display time. Treated like an explicit color when mapping.
*Why it matters here: the format mapper handles `sysClr` alongside `srgbClr`, or hand-painted colors would leak through.*

**clrMap**
The per-master mapping table that renames theme slots (`dk1` acts as "background" on dark masters, for instance).
*Why it matters here: the ThemeTransformer respects each master's clrMap instead of assuming, so dark and light masters both come out right.*

**Slide master**
The template slide that defines inherited formatting for a family of layouts — including its own theme reference and clrMap.
*Why it matters here: v1 threw masters away on rebuild; v2 keeps them byte-identical and only rewrites the theme parts they point to.*

**Layout**
A named arrangement (title slide, section header…) derived from a master, which slides inherit from. Sits between master and slide.
*Why it matters here: fidelity tests prove every layout survives a morph untouched — v1 replaced them all with "blank".*

**Placeholder**
A reserved text box on a layout or slide with a role: `title`, `ctrTitle`, `body`. PowerPoint's own "what is this text for?" label.
*Why it matters here: FontRoleMapper reads placeholder identity first — the most reliable signal of whether text is a heading or body copy.*

**python-pptx**
The Python library BrandMorph uses to read and edit decks: shapes, runs, tables, charts, placeholders.
*Why it matters here: the whole engine is python-pptx at heart — except the theme, which sits below its abstraction and needs raw XML.*

**lxml**
The fast XML parsing library used for raw OOXML surgery.
*Why it matters here: safety.py configures a hardened lxml parser that refuses entity expansion — the defense against billion-laughs bombs.*

**rebuild-vs-inplace**
The architectural fork this repo exists to document. *Rebuild*: decompile a deck, throw it away, redraw every slide from blank layouts (v1) — charts, tables, groups, masters die silently. *In-place*: keep the original file as the substrate and transform only the formatting layers (v2).
*Why it matters here: v2's entire design — "the deck is the substrate" — is the fix for v1's destroyed fidelity.*

**pydantic**
The validation library behind `BrandDNA`: a brand profile that fails loudly if a hex is malformed or a role is missing, instead of failing quietly mid-morph.
*Why it matters here: a bad brand file should be rejected at the door, not three stages into a transformation.*

**DeckAnalyzer / DeckInventory**
Stage ②: walk every slide, group, table, chart and XML tree, recording theme refs vs explicit colors, fonts, sizes and placeholders. The output is the DeckInventory — a JSON report of "what will change".
*Why it matters here: the engine never edits blind; it inventories first, and the UI can show the inventory before anything is applied.*

---

## 2. Color science — measuring color the way eyes do

**RGB**
The way screens store color: red, green and blue light amounts, 0–255 each. Computers compare RGB easily, but equal RGB steps don't *look* equally different.
*Why it matters here: it's the storage format — and the trap. Distances in RGB don't match human perception.*

**HSL (HLS)**
Hue, saturation, lightness — the same color in a more human-shaped coordinate system. BrandMorph uses it to classify roles (a very light color is probably a background; a very dark, saturated one is probably text).
*Why it matters here: role classification starts with luminance and saturation, both read from HLS.*

**CIE Lab**
A color space designed so that a distance of 1 means the same perceived difference anywhere in the space — built around how human vision actually works. `L` is lightness, `a` green↔red, `b` blue↔yellow.
*Why it matters here: all "nearest brand color" decisions happen in Lab, not RGB, so the mapping matches what a designer would see.*

**Delta-E (dE76)**
The distance between two Lab colors — one number for "how different do these look?". dE76 is the original 1976 formula: straight-line Euclidean distance in Lab. BrandMorph implements it by hand (no scikit dependency).
*Why it matters here: every change log entry carries its dE76 value, and the idempotence band is defined in dE units.*

**Perceptual color distance**
Any distance measure that agrees with human eyes rather than with storage. Dark navy `#030C1E` and black `#000000` are far apart in RGB but nearly identical to the eye.
*Why it matters here: it's the difference between a rebrand that looks designed and one that looks like a spreadsheet did it.*

**Role-preserving mapping**
The rule that a color is mapped to the brand color playing the same *role*: a red heading maps to the brand's danger color, a light background to the brand's background — never across roles, even if another brand color is numerically closer.
*Why it matters here: "red text stays text" is what keeps a morphed deck readable instead of technically-nearest nonsense.*

**Role classification**
Before mapping, each source color is classified — background, surface, text, accent, or decorative — from luminance, saturation, and neighborhood context (a near-white color on a dark slide *is* text; the same hex in a chart bar *is* data ink).
*Why it matters here: mapping is only as good as the role guess; the change log records the chosen role for every edit.*

**Idempotence**
Running the same brand twice changes nothing the second time. Property, not luck: colors already within the band of a brand color are recognized as on-brand and left alone.
*Why it matters here: an idempotent tool is safe to re-run, safe to schedule, and safe to trust — and there's a test that proves it.*

**ΔE < 8 band**
The "already on-brand" tolerance. A source color within dE76 distance 8 of a brand color is considered the same color and never remapped.
*Why it matters here: without the band, every run would nudge colors microscopically — destroying idempotence and bloating the change log.*

**Tone ladder / shades**
Generated shades of an accent color: the same hue at descending lightness steps, built in Lab so the hue stays true.
*Why it matters here: the DNA defines a handful of accents, but the theme has twelve slots — extra slots are filled from the ladder so the theme stays coherent.*

**Hue affinity**
Tie-breaking between equally-distant brand colors by preferring the one with the closer hue. Warm stays warm.
*Why it matters here: it's the difference between red text becoming brand-red versus brand-cyan when distances tie.*

**Fidelity sentinel**
A test trick: plant a chart, a table, a grouped shape and a picture in a fixture deck, then assert their counts — and the image bytes (hashes) — are identical after a morph.
*Why it matters here: it's the automated proof that v2 never destroys what v1 destroyed.*

---

## 3. Fonts & layout — text that fits after the swap

**Font role detection**
Deciding, per text element, whether it's a heading or body: placeholder type first, then explicit size (>18pt → heading), then a bold-first-paragraph heuristic.
*Why it matters here: v1 guessed from bounding boxes and got it wrong; v2 uses PowerPoint's own signals first.*

**latin / ea / cs typefaces**
The three font slots OOXML carries per run: latin (Western text), `ea` (East Asian), `cs` (complex scripts like Arabic). python-pptx's `font.name` only sets the latin slot.
*Why it matters here: FontRoleMapper patches the run's `rPr` XML directly so all three slots get the brand font.*

**CJK**
Chinese, Japanese, Korean — the East Asian scripts covered by the `ea` typeface slot.
*Why it matters here: a rebrand that only swaps latin fonts leaves every CJK deck half-morphed.*

**PIL font metrics**
Real text measurement using Pillow's ImageFont: the actual pixel width of a string in a specific font file at a specific size.
*Why it matters here: the fit guard measures with true font metrics, not the rough averages a guess would use.*

**Word-wrap simulation**
Replaying how PowerPoint will wrap a text box's words at its given width, counting the lines that result and the height they need.
*Why it matters here: "does the new text fit?" is answered by simulation before the file is ever opened in PowerPoint.*

**Fit guard**
Stage ⑦: measure every text frame against its box (at 10% slack) and act before anything spills.
*Why it matters here: re-branding with a wider font is exactly when text starts escaping its box.*

**Shrink ladder**
The fit guard's escalation: tighten spacing → reduce font size 1pt per step (max 2 steps) → give up and flag for review. Never widen the box.
*Why it matters here: small problems fix themselves; unfixable ones are escalated honestly instead of silently broken.*

**Horizontal bleed**
Text wider than the slide — the failure mode of a text box with word wrap turned off, which can overflow to the right no matter its font size.
*Why it matters here: the fit guard measures it and flags it (the demo deck ships with a caught example), because no shrink can fix geometry.*

**Wrap-off text box**
A text box with word wrap disabled — one long line that grows sideways.
*Why it matters here: the demo report flags exactly this: "~768pt wide but only ~240pt of slide width remains".*

**needs_review flag**
The report's honest "a human should look at this" marker — for overflow the shrink ladder couldn't solve, or gradients flagged instead of guessed.
*Why it matters here: an enterprise tool that never admits uncertainty is lying; the flag is where honesty lives.*

**preserve_display_fonts**
A brand rule that locks specific elements' fonts (a logo wordmark, a display face) so the morph never touches them.
*Why it matters here: some fonts *are* the brand — the escape hatch keeps them that way.*

---

## 4. Copy & safety — the words and the hostile files

**Brand DNA**
The validated brand profile (`BrandDNA` pydantic model): palette with semantic roles, heading/body typography, logo paths, tone of voice, glossary, banned words, and rules like minimum contrast.
*Why it matters here: it's the single source of truth every stage reads — and the thing v1's four hardcoded JSON keys could never express.*

**YAML profile**
A brand recipe written as human-editable YAML (see `brands/akkodis.yaml`): colors with usage notes, fonts, voice, glossary.
*Why it matters here: a designer can read and edit it without touching code — the input the product premise always promised.*

**Glossary enforcement**
The copy pass that rewrites disallowed terms to preferred ones — "utilise" → "use", "leverage" → "use" — case-insensitively, across all slide text.
*Why it matters here: brand voice is words as much as colors; this pass makes terminology a rule, not a wish.*

**Banned words**
Words the brand never uses ("cheap", "hack", "guys"). They are flagged for review — never silently deleted.
*Why it matters here: deleting someone's sentence is worse than surfacing it; the flag keeps humans in charge.*

**Length budget (orig_len × 1.1)**
The hard rule that a rewritten line may be at most 10% longer than the original — the template-budget rule.
*Why it matters here: voice-rewritten copy that no longer fits its box just recreates the overflow problem under a different name.*

**Numbers/dates/proper-noun freezing**
The regex whitelist protecting figures, dates and names from the copy rewriter.
*Why it matters here: "Q3 revenue" becoming prose is how rebranding tools earn lawsuits.*

**Morph report**
The receipt: JSON + Markdown with counts per stage, the full change log, the idempotence hash, and review flags. Stage ⑧.
*Why it matters here: for an enterprise user, the report IS the trust artifact — every change, auditable.*

**Change log**
One row per edit: stage, slide, element, kind, before → after, role, dE, note. Example from the demo deck: `1F4E79 → 030C1E, background, dE 33.4`.
*Why it matters here: "what did you do to my deck?" has a precise answer, row by row.*

**Review flag**
A row in the report's "needs manual review" section — the list of things a human should confirm.
*Why it matters here: it's the boundary between what the robot did and what it refused to do.*

**Dry run**
Run every stage against a throwaway copy and return only the report — a complete *plan* with no output deck.
*Why it matters here: you can preview a brand on your real deck with zero risk, before committing.*

**Zip bomb**
A tiny archive that decompresses to enormous size — a 40 KB file claiming to be petabytes of XML.
*Why it matters here: decks are untrusted input; the safety layer caps total uncompressed size (250 MB default) and rejects the rest.*

**Compression ratio**
Compressed size vs uncompressed size for an archive entry. Anything far above the cap (200× default) is bomb-shaped.
*Why it matters here: the ratio check catches a bomb even when its total size looks plausible.*

**Zip-slip**
An archive whose entry paths escape the extraction directory (`../../somewhere/evil`) to write outside it.
*Why it matters here: entry paths are validated before extraction — extraction can never escape the workspace.*

**XML entity bomb (billion laughs)**
An XML file whose nested entity definitions expand exponentially — a few bytes becoming billions on parse.
*Why it matters here: the hardened lxml parser refuses entity expansion entirely, so the joke never runs.*

**Upload cap**
The maximum accepted upload size (120 MB default), enforced before any bytes are processed.
*Why it matters here: the API's front door matches the safety layer's limits, so a hostile payload dies at the gate.*

**Batch processing**
The CLI applies a whole folder (globs OK) of decks in one command; one hostile or corrupt deck fails alone and the batch continues.
*Why it matters here: "40 decks" is the actual scenario — and one poisoned file must not kill the run.*

**Hardened XML parser**
`SAFE_PARSER`: entity resolution off, network access off, DTD loading off, huge trees off.
*Why it matters here: every parse of untrusted XML goes through it — defense in depth at the format level.*

---

## 5. Testing & delivery — proving it, and showing it

**Fidelity test**
The test family that asserts shape/table/chart/group counts and image part hashes are identical before and after a morph.
*Why it matters here: it's the regression alarm for the "destroy nothing" promise.*

**Fixture deck**
A synthetic deck built in-test with python-pptx: theme-referenced, hard-coded-colors, mixed (with loss sentinels), and overflow-prone variants.
*Why it matters here: tests run offline in seconds against decks engineered to expose each failure mode.*

**LibreOffice render (Visual QA)**
The optional stage ⑨: if `soffice` is on PATH, render before/after PNG pairs and a contact sheet; if not, skip gracefully and say so in the report.
*Why it matters here: eyes are the final QA — and the engine never *fails* because a renderer is missing.*

**FastAPI multipart**
How decks arrive over HTTP: multipart form uploads to `/api/brand/apply` and `/api/deck/inventory`.
*Why it matters here: the browser UI and the desktop app both speak this contract; the upload cap guards it.*

**Idempotence hash**
A fingerprint of the transformed deck recorded in every report — identical across re-runs of the same inputs.
*Why it matters here: it turns "nothing changed" from a claim into a checkable value.*

**43 tests**
The offline suite (`cd backend && python -m pytest tests -q`): theme surgery, role mapping, idempotence, fidelity sentinels, fit-guard ladder, safety rules, API contract, CLI end-to-end.
*Why it matters here: every promise in the video is a test in that suite — measured, not claimed.*

**65 audited changes**
The committed demo deck's morph report: 18 color remaps, 29 font role assignments, 18 theme slots — with fidelity preserved and one wrap-off bleed caught.
*Why it matters here: it's the worked example you can open: `backend/examples/report/morph_report.md`.*

---

*Terms on this list appear in the video the moment they're first used — the video defines them on screen; this file is where they stick.*
