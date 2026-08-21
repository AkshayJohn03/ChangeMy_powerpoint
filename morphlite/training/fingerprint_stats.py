"""Verification gate 3: fingerprint uniqueness / collision statistics.

    python -m morphlite.training.fingerprint_stats
"""
from __future__ import annotations

import json
from collections import Counter
from itertools import combinations
from pathlib import Path

from .. import config
from ..features import fingerprint as fp

AST_V2 = config.EXTRACTED_DIR / "ast_v2"


def main() -> None:
    index = {}
    with open(AST_V2 / "extraction_manifest_v2.jsonl", encoding="utf-8") as fh:
        for line in fh:
            rec = json.loads(line)
            index[rec["deck_id"]] = rec["ast_v2_path"]

    fps = fp.build_all(sorted(index), index)
    ids = sorted(fps)

    exact_hashes = Counter(fps[d]["exact_hash"] for d in ids)
    dup_clusters = {h: c for h, c in exact_hashes.items() if c > 1}

    pair_sims = []
    template_ids = [d for d in ids if d.startswith("template__")]
    for a, b in combinations(ids, 2):
        s = fp.similarity(fps[a], fps[b])
        pair_sims.append((s["weighted"], a, b, s["exact_match"]))

    near_dups = [(w, a, b) for w, a, b, em in pair_sims if w >= 0.95 and not em]
    exact_pairs = [(a, b) for w, a, b, em in pair_sims if em]

    sims_template_to_template = [
        w for w, a, b, _ in pair_sims if a in template_ids and b in template_ids
    ]
    sims_template_to_other = [
        w for w, a, b, _ in pair_sims if (a in template_ids) != (b in template_ids)
    ]
    all_w = [w for w, _, _, _ in pair_sims]

    def pct(values, q):
        values = sorted(values)
        return round(values[int(q * (len(values) - 1))], 4) if values else None

    report = {
        "decks": len(ids),
        "pairs_computed": len(pair_sims),
        "exact_duplicate_clusters": len(dup_clusters),
        "exact_duplicate_decks": sum(dup_clusters.values()),
        "near_dup_pairs_ge_095_non_exact": len(near_dups),
        "sim_percentiles_all": {q: pct(all_w, q) for q in (0.05, 0.25, 0.5, 0.75, 0.95)},
        "template_separation": {
            "n_templates": len(template_ids),
            "template_to_template_mean": round(sum(sims_template_to_template) / max(len(sims_template_to_template), 1), 4),
            "template_to_other_p95": pct(sims_template_to_other, 0.95),
            "template_to_other_max": round(max(sims_template_to_other), 4) if sims_template_to_other else None,
        },
        "nearest_neighbors_sample": [
            {"sim": round(w, 3), "a": a.split("__")[-1][:36], "b": b.split("__")[-1][:36]}
            for w, a, b, _ in sorted(pair_sims, key=lambda t: -t[0])[:8]
        ],
    }
    (config.METADATA_DIR / "FINGERPRINT_STATS.json").write_text(json.dumps(report, indent=1), encoding="utf-8")
    print(json.dumps(report, indent=1))

    with open(config.METADATA_DIR / "FINGERPRINT_INDEX.json", "w", encoding="utf-8") as fh:
        json.dump({d: {"exact_hash": fps[d]["exact_hash"], "canonical": fps[d]["canonical"]} for d in ids}, fh, indent=0)


if __name__ == "__main__":
    main()
