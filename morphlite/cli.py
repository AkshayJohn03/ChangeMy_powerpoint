"""CLI: raw PPTX -> typed spec -> branded .pptx"""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
from .models.content_model import extract_deck
from .llm.spec_builder import SpecBuilder
from .llm.provider import get_provider, CONFIG
from .render.renderer import BrandRenderer

def main(argv=None):
    ap = argparse.ArgumentParser(prog="morphlite", description="Raw PPTX -> Akkodis-branded PPTX")
    ap.add_argument("raw_deck", help="Path to raw .pptx")
    ap.add_argument("--out","-o", default=None, help="Output path (default: <input>_branded.pptx)")
    ap.add_argument("--provider","-p", default="", choices=["","azure","openai","mock"])
    ap.add_argument("--dump-spec", default=None)
    ap.add_argument("--no-llm", action="store_true")
    args = ap.parse_args(argv)
    raw = Path(args.raw_deck)
    if not raw.exists():
        print(f"ERROR: {raw} not found", file=sys.stderr); sys.exit(1)
    out = args.out or str(raw.with_name(raw.stem + "_branded.pptx"))
    print("[1/3] Extracting content model ...")
    deck = extract_deck(str(raw))
    print(f"  -> {deck.n_slides} slides")
    if args.no_llm or not CONFIG.llm_is_configured():
        if not CONFIG.llm_is_configured():
            print("[2/3] No LLM creds -> heuristic builder (no key needed).")
        provider = get_provider("mock")
    else:
        name = args.provider or CONFIG.pick_provider()
        print(f"[2/3] Building spec via {name} ...")
        provider = get_provider(name)
    builder = SpecBuilder(llm=provider)
    spec = builder.build(deck)
    print(f"  -> {spec.n_slides} slides in spec")
    if args.dump_spec:
        Path(args.dump_spec).write_text(json.dumps({"brand":spec.brand,"slides":[{"archetype":s.archetype,"title":s.title} for s in spec.slides]}, indent=2), encoding="utf-8")
        print(f"  -> spec -> {args.dump_spec}")
    print("[3/3] Rendering ...")
    BrandRenderer().render(spec, out)
    print(f"  -> saved: {out}")

if __name__ == "__main__":
    main()
