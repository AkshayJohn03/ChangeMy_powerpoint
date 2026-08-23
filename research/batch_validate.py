"""Phase 12.5 Sprint A: batch-validate production pipeline on diverse decks."""
from __future__ import annotations

import glob
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from morphlite.pipeline.engine import BrandMorphPipeline


def main() -> None:
    decks = sorted(glob.glob("data/source/paired/raw/**/*.pptx", recursive=True))
    branded = sorted(glob.glob("data/source/paired/branded/**/*.pptx", recursive=True))

    seen = set()
    selected = []
    for pool, tag in ((decks, "raw"), (branded, "branded")):
        for d in pool:
            did = Path(d).stem[:20]
            if did not in seen and len(selected) < 15:
                seen.add(did)
                selected.append((d, tag))

    results = []
    out_dir = os.path.join(os.environ.get("TEMP", "/tmp"), "bm_batch")
    os.makedirs(out_dir, exist_ok=True)

    for i, (deck_path, tag) in enumerate(selected):
        deck_name = Path(deck_path).stem
        out_path = os.path.join(out_dir, f"out_{i}.pptx")
        t0 = time.time()
        entry = {
            "deck": f"deck_{i+1:02d}_{tag}",
            "source_file": deck_name,
            "status": "OK",
            "slides": 0, "nodes_total": 0,
            "applied": 0, "review": 0, "noop": 0, "preserved": 0,
            "by_action": {}, "time_sec": 0, "output_valid": False,
        }
        try:
            pipeline = BrandMorphPipeline()
            result = pipeline.process(deck_path, out_path)
            totals = result.plan.get("totals", {})
            by_policy = totals.get("by_policy", {})
            entry.update({
                "slides": len(result.slides),
                "nodes_total": totals.get("nodes_total", 0),
                "applied": totals.get("changed", by_policy.get("APPLY", 0)),
                "review": by_policy.get("REVIEW", 0),
                "noop": by_policy.get("NOOP", 0),
                "preserved": by_policy.get("PRESERVE", 0),
                "by_action": totals.get("by_action", {}),
                "time_sec": round(time.time() - t0, 1),
                "output_valid": os.path.exists(out_path) and os.path.getsize(out_path) > 1000,
            })
        except Exception as exc:
            entry["status"] = f"ERROR: {exc}"
            entry["time_sec"] = round(time.time() - t0, 1)
        if os.path.exists(out_path):
            os.remove(out_path)
        results.append(entry)
        print(f"[{i+1}/{len(selected)}] {entry['deck']:20s} "
              f"slides={entry['slides']:3d} nodes={entry['nodes_total']:4d} "
              f"applied={entry['applied']:3d} review={entry['review']:2d} "
              f"time={entry['time_sec']:.0f}s valid={entry['output_valid']} "
              f"status={entry['status']}", flush=True)

    ok = [r for r in results if r["status"] == "OK"]
    total_nodes = sum(r["nodes_total"] for r in ok)
    total_applied = sum(r["applied"] for r in ok)
    summary = {
        "decks_tested": len(results),
        "decks_ok": len(ok),
        "decks_failed": len(results) - len(ok),
        "total_nodes": total_nodes,
        "total_applied": total_applied,
        "mean_apply_rate": round(total_applied / max(total_nodes, 1), 4),
        "total_review": sum(r["review"] for r in ok),
        "all_outputs_valid": all(r["output_valid"] for r in ok),
        "mean_time_sec": round(sum(r["time_sec"] for r in ok) / max(len(ok), 1), 1),
    }

    out_json = Path("research/BATCH_VALIDATION.json")
    out_json.write_text(json.dumps({"summary": summary, "per_deck": results}, indent=1), encoding="utf-8")

    md = ["# Phase 12.5 Batch Validation", "",
          "| Deck | Slides | Nodes | Applied | Review | NOOP | Time(s) | Valid |",
          "|---|---:|---:|---:|---:|---:|---:|---|"]
    for r in results:
        md.append(f"| {r['deck']} | {r['slides']} | {r['nodes_total']} | {r['applied']} | {r['review']} | {r['noop']} | {r['time_sec']} | {r['output_valid']} |")
    md += ["", f"**Summary**: {json.dumps(summary)}"]
    Path("research/BATCH_VALIDATION.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
