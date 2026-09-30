# Brag Plan: BrandMorph — whiteboard lecture

> TUTOR BRIEF override: this is NOT a launch video. It is a whiteboard explainer
> lecture whose success metric is: "the owner of these repos understands what was
> built and why." Narration on. Calm, precise, friendly. Aim 5+ minutes.

## What is this app?
BrandMorph re-skins PowerPoint decks: you hand it a deck plus a brand recipe
file (YAML), and it returns a re-branded deck — transformed *in place*, never
rebuilt — plus a receipt listing every single change.

## The angle
A patient senior engineer at a whiteboard teaching ONE system to a smart junior.
The story arc is the repo's own diagnosis: **v1 rebuilt decks and destroyed them;
v2 transforms in place.** Every technical keyword is defined on screen in one
plain sentence the moment it first appears. No hype adjectives, no launch energy.

## Hook (first 8 seconds)
The rebrand memo: "New brand. New colors. New fonts." — and the number that
ruins the week: 40 decks. Long-form hook, not a gimmick: the scenario IS the hook.

## Key moments (the middle)
- V1's fatal flaw: rebuilding every slide from blank layouts — the "different, worse deck".
- Theme = paint tin vs hand-painted walls: repaint the tin AND remap every hand-painted hex, in place.
- Colors compared in Lab space: navy `#030C1E` vs black `#000000` — far apart in RGB, identical to eyes.
- Role-preserving mapping: red text stays text (→ danger color), white on a dark slide stays text.
- Fit guard: real PIL font metrics, word-wrap simulation, shrink ladder, wrap-off bleed caught.
- Idempotence: run it twice, the second run changes nothing (ΔE<8 band).
- The morph report: a receipt — 65 audited changes on the committed demo deck.
- Hostile-deck defenses: a deck is a ZIP of XML; zip bombs, zip-slip, billion laughs.

## Outro / punchline
The 30-second recap the viewer could repeat to a colleague, ending on the
success metric: "now explain it to someone else."

## User flow worth showing
Whiteboard lecture — the "flow" shown is the pipeline itself:
deck + brand YAML in → stages (analyze → theme → format → fonts → fit) →
transformed deck + morph report out. Recreated as whiteboard diagrams, plus the
real numbers from `backend/examples/report/morph_report.md` (65 changes:
18 color remaps, 29 font roles, 18 theme slots) and the 43-test suite.

## Tone
- Preset: polished (structure), delivered as a lecture
- Creative direction: TUTOR_BRIEF --tone paragraph merged with TUTOR_BRIEF §8 outline
- Interpretation: long-form pacing, each idea gets the time it needs; every
  keyword defined on screen at first use; calm, precise, friendly; zero hype.

## Format: landscape — 1920x1080
## Duration: ~360–400 seconds (long-form lecture; 4–7 min verify window)

## Visual identity (from the project's own brand DNA — brands/akkodis.yaml)
- Background: #081632 (surface navy) on #030C1E (deep navy) — the deck is literally painted in the brand BrandMorph applies
- Accent: #FFB81C (gold) and #00E5FF (cyan)
- Text: #F2F6FC primary, #93A5C4 muted
- Display font: Ink Free (whiteboard hand), Body: system-ui
- Strongest visual element: the paint-tin/walls analogy, the Lab space plot, the change-log receipt table

## Share copy (draft)
"I made a whiteboard lecture explaining BrandMorph — the engine that re-skins
PowerPoint decks in place: Lab-space color mapping, role-preserving, idempotent,
with a receipt for every change. 43 tests; the demo deck ships 65 audited changes."

## Audio direction
- Role: steady clean music bed under narration, very quiet
- Music: happy-beats-business-moves-vol-12 (bundled, proven with sibling episodes), looped back-to-back
- Music treatment: 0.13 volume throughout; no fades needed at loop points (like siblings)
- Music cue guidance: bed track — narration pacing owns timing; no beat-locking needed for a lecture
- Audio-reactive treatment: none (lecture; restraint rule: audio must never compete with speech)
- SFX posture: sparse — a few soft interface drops where big elements land
- Audio-coupled moments: soft drop when the paint tin lands, soft impact on the "43 tests" stat wall
- Restraint rule: music stays under narration at all times; no beat-grid tricks in a lecture

## Voiceover script
Voice: Kokoro `af_heart`. Numbers written for TTS; exact figures appear on screen.
Scene lengths derive from measured WAV durations (script in narration script below,
generated per scene into `composition/assets/voiceover/voice_NN.wav`).

### Scene 1 — The rebrand memo (~38s)
It starts with a memo from the design team. "We've rebranded. New colors, new
fonts. Please update all materials." Sounds simple — until you count. Forty
PowerPoint decks. Sales decks, pitch decks, training decks. Each one is a dozen
slides of text boxes, charts, and tables, colored by hand by different people
over different years. Doing it by hand means opening every slide and repainting,
for days. And you will still miss the chart someone pasted at three a.m. with
the old blue. This is the problem BrandMorph was built for: a robot that
re-skins decks. In the next few minutes, we'll walk through how it works — and
why the first version of it failed.

### Scene 2 — V1's fatal flaw (~42s)
Version one took an honest swing and missed. Its pipeline was: read the deck,
throw it away, and rebuild every slide from a blank layout, redrawing everything
as generic text boxes. It produced *a* deck. But it wasn't *your* deck. Charts
were gone. Tables were gone. Grouped shapes, images, speaker notes — flattened
or dropped, silently. The output looked like a different, worse deck. The
diagnosis in this repo names it precisely: rebuilding is the bug. So version two
is built on one principle — the original deck is the substrate. We transform the
formatting layers, and touch nothing else. Shape geometry, charts, tables,
images, animations: byte-identical unless a rule explicitly changes them.

### Scene 3 — The paint tin and the hand-painted walls (~46s)
To understand how, you need one fact about PowerPoint files. A PPTX is a ZIP
archive of XML parts — a folder dressed up as a file. And colors hide in two
places. Place one: the theme. Think of it as one paint tin that many shapes
point at by reference. Repaint the tin — rewrite the theme's color scheme,
the clrScheme — and every referencing shape updates at once. Place two: colors
somebody hand-painted — a hex value written directly on a text run or a fill.
Those ignore the tin entirely. Version one only knew how to rebuild walls.
Version two does both jobs: it repaints the tin with raw XML surgery, and then
hunts down every hand-painted color, one by one, and remaps it — in place. The
deck is never dismantled.

### Scene 4 — Measuring color like eyes do (~44s)
Now — how do you decide a hand-painted color should become? "The nearest brand
color" sounds simple, but nearest *where*? Computers store color as RGB — three
numbers. But RGB distance lies. Our brand navy, hex zero-three-zero-C-one-E,
and pure black are far apart as numbers — yet to your eyes, they're nearly
identical. So the engine compares colors in CIE Lab: a color space designed so
that distance matches human perception. The distance measure is Delta-E — one
number for "how different do these look?" The mapping picks the smallest Delta-E
to a brand color, breaking ties by hue — warm stays warm.

### Scene 5 — Role-preserving mapping (~40s)
Distance alone isn't enough. Before mapping, each source color is classified by
role: background, surface, text, accent — judged from its lightness, saturation,
and context. A near-white color on a dark slide is text. The same hex in a chart
bar is data ink. Then the rule: map each color to the brand color playing the
*same role*. Red text maps to the brand's danger color — still text, still red.
A white background maps to the brand's background. Text never becomes a
background, and charts stay charts. That's role-preserving mapping, and every
decision lands in the change log with its role and its Delta-E.

### Scene 6 — The fit guard (~40s)
New fonts are a trap. The brand font may be wider than the old one, and wider
text spills out of its box. So before anything ships, the fit guard measures
every text frame — with real font metrics from actual font files, simulating
how PowerPoint will wrap the words, line by line. If text doesn't fit, a shrink
ladder runs: tighten the spacing, then reduce the font one point at a time, two
steps maximum. If it still doesn't fit, it's flagged for a human. Boxes are
never widened. And there's a sneakier case: a text box with word wrap switched
off can grow sideways forever — the fit guard measures the bleed against the
slide edge and flags that too.

### Scene 7 — Idempotence (~30s)
Here's a property nobody asks for until they need it. Run BrandMorph on a deck,
then run it again, same brand. The second run changes nothing. This is
idempotence, and it's designed in, not lucky: any source color already within
Delta-E eight of a brand color counts as on-brand and is left alone. Without
that band, every run would nudge every color a little — and the tool could
never be safely re-run. There's a test that proves it, and every report carries
a hash that proves it again.

### Scene 8 — The receipt (~34s)
Which brings us to trust. An enterprise tool that says "trust me" gets one
run. So every morph produces a report — a receipt. Every change, row by row:
which slide, which element, before, after, the color's role, the Delta-E
distance, and the confidence. Colors that needed judgment but didn't get it are
flagged for review. And there's a dry-run mode: every stage executes against a
throwaway copy, and you get the complete plan without a single changed file.
The committed demo deck's receipt lists sixty-five audited changes. Open it —
it's in the repo.

### Scene 9 — Hostile decks (~42s)
One more thing, because decks arrive from the outside world. A PPTX is a ZIP of
XML, and both layers can be weaponized. A zip bomb: a forty-kilobyte file that
claims to decompress to petabytes. The safety layer caps the compression ratio
and the total uncompressed size, before extraction. Zip-slip: an archive whose
entry paths escape the working directory — path-checked. And the XML entity
bomb, "billion laughs": nested entity definitions that explode exponentially on
parse. The hardened parser refuses entity expansion entirely. Add an upload cap
and batch processing — where one hostile deck fails alone and the rest of the
batch continues — and the robot can be pointed at the internet safely.

### Scene 10 — The numbers (~36s)
So — measured, not claimed. Forty-three automated tests run offline in seconds:
theme surgery, role mapping, idempotence, fidelity sentinels, the fit ladder,
safety rules, the API contract, the CLI. Fidelity sentinels are the interesting
one: a chart, a table, a grouped shape and a picture are planted in a test deck,
and the tests assert those counts — and even the image bytes — are identical
after a morph. And on the committed demo deck: sixty-five audited changes.
Eighteen color remaps, twenty-nine font roles, eighteen theme slots. Fidelity
preserved. One wrap-off bleed caught and flagged.

### Scene 11 — Recap (~40s)
Thirty-second recap. A deck is a ZIP of XML; colors hide in the theme — the
paint tin — and in hand-painted hexes. Version one rebuilt decks and destroyed
them. Version two transforms in place: repaint the theme, remap every
hand-painted color to the brand color playing the same role, measured in Lab
space with Delta-E. The fit guard keeps text inside its box, shrinking before it
flags. Running it twice changes nothing. Every change lands in the morph report,
the receipt. Hostile decks — zip bombs, entity bombs — are stopped at the door.
Forty-three tests, sixty-five audited changes on the demo deck. That's
BrandMorph — and now you can explain it to someone else.

**Music mood for this video:** steady, clean, corporate-calm
**Audio summary:** one quiet bed track looped under eleven narration scenes;
sparse soft SFX on the biggest landings; music never competes with speech.
