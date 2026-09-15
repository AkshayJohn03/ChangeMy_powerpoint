from pathlib import Path
import re

files_to_check = [
    Path(r"C:\Users\Akshay.JOHN-XAVIER\OneDrive - Akkodis\Documents\Me\session-ses_brandmorph.md"),
    Path(r"C:\Users\Akshay.JOHN-XAVIER\OneDrive - Akkodis\Documents\Me\Redesign with Design System\redesign_prompt_guide.md"),
    Path(r"C:\Users\Akshay.JOHN-XAVIER\.gemini\antigravity-ide\scratch\BrandMorph\COLLAB_HANDOVER.md"),
    Path(r"C:\Users\Akshay.JOHN-XAVIER\.gemini\antigravity-ide\brain\2beb96ac-5bff-4ae0-b9c9-cdd58bd8ec16\PDR_BrandMorph_Deck_Engine.md"),
]

# Also search any .md or .txt in Documents\Me
me_dir = Path(r"C:\Users\Akshay.JOHN-XAVIER\OneDrive - Akkodis\Documents\Me")
for p in me_dir.rglob("*.md"):
    if p not in files_to_check:
        files_to_check.append(p)

keywords = ["guideline", "slide 1", "slide 2", "slide 3", "slide 4", "slide 5", "slide 6", "slide 7", "slide 8", "slide 9", "slide 10", "template", "personalizado", "brand", "rule"]

for f in files_to_check:
    if not f.exists():
        continue
    try:
        text = f.read_text(encoding="utf-8", errors="ignore")
    except Exception as e:
        continue
    
    found = []
    for line_no, line in enumerate(text.splitlines(), 1):
        line_l = line.lower()
        if any(k in line_l for k in ["slide 1", "slide 2", "slide 3", "slide 4", "slide 5", "slide 6", "slide 7", "slide 8", "slide 9", "slide 10", "redesign", "guideline", "dark base", "akkodis"]):
            if len(line.strip()) > 15:
                found.append((line_no, line.strip()))
    
    if found:
        print(f"\n=== MATCHES IN {f.name} ({len(found)} hits) ===")
        for lno, ltxt in found[:25]:
            print(f"  L{lno}: {ltxt[:120]}")
