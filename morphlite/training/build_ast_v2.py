"""AST v2 builder: V1 AST + effective typography, written to a parallel tree.

V1 artifacts under data/extracted/ast/ remain untouched.

    python -m morphlite.training.build_ast_v2
"""
from __future__ import annotations

import json
import statistics
import time
from collections import Counter
from pathlib import Path

from .. import config
from ..ast import extractor
from ..ast.effective import DeckTypographyResolver

AST_ROOT = config.EXTRACTED_DIR / "ast"
AST_V2_ROOT = config.EXTRACTED_DIR / "ast_v2"

FIELD_KEYS = ("font_family", "font_size_pt", "bold", "italic", "color")


def enrich_deck(deck: dict, resolver: DeckTypographyResolver) -> tuple[dict, dict]:
    stats = {
        "nodes_total": 0,
        "nodes_with_text": 0,
        "resolved": Counter(),
        "unresolved": Counter(),
        "origin_hist": Counter(),
    }

    for slide in deck["slides"]:
        idx = slide["index"] - 1
        eff_map = resolver.resolve_slide(idx)
        flat = extractor.flatten_nodes(slide["nodes"])
        sizes_eff = []
        for node in flat:
            stats["nodes_total"] += 1
            has_text = bool(node.get("paragraphs"))
            if not has_text:
                continue
            stats["nodes_with_text"] += 1
            sid = str(node.get("shape_id")) if node.get("shape_id") is not None else None
            matched = eff_map.get(sid) if sid else None
            if matched is None:
                stats["unresolved"]["no_shape_match"] += 1
                continue
            eff_clean = {k: v for k, v in matched.items() if k in FIELD_KEYS}
            if not eff_clean:
                stats["unresolved"]["empty"] += 1
                continue
            node["effective"] = eff_clean
            for k, payload in eff_clean.items():
                stats["resolved"][k] += 1
                stats["origin_hist"][f"{k}:{payload['origin']}"] += 1
                if k == "font_size_pt" and isinstance(payload.get("value"), (int, float)):
                    sizes_eff.append(payload["value"])

        slide["eff_context"] = {
            "eff_max_size": max(sizes_eff) if sizes_eff else None,
            "eff_median_size": round(statistics.median(sizes_eff), 2) if sizes_eff else None,
        }

    return deck, stats


def _matches(node: dict, eff: dict) -> bool:
    """Match AST node to resolved shape by dominant explicit typography."""
    dom_size = None
    dom_fam = None
    votes_size, votes_fam = {}, {}
    for p in node.get("paragraphs") or []:
        for r in p.get("runs") or []:
            s = r.get("font_size_pt")
            f = r.get("font_family")
            if s:
                votes_size[s] = votes_size.get(s, 0) + 1
            if f:
                votes_fam[f] = votes_fam.get(f, 0) + 1
    dom_size = max(votes_size, key=votes_size.get) if votes_size else None
    dom_fam = max(votes_fam, key=votes_fam.get) if votes_fam else None

    eff_size = (eff.get("font_size_pt") or {}).get("value")
    eff_fam = (eff.get("font_family") or {}).get("value")

    if dom_size is not None and eff_size is not None and abs(dom_size - eff_size) < 0.01:
        return True
    if dom_fam is not None and eff_fam is not None and dom_fam.lower() == str(eff_fam).lower():
        return True
    return False


def main() -> None:
    AST_V2_ROOT.mkdir(parents=True, exist_ok=True)
    manifest = []
    with open(AST_ROOT / "extraction_manifest.jsonl", encoding="utf-8") as fh:
        entries = [json.loads(line) for line in fh]

    totals = Counter()
    t0 = time.time()
    for i, rec in enumerate(entries, 1):
        src = Path(rec["source"])
        deck = json.loads(Path(rec["ast_path"]).read_text(encoding="utf-8"))

        with DeckTypographyResolver(str(src)) as resolver:
            deck, stats = enrich_deck(deck, resolver)

        deck["schema_version"] = "2.0.0"
        out_dir = AST_V2_ROOT / rec["bucket"] / rec["batch"]
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"{rec['deck_id']}.json"
        out_path.write_text(json.dumps(deck, ensure_ascii=False), encoding="utf-8")

        for k, v in stats["resolved"].items():
            totals[f"resolved:{k}"] += v
        for k, v in stats["unresolved"].items():
            totals[f"unresolved:{k}"] += v
        for k, v in stats["origin_hist"].items():
            totals[f"origin:{k}"] += v

        manifest.append({"deck_id": rec["deck_id"], "bucket": rec["bucket"], "batch": rec["batch"], "name_key": rec["name_key"], "n_slides": rec["n_slides"], "ast_v2_path": str(out_path)})
        if i % 40 == 0:
            print(f"[{i}/{len(entries)}]", flush=True)

    with open(AST_V2_ROOT / "extraction_manifest_v2.jsonl", "w", encoding="utf-8") as fh:
        for m in manifest:
            fh.write(json.dumps(m, ensure_ascii=False) + "\n")

    text_nodes = sum(v for k, v in totals.items() if k.startswith("resolved")) or 1
    coverage = {
        "decks": len(entries),
        "elapsed_sec": round(time.time() - t0, 1),
        "field_resolution": {
            k.split(":")[1]: round(v / max(text_nodes / 5, 1), 4)
            for k, v in totals.items() if k.startswith("resolved:")
        },
        "unresolved_counts": {k.split(":", 1)[1]: v for k, v in totals.items() if k.startswith("unresolved")},
        "origin_histogram": {k.split(":", 1)[1]: v for k, v in totals.items() if k.startswith("origin:")},
    }
    (config.METADATA_DIR / "EFFECTIVE_COVERAGE.json").write_text(json.dumps(coverage, indent=1), encoding="utf-8")
    print(json.dumps(coverage, indent=1)[:1800])


if __name__ == "__main__":
    main()
