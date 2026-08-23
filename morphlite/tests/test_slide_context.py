"""Phase 9 STEP 5 guards: schema, source-only, shuffle-invariance, determinism,
NaN guard, degenerate slides, template-dedupe behaviour.

Run: python -m morphlite.tests.test_slide_context  -> SLIDE CONTEXT GUARD PASSED
"""
from __future__ import annotations

import copy
import io
import random
import sys
from pathlib import Path

import numpy as np

from ..training import slide_context as sc

MODULE_FILE = Path(sc.__file__)
BANNED_IN_SOURCE = [
    "branded",
    "match_confidence",
    "transformation_records",
    'geometry["after"',
    "geometry.get('after'",
    '"after"',
    "'after'",
]


def t1_schema() -> None:
    assert len(sc.FEATURE_NAMES) == 45, len(sc.FEATURE_NAMES)
    assert len(set(sc.FEATURE_NAMES)) == 45
    assert len(sc.G1) == 11 and len(sc.G2) == 11 and len(sc.G3) == 13 and len(sc.G4) == 10
    missing = sc.MUST_HAVE - set(sc.FEATURE_NAMES)
    assert not missing, missing
    print("t1 schema OK (45 features, MUST-HAVE present)")


def t2_source_only() -> None:
    src = MODULE_FILE.read_text(encoding="utf-8")
    hits = [tok for tok in BANNED_IN_SOURCE if tok in src]
    assert not hits, f"banned tokens in source: {hits}"
    print("t2 source-only OK")


def _tiny_rows() -> list[dict]:
    def node(i, cx, cy, text=False):
        b = {
            "x": cx - 0.05, "y": cy - 0.02, "w": 0.1, "h": 0.04,
            "cx": cx, "cy": cy, "area_log1p": 0.0, "aspect": 0.0,
            "container_depth": 0, "eff_size_pt": 12.0 if text else 0.0,
            "overlap_frac_max": 0.0, "text_len_log1p": 2.5 if text else 0.0,
            "is_text": text, "is_image": False, "is_shape": not text,
            "is_line": False, "is_table": False, "is_chart": False,
            "is_group": False, "is_arrow": False, "bold": False,
            "is_largest_font": text,
        }
        return {"schema": "prop_v1", "sample_id": f"syn__s001__n{i:03d}",
                "group": "fam_syn", "label": "UNCHANGED",
                "slide_key": "syn__s001", "base": b,
                "nbrs": {"ALIGNMENT": [], "CONTAINMENT": [], "GROUP": [], "ALL": []}}

    return [
        node(0, 0.2, 0.15, True), node(1, 0.55, 0.5),
        node(2, 0.85, 0.85), node(3, 0.35, 0.75),
    ]


def t3_label_shuffle_invariance() -> None:
    rng = random.Random(1234)
    real = []
    p = Path("data/processed/propagation_cache.jsonl")
    with open(p, encoding="utf-8") as fh:
        for line in fh:
            real.append(json_load(line))
            if len(real) >= 600:
                break
    _, X1 = sc.extract(real)
    shuffled = copy.deepcopy(real)
    labels = [r["label"] for r in shuffled]
    rng.shuffle(labels)
    for r, lab in zip(shuffled, labels):
        r["label"] = lab
    _, X2 = sc.extract(shuffled)
    assert np.array_equal(X1, X2), "features changed under label shuffle"
    print(f"t3 label-shuffle invariance OK ({len(real)} rows)")


def json_load(s: str):
    import json

    return json.loads(s)


def t4_determinism() -> None:
    rows = _tiny_rows()
    n1, X1 = sc.extract(rows)
    n2, X2 = sc.extract(copy.deepcopy(rows))
    assert n1 == n2 and X1.tobytes() == X2.tobytes()
    print("t4 determinism OK")


def t5_nan_guard_and_degenerate() -> None:
    rows = _tiny_rows()
    _, X = sc.extract(rows[:1])
    assert np.isfinite(X).all()
    _, Xa = sc.extract(rows)
    assert np.isfinite(Xa).all()
    print("t5 nan/inf + degenerate-slide OK")


def t6_template_dedupe_helper() -> None:
    from ..training.slide_context_bench import template_dedupe

    fp_index = {
        "deckA": {"exact_hash": "h1"},
        "deckB": {"exact_hash": "h1"},
        "deckC": {"exact_hash": "h2"},
        "deckD": {"exact_hash": "h3"},
    }
    rows = _tiny_rows()
    for i, dk in enumerate(["deckA", "deckB", "deckC", "deckD"]):
        rows[i]["sample_id"] = f"{dk}__s001__n{i:03d}"
        rows[i]["group"] = f"fam_{i+1:03d}"
        rows[i]["slide_key"] = f"{dk}__s001"
    mask, report = template_dedupe(rows, fp_index)
    assert mask.count(True) == 3 and mask[1] is False, (mask, report)
    assert report["rows_excluded"] == 1 and report["clusters_spanning_multiple_families"] >= 1
    print("t6 template-dedupe OK")


def t7_must_have_signal_sanity() -> None:
    rows = _tiny_rows()
    names, X = sc.extract(rows)
    col = {n: i for i, n in enumerate(names)}
    for feat in sorted(sc.MUST_HAVE):
        assert feat in col
    # rel_x_med of first node (left-most) must be negative on this fixture
    assert X[0, col["rel_x_med"]] < 0 < X[2, col["rel_x_med"]]
    print("t7 must-have directional sanity OK")


def main() -> int:
    t1_schema()
    t2_source_only()
    t4_determinism()
    t5_nan_guard_and_degenerate()
    t6_template_dedupe_helper()
    t7_must_have_signal_sanity()
    t3_label_shuffle_invariance()
    print("SLIDE CONTEXT GUARD PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
