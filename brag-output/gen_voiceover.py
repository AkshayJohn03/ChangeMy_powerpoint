"""Generate per-scene voiceover WAVs via `npx hyperframes tts` and record durations."""
import json
import shutil
import subprocess
import sys
from pathlib import Path

NPX = shutil.which("npx") or "npx.cmd"

OUT = Path(__file__).parent / "composition" / "assets" / "voiceover"
OUT.mkdir(parents=True, exist_ok=True)

SCENES = {
    "scene01": "It starts with a memo: \"We've rebranded — new colors, new fonts, please update all materials.\" Then you count: forty PowerPoint decks. Sales decks, pitch decks, training decks — each a dozen slides of text boxes, charts and tables, colored by hand, over years. Repainting by hand takes days — and you'll still miss the chart someone pasted at three a.m. with the old blue. BrandMorph is the robot that re-skins decks. Let's walk through how it works — and why version one failed.",
    "scene02": "Version one read a deck, threw it away, and rebuilt every slide from a blank layout as generic text boxes. It produced a deck — but not your deck. Charts: gone. Tables: gone. Groups, images, notes: flattened or dropped, silently. A different, worse deck. The diagnosis names it precisely: rebuilding is the bug. So version two stands on one principle — the original deck is the substrate. We transform only the formatting layers. Charts, tables, images, animations stay byte-identical, unless a rule explicitly changes them.",
    "scene03": "One fact about PowerPoint files: a P P T X is a ZIP archive of XML parts — a folder dressed up as a file. Colors hide in two places. The theme: one paint tin that many shapes point at by reference. Repaint the tin — the theme's color scheme — and every referencing shape updates at once. And hand-painted colors: a hex written directly on a run or a fill, ignoring the tin. Version two does both jobs: it repaints the tin with raw X M L surgery, then finds every hand-painted hex and remaps it — in place. The deck is never dismantled.",
    "scene04": "Nearest brand color — but nearest where? Computers store color as R G B, three numbers, and R G B distance lies. Our brand navy and pure black differ in every number, yet look nearly identical. So the engine compares colors in C I E Lab — a color space built so that distance matches human perception. The measure is Delta E: one number for how different two colors look. The mapping picks the smallest Delta E to a brand color, breaking ties by hue — warm stays warm.",
    "scene05": "Distance alone isn't enough. First, classify each color's role — background, surface, text, accent — from lightness, saturation, and context. Near-white on a dark slide is text. The same hex in a chart bar is data ink. Then the rule: map every color to the brand color playing the same role. Red text becomes the brand's danger color — still text, still red. A white background becomes the brand background. Text never becomes a background; charts stay charts. Every decision lands in the change log, with its role and its Delta E.",
    "scene06": "New fonts are a trap: the brand font may be wider, and wider text spills. So the fit guard measures every text frame with real font metrics from actual font files, simulating how PowerPoint wraps the words, line by line. If text doesn't fit, a shrink ladder runs: tighten spacing, then one point off the font size, two steps maximum. Still no fit? Flagged for a human — boxes are never widened. And a wrap-off text box can grow sideways forever — the guard measures that bleed against the slide edge, and flags it.",
    "scene07": "A property nobody asks for until they need it. Run BrandMorph twice — the second run changes nothing. That's idempotence, designed in: any color already within Delta E eight of a brand color counts as on-brand, and is left alone. Without that band, every run would nudge every color. A test proves it — and every report carries a hash that proves it again.",
    "scene08": "An enterprise tool that says \"trust me\" gets one run. So every morph produces a receipt: the morph report. Every change, row by row — slide, element, before, after, role, Delta E, confidence. Ambiguous calls are flagged for review. And dry-run mode executes every stage against a throwaway copy: the complete plan, zero changed files. The committed demo deck's receipt lists sixty-five audited changes — open it, it's in the repo.",
    "scene09": "Decks arrive from the outside world — and a P P T X can be weaponized. A zip bomb: forty kilobytes claiming to decompress to petabytes. The safety layer caps the compression ratio, and total uncompressed size, before extraction. Zip slip: entry paths escaping the working directory — path-checked. The X M L entity bomb — billion laughs — nested entities exploding on parse; the hardened parser refuses entity expansion entirely. Add an upload cap, and batch processing where one hostile deck fails alone — and the robot is safe to point at the internet.",
    "scene10": "Measured, not claimed. Forty-three offline tests: theme surgery, role mapping, idempotence, the fit ladder, safety rules, the API, the CLI. The fidelity sentinels are the interesting one: plant a chart, a table, a group, and a picture in a test deck, then assert the counts — and the image bytes — survive a morph untouched. On the committed demo deck: sixty-five audited changes. Eighteen color remaps, twenty-nine font roles, eighteen theme slots. Fidelity preserved; one wrap-off bleed caught.",
    "scene11": "Thirty-second recap. A deck is a ZIP of X M L; colors hide in the theme — the paint tin — and in hand-painted hexes. Version one rebuilt decks and destroyed them. Version two transforms in place: repaint the theme, remap every hand-painted color to the brand color playing the same role, measured in Lab. The fit guard keeps text in its box. Running it twice changes nothing. Every change lands in the receipt. Zip bombs are stopped at the door. Forty-three tests. Sixty-five audited changes. That's BrandMorph — now explain it to someone else.",
}

def wav_duration(path: Path) -> float:
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", str(path)],
        capture_output=True, text=True, check=True)
    return float(r.stdout.strip())

def main() -> int:
    only = sys.argv[1:] or list(SCENES)
    durations = {}
    dur_file = Path(__file__).parent / "voiceover-durations.json"
    if dur_file.exists():
        durations = json.loads(dur_file.read_text())
    for name in only:
        wav = OUT / f"{name}.wav"
        if wav.exists():
            durations[name] = wav_duration(wav)
            print(f"[skip] {name} exists, {durations[name]:.2f}s", flush=True)
            continue
        print(f"[tts ] {name} ...", flush=True)
        subprocess.run(
            [NPX, "hyperframes", "tts", SCENES[name],
             "--voice", "af_heart", "--output", str(wav)],
            check=True, capture_output=True, text=True)
        durations[name] = wav_duration(wav)
        print(f"       -> {durations[name]:.2f}s", flush=True)
    dur_file.write_text(json.dumps(durations, indent=2))
    total = sum(durations.values())
    print(f"TOTAL narration: {total:.1f}s ({total/60:.1f} min)")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
