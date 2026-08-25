"""BrandMorph v0.3 — one-click runner.

Usage:
    .\backend\venv\Scripts\python.exe run_brandmorph.py

Optionally specify a deck:
    .\backend\venv\Scripts\python.exe run_brandmorph.py "path\to\deck.pptx"
"""
import glob
import os
import shutil
import sys

REPO = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "backend"))

TEMPLATE_ONEDRIVE = os.path.expanduser(
    r"~\OneDrive - Akkodis\Documents\Me\Brand_guideline_Akkodis.pptx"
)
TEMPLATE_LOCAL = os.path.join(REPO, "data", "brand_template", "Brand_guideline_Akkodis.pptx")


def get_template() -> str:
    """Copy template from OneDrive to local, handling file locks."""
    os.makedirs(os.path.dirname(TEMPLATE_LOCAL), exist_ok=True)

    # If local copy already exists and is recent enough, use it
    if os.path.exists(TEMPLATE_LOCAL) and os.path.getsize(TEMPLATE_LOCAL) > 1000000:
        return TEMPLATE_LOCAL

    # Try copy2 first
    try:
        shutil.copy2(TEMPLATE_ONEDRIVE, TEMPLATE_LOCAL)
        print(f"Template copied: {TEMPLATE_LOCAL} ({os.path.getsize(TEMPLATE_LOCAL) // 1024} KB)")
        return TEMPLATE_LOCAL
    except PermissionError:
        pass

    # Fallback: read/write to bypass locks
    try:
        with open(TEMPLATE_ONEDRIVE, "rb") as src:
            data = src.read()
        with open(TEMPLATE_LOCAL, "wb") as dst:
            dst.write(data)
        print(f"Template copied (fallback): {TEMPLATE_LOCAL}")
        return TEMPLATE_LOCAL
    except Exception as e:
        print(f"ERROR: cannot access template at {TEMPLATE_ONEDRIVE}: {e}")
        print("Please copy the file manually to:")
        print(f"  {TEMPLATE_LOCAL}")
        sys.exit(1)


def find_deck(user_path=None) -> str:
    if user_path and os.path.exists(user_path):
        return user_path

    # Find first available raw deck
    for pattern in [
        "data/source/paired/raw/**/*.pptx",
        "data/source/paired/branded/**/*.pptx",
    ]:
        decks = sorted(glob.glob(os.path.join(REPO, pattern), recursive=True))
        if decks:
            return decks[0]

    print("ERROR: no .pptx files found in data/source/")
    sys.exit(1)


def main():
    user_deck = sys.argv[1] if len(sys.argv) > 1 else None

    print("=== BrandMorph v0.3 ===\n")

    # 1. Get template
    template_path = get_template()

    # 2. Get input deck
    deck_path = find_deck(user_deck)
    print(f"Input deck: {deck_path} ({os.path.getsize(deck_path) // 1024} KB)")

    # 3. Run pipeline
    from morphlite.pipeline.template_filler import TemplateFiller

    output_path = os.path.join(REPO, "branded_output.pptx")
    filler = TemplateFiller(template_path)
    result = filler.process(deck_path, output_path)

    # 4. Report
    print(f"\n=== RESULTS ===")
    print(f"Slides: {result['n_raw_slides']}")
    print(f"Binary changed: {result['binary_changed']}")
    print(f"\nSlide types:")
    for sm in result["slide_type_map"]:
        print(f"  Slide {sm['slide']}: {sm['type']}")

    print(f"\n=== OUTPUT ===")
    full_path = os.path.abspath(output_path)
    print(f"File: {full_path}")
    if os.path.exists(full_path):
        print(f"Size: {os.path.getsize(full_path) // 1024} KB")
        print(f"\nOpen it in PowerPoint to see the branded result.")
    else:
        print("ERROR: output file was not created")

    print(f"\n=== DONE ===")


if __name__ == "__main__":
    main()
