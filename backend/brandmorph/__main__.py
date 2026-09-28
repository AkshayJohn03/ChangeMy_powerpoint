"""CLI entry: `python -m brandmorph apply --deck deck.pptx --brand akkodis --out out.pptx`.

Batch mode (scalability): pass multiple decks or a glob and `--out` becomes a
directory — `python -m brandmorph apply --deck "decks/*.pptx" --brand akkodis
--out branded/`. One hostile or corrupt deck fails alone; the batch continues
and a summary table prints at the end.
"""

from __future__ import annotations

import argparse
import glob
import json
import sys
from pathlib import Path

from .brand.profile import BrandDNA
from .engine.analyzer import analyze
from .engine.pipeline import MorphOptions, MorphPipeline
from .engine.safety import UnsafeDeckError


def _llm_from_env():
    from .llm import env_client

    client = env_client()
    if client is None:
        print(
            "copy rewriting requested but LLM_API_KEY is not set — continuing without",
            file=sys.stderr,
        )
    return client


def _expand_decks(deck_args: list[str]) -> list[Path]:
    out: list[Path] = []
    for arg in deck_args:
        matches = glob.glob(arg)
        if matches:
            out.extend(Path(m) for m in sorted(matches))
        else:
            out.append(Path(arg))
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        prog="brandmorph", description="Re-brand a PowerPoint deck in place (v2 engine)"
    )
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_apply = sub.add_parser("apply", help="apply a brand to one deck or a batch (globs OK)")
    p_apply.add_argument("--deck", required=True, nargs="+", help="deck path(s) or glob(s)")
    p_apply.add_argument("--brand", required=True, help="bundled brand name or YAML/JSON path")
    p_apply.add_argument(
        "--out", required=True,
        help="output file (single deck) or directory (batch — same filename inside)",
    )
    p_apply.add_argument("--dry-run", action="store_true", help="report only, no output deck")
    p_apply.add_argument("--report", help="directory for morph_report.md/.json")
    p_apply.add_argument(
        "--rewrite-copy", action="store_true",
        help="enable LLM copy rewriting (requires LLM_API_KEY)",
    )

    p_inv = sub.add_parser("inventory", help="print the deck inventory JSON")
    p_inv.add_argument("--deck", required=True)

    args = ap.parse_args(argv)

    if args.cmd == "inventory":
        print(json.dumps(analyze(args.deck), indent=2))
        return 0

    dna = BrandDNA.load(args.brand)
    llm = _llm_from_env() if args.rewrite_copy else None
    options = MorphOptions(
        dry_run=args.dry_run, rewrite_copy=True if args.rewrite_copy else None
    )
    decks = _expand_decks(args.deck)
    pipeline = MorphPipeline(dna, llm, options)

    if len(decks) == 1:
        report = pipeline.run(decks[0], args.out, report_dir=args.report)
        print(report.to_markdown())
        if report.review_flags:
            print(f"\n{len(report.review_flags)} item(s) flagged for manual review.", file=sys.stderr)
        return 0

    # ---- batch mode: isolation per deck, continue on failure ---------------
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    results: list[tuple[str, str, str]] = []  # (deck, status, detail)
    for deck in decks:
        out_path = out_dir / deck.name
        try:
            report = pipeline.run(deck, out_path, report_dir=args.report)
            results.append((deck.name, "ok", f"{report.total_changes} changes"))
        except UnsafeDeckError as e:
            results.append((deck.name, "REJECTED", f"unsafe deck: {e}"))
        except Exception as e:  # one bad deck never kills the batch
            results.append((deck.name, "FAILED", str(e)[:120]))

    print("| deck | status | detail |", file=sys.stderr)
    print("|---|---|---|", file=sys.stderr)
    for name, status, detail in results:
        print(f"| {name} | {status} | {detail} |", file=sys.stderr)
    failed = sum(1 for _, s, _ in results if s != "ok")
    print(f"\nbatch: {len(results) - failed}/{len(results)} succeeded", file=sys.stderr)
    return 1 if failed and len(results) == failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
