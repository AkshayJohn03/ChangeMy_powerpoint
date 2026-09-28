"""CLI entry: `python -m brandmorph apply --deck deck.pptx --brand akkodis --out out.pptx`."""

from __future__ import annotations

import argparse
import json
import sys

from .brand.profile import BrandDNA
from .engine.analyzer import analyze
from .engine.pipeline import MorphOptions, MorphPipeline


def _llm_from_env():
    from .llm import env_client

    client = env_client()
    if client is None:
        print(
            "copy rewriting requested but LLM_API_KEY is not set — continuing without",
            file=sys.stderr,
        )
    return client


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        prog="brandmorph", description="Re-brand a PowerPoint deck in place (v2 engine)"
    )
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_apply = sub.add_parser("apply", help="apply a brand to a deck")
    p_apply.add_argument("--deck", required=True)
    p_apply.add_argument("--brand", required=True, help="bundled brand name or YAML/JSON path")
    p_apply.add_argument("--out", required=True)
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
    report = MorphPipeline(dna, llm, options).run(args.deck, args.out, report_dir=args.report)
    print(report.to_markdown())
    if report.review_flags:
        print(f"\n{len(report.review_flags)} item(s) flagged for manual review.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
