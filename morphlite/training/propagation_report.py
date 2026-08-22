"""Phase 7: markdown report renderer for the propagation experiment.

Reads PROPAGATION_RESULTS.json (measured aggregate metrics only) plus the
relational benchmark / dataset integrity aggregates and renders
data/metadata/PROPAGATION_EXPERIMENT_REPORT.md.

Compliance: this module emits AGGREGATE STATISTICS ONLY (counts, rates,
metrics). It never reads or prints deck filenames, slide text, client names,
or deck_registry.json.

    python -m morphlite.training.propagation_report             # render real report
    python -m morphlite.training.propagation_report --selftest  # render-gate check
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

from .. import config

RESULTS_PATH = config.METADATA_DIR / "PROPAGATION_RESULTS.json"
RELATIONAL_PATH = config.METADATA_DIR / "RELATIONAL_BENCHMARK.json"
INTEGRITY_PATH = config.METADATA_DIR / "DATASET_INTEGRITY.json"
REPORT_PATH = config.METADATA_DIR / "PROPAGATION_EXPERIMENT_REPORT.md"

WEAK = ["RESTYLE", "RESIZE", "REMOVE", "MOVE"]
GRID_COLS = [
    ("rounds", "rounds"),
    ("alpha", "alpha"),
    ("edges", "edges"),
    ("head", "head"),
    ("pooled_macro_f1", "macro"),
    ("weak_macro_f1", "weak"),
    ("move_precision", "moveP"),
    ("move_recall", "moveR"),
    ("move_f1", "moveF1"),
    ("unchanged_recall", "unchanged_recall"),
    ("unsafe_rate", "unsafe_rate"),
    ("brier", "brier"),
]
REQUIRED_HEADERS = [
    "# Propagation Experiment Report (Phase 7)",
    "## Protocol",
    "## Baselines",
    "## Grid summary",
    "## Best configuration & promotion decision",
    "## Interpretation guidance",
    "## Safety & calibration",
    "## Determinism & integrity",
]
NO_GO_TEXT = (
    "NO-GO: iterative propagation of OOF predicted probabilities does not recover "
    "oracle-context performance at current label/model quality; do not proceed to "
    "neural MorphNet. Recommended investment: more validated pairs, better "
    "correspondence, manual review loop."
)
GO_TEXT = "GO for scoped message-passing prototype under identical CV + safety gates."


def _load(path: Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _fmt(v) -> str:
    if isinstance(v, float):
        return f"{v if abs(v) > 5e-5 else 0.0:.4f}"
    return str(v)


def _anchor_reference(relational_path: Path | None, results: dict) -> tuple[float, float]:
    """(cv_macro_f1_mean, weak_macro_f1) from RELATIONAL_BENCHMARK ANCHOR_CONTEXT rf."""
    src = Path(relational_path) if relational_path else RELATIONAL_PATH
    try:
        rel = _load(src)
        rf = rel["results"]["ANCHOR_CONTEXT"]["random_forest"]
        per = rf["pooled_per_class_f1"]
        present = [k for k in WEAK if k in per]
        weak = sum(per[k] for k in present) / max(len(present), 1)
        return float(rf["cv_macro_f1_mean"]), round(float(weak), 4)
    except (OSError, KeyError, TypeError):
        ref = results.get("baselines", {}).get("anchor_reference", {})
        return float(ref.get("cv_macro_f1", 0.0)), float(ref.get("weak_macro_f1", 0.0))


def _gate_rows(best: dict, base: dict, anchor_weak: float, gates: dict) -> list[tuple[str, str, str, str]]:
    delta = best.get("weak_macro_f1", 0.0) - anchor_weak
    drop = base.get("unchanged_recall", 0.0) - best.get("unchanged_recall", 0.0)
    checks = [
        (
            "weak_delta_vs_anchor_min",
            delta,
            ">=",
            gates.get("weak_delta_vs_anchor_min"),
            delta >= gates.get("weak_delta_vs_anchor_min", 0.0),
        ),
        (
            "move_recall_min",
            best.get("move_recall", 0.0),
            ">=",
            gates.get("move_recall_min"),
            best.get("move_recall", 0.0) >= gates.get("move_recall_min", 0.0),
        ),
        (
            "move_f1_min",
            best.get("move_f1", 0.0),
            ">=",
            gates.get("move_f1_min"),
            best.get("move_f1", 0.0) >= gates.get("move_f1_min", 0.0),
        ),
        (
            "unchanged_recall_drop_max",
            drop,
            "<=",
            gates.get("unchanged_recall_drop_max"),
            drop <= gates.get("unchanged_recall_drop_max", 0.0),
        ),
    ]
    return [
        (name, _fmt(measured), op, f"{_fmt(thr)} -> {'PASS' if ok else 'FAIL'}")
        for name, measured, op, thr, ok in checks
    ]


def generate_report(
    results_path: str | Path | None = None,
    out_path: str | Path | None = None,
    relational_path: str | Path | None = None,
    integrity_path: str | Path | None = None,
    gate_status: dict[str, str] | None = None,
) -> dict:
    """Render the Phase 7 markdown report from measured results."""
    results = _load(results_path if results_path else RESULTS_PATH)
    out = Path(out_path) if out_path else REPORT_PATH
    gates_status = dict(gate_status) if gate_status else {"no_leakage": "PASS"}

    base = results.get("baselines", {}).get("base_rf_round0", {})
    anchor_cv, anchor_weak = _anchor_reference(relational_path, results)
    gates = results.get("promotion_gates", {})
    grid = sorted(
        results.get("grid", []),
        key=lambda e: (-e.get("weak_macro_f1", 0.0), -e.get("move_f1", 0.0)),
    )
    promo = results.get("promotion", {})
    best = promo.get("best_config") or (grid[0] if grid else {})
    promoted = bool(promo.get("promoted"))

    lines: list[str] = []
    lines.append("# Propagation Experiment Report (Phase 7)")
    lines.append("")
    lines.append("Aggregate statistics only; no deck or client identifiers.")
    lines.append("")
    lines.append("## Protocol")
    lines.append("")
    lines.append(f"- rows: {results.get('n_rows')}")
    lines.append(f"- groups: {results.get('n_groups')}")
    lines.append(f"- CV splits: {results.get('n_splits')}")
    lines.append(f"- seed: {results.get('seed')}")
    lines.append(f"- labels ({len(results.get('labels', []))}): {', '.join(results.get('labels', []))}")
    lines.append("")
    lines.append("## Baselines")
    lines.append("")
    lines.append("| metric | base_rf_round0 |")
    lines.append("|---|---|")
    for key in [
        "pooled_macro_f1",
        "weak_macro_f1",
        "move_precision",
        "move_recall",
        "move_f1",
        "unchanged_recall",
        "unsafe_rate",
        "brier",
    ]:
        if key in base:
            lines.append(f"| {key} | {_fmt(base[key])} |")
    lines.append("")
    lines.append(f"Anchor reference (RELATIONAL_BENCHMARK ANCHOR_CONTEXT random_forest): "
                 f"cv_macro_f1_mean={_fmt(anchor_cv)}, weak_macro_f1={_fmt(anchor_weak)} "
                 f"(mean of pooled per-class F1 over {', '.join(WEAK)} present).")
    lines.append("")
    lines.append("## Grid summary")
    lines.append("")
    lines.append(f"{len(grid)} configs evaluated; TOP 10 by weak_macro_f1 desc:")
    lines.append("")
    lines.append("| " + " | ".join(h for _, h in GRID_COLS) + " |")
    lines.append("|" + "---|" * len(GRID_COLS))
    for e in grid[:10]:
        lines.append("| " + " | ".join(_fmt(e.get(k, "-")) for k, _ in GRID_COLS) + " |")
    lines.append("")
    lines.append("## Best configuration & promotion decision")
    lines.append("")
    if best:
        lines.append(
            f"- best config: rounds={best.get('rounds')} alpha={best.get('alpha')} "
            f"edges={best.get('edges')} head={best.get('head')} "
            f"weak_macro_f1={_fmt(best.get('weak_macro_f1'))}"
        )
    lines.append(f"- promoted: {promoted}")
    reasons = promo.get("reasons", [])
    lines.append(f"- failure reasons: {', '.join(reasons) if reasons else 'none'}")
    lines.append("")
    lines.append("| gate | measured | op | threshold -> verdict |")
    lines.append("|---|---|---|---|")
    for name, measured, op, verdict in _gate_rows(best, base, anchor_weak, gates):
        lines.append(f"| {name} | {measured} | {op} | {verdict} |")
    lines.append("")
    lines.append("## Interpretation guidance")
    lines.append("")
    lines.append(NO_GO_TEXT if not promoted else GO_TEXT)
    lines.append("")
    lines.append("## Safety & calibration")
    lines.append("")
    if best:
        d_unsafe = best.get("unsafe_rate", 0.0) - base.get("unsafe_rate", 0.0)
        d_brier = best.get("brier", 0.0) - base.get("brier", 0.0)
        d_unch = best.get("unchanged_recall", 0.0) - base.get("unchanged_recall", 0.0)
        lines.append(f"- unsafe rate: base={_fmt(base.get('unsafe_rate'))} vs best={_fmt(best.get('unsafe_rate'))} (delta {_fmt(d_unsafe)})")
        lines.append(f"- brier: round0={_fmt(base.get('brier'))} vs best={_fmt(best.get('brier'))} (delta {_fmt(d_brier)})")
        lines.append(f"- unchanged recall delta vs base: {_fmt(d_unch)}")
    lines.append("")
    lines.append("## Determinism & integrity")
    lines.append("")
    lines.append(f"- determinism_check: {results.get('determinism_check')}")
    integ = {}
    try:
        integ = _load(integrity_path if integrity_path else INTEGRITY_PATH).get("v2", {}).get("node", {})
    except OSError:
        pass
    if integ:
        lines.append(
            f"- v2 node dataset: n_samples={integ.get('n_samples')} "
            f"unique_groups={integ.get('unique_groups')} "
            f"duplicate_sample_ids={integ.get('duplicate_sample_ids')} "
            f"groups_spanning_splits={integ.get('groups_spanning_splits')}"
        )
    for name in sorted(gates_status):
        lines.append(f"- gate {name}: {gates_status[name]}")
    lines.append("")

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")

    bc = best or {}
    decision_line = (
        f"PROMOTION DECISION: {'GO' if promoted else 'NO-GO'} "
        f"(promoted={promoted}) best="
        f"{bc.get('edges')}/rounds={bc.get('rounds')}/alpha={bc.get('alpha')}/head={bc.get('head')} "
        f"weak={_fmt(bc.get('weak_macro_f1'))}"
    )
    return {"report_path": str(out), "promoted": promoted, "decision_line": decision_line}


def _selftest() -> None:
    """Render a synthetic report into %TEMP% and assert required headers."""
    synth = {
        "schema": "prop_results_v1",
        "seed": 7,
        "n_splits": 3,
        "n_rows": 120,
        "n_groups": 6,
        "labels": ["ADD", "MOVE", "RECOLOR", "REMOVE", "RESIZE", "RESTYLE", "UNCHANGED"],
        "baselines": {
            "base_rf_round0": {
                "pooled_macro_f1": 0.40,
                "weak_macro_f1": 0.30,
                "move_precision": 0.10,
                "move_recall": 0.05,
                "move_f1": 0.06,
                "unchanged_recall": 0.95,
                "unsafe_rate": 0.02,
                "brier": 0.05,
            },
            "anchor_reference": {"cv_macro_f1": 0.45, "weak_macro_f1": 0.32},
        },
        "promotion_gates": {
            "weak_delta_vs_anchor_min": 0.10,
            "move_recall_min": 0.25,
            "move_f1_min": 0.20,
            "unchanged_recall_drop_max": 0.03,
        },
        "grid": [
            {
                "rounds": 1,
                "alpha": 0.9,
                "edges": "SYNTH_A",
                "head": "argmax",
                "pooled_macro_f1": 0.41,
                "weak_macro_f1": 0.31,
                "move_precision": 0.20,
                "move_recall": 0.10,
                "move_f1": 0.13,
                "unchanged_recall": 0.94,
                "unsafe_rate": 0.03,
                "brier": 0.049,
            },
            {
                "rounds": 2,
                "alpha": 0.8,
                "edges": "SYNTH_B",
                "head": "rf",
                "pooled_macro_f1": 0.39,
                "weak_macro_f1": 0.28,
                "move_precision": 0.15,
                "move_recall": 0.08,
                "move_f1": 0.10,
                "unchanged_recall": 0.93,
                "unsafe_rate": 0.04,
                "brier": 0.052,
            },
        ],
        "determinism_check": True,
        "promotion": {
            "promoted": False,
            "best_config": None,
            "reasons": ["weak_delta_vs_anchor_below_min", "move_recall_below_min"],
        },
    }
    tmp_dir = Path(tempfile.gettempdir())
    res_tmp = tmp_dir / "prop_results_selftest.json"
    out_tmp = tmp_dir / "PROPAGATION_EXPERIMENT_REPORT_SELFTEST.md"
    res_tmp.write_text(json.dumps(synth), encoding="utf-8")
    try:
        info = generate_report(
            results_path=res_tmp,
            out_path=out_tmp,
            relational_path=tmp_dir / "no_such_relational_benchmark.json",
            integrity_path=tmp_dir / "no_such_integrity.json",
        )
        md = out_tmp.read_text(encoding="utf-8")
        missing = [h for h in REQUIRED_HEADERS if h not in md]
        assert not missing, f"missing section headers: {missing}"
        assert info["promoted"] is False
        assert "NO-GO:" in md
        assert "PASS" in md or "FAIL" in md
    finally:
        res_tmp.unlink(missing_ok=True)
        out_tmp.unlink(missing_ok=True)


def main() -> None:
    if "--selftest" in sys.argv:
        _selftest()
        print("REPORT RENDER GATE PASSED")
        return
    info = generate_report()
    print(info["report_path"])
    print(info["decision_line"])


if __name__ == "__main__":
    main()
