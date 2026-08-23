"""Phase 12.7: Mutation quality audit across diverse decks."""
from __future__ import annotations

import glob
import json
import os
import sys
import time
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from morphlite.pipeline.engine import BrandMorphPipeline
from morphlite.pipeline.brand_profile import DEFAULT_PROFILE


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

    out_dir = os.path.join(os.environ.get("TEMP", "/tmp"), "bm_audit")
    os.makedirs(out_dir, exist_ok=True)

    all_mutations = []
    deck_summaries = []

    for i, (deck_path, tag) in enumerate(selected):
        deck_label = f"deck_{i+1:02d}_{tag}"
        out_path = os.path.join(out_dir, f"out_{i}.pptx")
        t0 = time.time()
        entry = {"deck": deck_label, "status": "OK", "slides": 0,
                 "mutations_changed": 0, "mutations_no_change": 0,
                 "mutations_unsupported": 0, "mutations_failed": 0,
                 "time_sec": 0}

        try:
            pipeline = BrandMorphPipeline(profile=DEFAULT_PROFILE)
            result = pipeline.process(deck_path, out_path)

            entry["slides"] = len(result.slides)
            totals = result.plan.get("totals", {})
            entry["mutations_changed"] = totals.get("changed", 0)
            entry["mutations_no_change"] = totals.get("no_change", 0)
            entry["mutations_unsupported"] = totals.get("unsupported", 0)
            entry["mutations_failed"] = totals.get("failed", 0)
            entry["time_sec"] = round(time.time() - t0, 1)

            for s_idx, slide in enumerate(result.slides):
                for dec in slide.get("decisions", []):
                    mr = dec.get("mutation")
                    if not mr or mr.get("status") != "CHANGED":
                        continue
                    all_mutations.append({
                        "deck": deck_label,
                        "slide": s_idx + 1,
                        "shape_id": mr.get("shape_id"),
                        "shape_name": mr.get("shape_name", ""),
                        "action": mr.get("action", ""),
                        "changes": mr.get("changes", []),
                        "reason": mr.get("reason", ""),
                    })

        except Exception as exc:
            entry["status"] = f"ERROR: {exc}"

        if os.path.exists(out_path):
            os.remove(out_path)
        deck_summaries.append(entry)
        print(f"[{i+1}/{len(selected)}] {deck_label} changed={entry['mutations_changed']} "
              f"no_change={entry['mutations_no_change']} unsupported={entry['mutations_unsupported']} "
              f"time={entry['time_sec']:.0f}s status={entry['status']}", flush=True)

    # Aggregate mutation analysis
    action_counts = Counter(m["action"] for m in all_mutations)
    property_counts = Counter()
    font_before = Counter()
    font_after = Counter()
    size_changes = []
    color_changes = []
    for m in all_mutations:
        for c in m.get("changes", []):
            property_counts[c.get("property", "?")] += 1
            if c["property"] == "font":
                font_before[c["before"]] += 1
                font_after[c["after"]] += 1
            elif c["property"] == "size_pt":
                try:
                    b = float(c["before"]) if c["before"] else 0
                    a = float(c["after"]) if c["after"] else 0
                    if b > 0 and a > 0:
                        size_changes.append({"before": b, "after": a})
                except (ValueError, TypeError):
                    pass
            elif c["property"] == "color":
                color_changes.append({"before": c["before"], "after": c["after"]})

    total_changed = len(all_mutations)
    total_no_change = sum(d["mutations_no_change"] for d in deck_summaries)
    total_unsupported = sum(d["mutations_unsupported"] for d in deck_summaries)
    total_failed = sum(d["mutations_failed"] for d in deck_summaries)

    payload = {
        "schema": "mutation_audit_v1",
        "decks_tested": len(selected),
        "decks_ok": sum(1 for d in deck_summaries if d["status"] == "OK"),
        "total_changed": total_changed,
        "total_no_change": total_no_change,
        "total_unsupported": total_unsupported,
        "total_failed": total_failed,
        "mutation_rate": round(total_changed / max(total_changed + total_no_change + total_unsupported, 1), 4),
        "by_action": dict(action_counts),
        "by_property": dict(property_counts.most_common()),
        "font_transitions": {
            "top_sources": font_before.most_common(10),
            "top_targets": font_after.most_common(10),
        },
        "size_changes_sample": size_changes[:20],
        "color_changes_sample": color_changes[:20],
        "per_deck": deck_summaries,
    }

    out_json = Path("research/MUTATION_AUDIT.json")
    out_json.write_text(json.dumps(payload, indent=1, ensure_ascii=False), encoding="utf-8")

    md = [
        "# Phase 12.7 - Mutation Quality Audit",
        "",
        f"Decks: {len(selected)} | Verified changes: **{total_changed}** | No-change: {total_no_change} | Unsupported: {total_unsupported} | Failed: {total_failed}",
        "",
        f"Mutation success rate: **{round(total_changed / max(total_changed + total_no_change + total_unsupported, 1) * 100, 1)}%**",
        "",
        "## Mutations by action type",
        "",
        "| Action | Count | Share |",
        "|---|---:|---:|",
    ]
    for action, cnt in action_counts.most_common():
        md.append(f"| {action} | {cnt} | {round(cnt / max(total_changed,1)*100,1)}% |")

    md += ["", "## Property change breakdown", "", "| Property | Changes |", "|---|---:|"]
    for prop, cnt in property_counts.most_common():
        md.append(f"| {prop} | {cnt} |")

    md += ["", "## Font transitions (source -> target)", "", "| Source font | Count |", "|---|---:|"]
    for fname, cnt in font_before.most_common(8):
        md.append(f"| {fname} | {cnt} |")

    md += ["", "## Size changes (sample)", ""]
    for sc in size_changes[:10]:
        md.append(f"- {sc['before']}pt -> {sc['after']}pt")

    md += ["", "## Color changes (sample)", ""]
    for cc in color_changes[:10]:
        md.append(f"- {cc['before']} -> {cc['after']}")

    Path("research/MUTATION_AUDIT.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(json.dumps({k: payload[k] for k in ("decks_tested", "total_changed", "total_no_change", "mutation_rate")}, indent=1))
    print("\ntop actions:", dict(action_counts.most_common()))
    print("top properties:", dict(property_counts.most_common()))


if __name__ == "__main__":
    main()
