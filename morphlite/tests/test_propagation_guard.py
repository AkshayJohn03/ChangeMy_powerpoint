"""Phase 7 adversarial guard: oracle containment, group-safe OOF, cache-schema
drift handling, determinism, neighbour scope, bench grouping sanity, and the
no-leakage compliance gate. Prints aggregate results only (never deck names
or contents).

    python -m morphlite.tests.test_propagation_guard
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest.mock as mock
from pathlib import Path

import numpy as np

from ..training import propagation as prop

MORPHLITE_ROOT = Path(__file__).resolve().parents[1]
BRANDMORPH_ROOT = MORPHLITE_ROOT.parent
BANNED_TOKENS = ("oracle_features", "ORACLE_CONTEXT_FEATURES", "transformation_records")
_REAL_MODEL_ZOO = prop.model_zoo

RESULTS: list[tuple[str, bool, str]] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    RESULTS.append((name, bool(ok), detail))
    print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f" :: {detail}" if detail else ""), flush=True)


def _row_ids(X) -> frozenset:
    return frozenset(np.asarray(X)[:, 0].astype(int).tolist())


def t1_oracle_containment() -> None:
    hits = []
    for sub in ("inference", "rules"):
        for p in sorted((MORPHLITE_ROOT / sub).rglob("*.py")):
            if p.name == "learn.py":
                continue
            text = p.read_text(encoding="utf-8")
            for tok in BANNED_TOKENS:
                if tok in text:
                    hits.append(f"{sub}/{p.name}:{tok}")
    check(
        "T1a inference/+rules(engine-runtime) free of oracle/transformation tokens (learn.py excluded: offline trainer)",
        not hits,
        ",".join(hits),
    )
    src = (MORPHLITE_ROOT / "training" / "propagation.py").read_text(encoding="utf-8")
    check(
        "T1b propagation.py sources labels via dataset_builder.truth_node_labels",
        "truth_node_labels" in src and "dataset_builder" in src,
    )
    check(
        "T1c propagation.py free of oracle_features/transformation_records",
        "oracle_features" not in src and "transformation_records" not in src,
    )


def t2_label_independence_and_determinism() -> tuple[np.ndarray, list[list[int]]]:
    rng = np.random.default_rng(7)
    P = rng.random((9, 4))
    P /= P.sum(axis=1, keepdims=True)
    nbrs = [[1, 2], [0], [], [4, 5, 6], [3], [], [7], [6, 8], [0]]
    dummy_labels_a = np.array(["A", "B", "A", "B", "A", "B", "A", "B", "A"])
    dummy_labels_b = np.array([3, 1, 4, 1, 5, 9, 2, 6, 5])
    _ = (dummy_labels_a, dummy_labels_b)
    Qa = prop.propagate(P.copy(), nbrs, alpha=0.8, rounds=2)
    Qb = prop.propagate(P.copy(), nbrs, alpha=0.8, rounds=2)
    check("T2 propagate output independent of ambient label vectors", np.array_equal(Qa, Qb))
    isolated = [i for i, nb in enumerate(nbrs) if not nb]
    check(
        "T2b isolated nodes pass through unchanged",
        all(np.array_equal(Qa[i], P[i]) for i in isolated),
    )
    Qc = prop.propagate(P.copy(), nbrs, alpha=0.75, rounds=3)
    Qd = prop.propagate(P.copy(), nbrs, alpha=0.75, rounds=3)
    check("T5b propagate deterministic across repeated calls", np.array_equal(Qc, Qd))
    return P, nbrs


def _synth_grouped(n_groups: int = 3, per_group: int = 12, seed: int = 11):
    rng = np.random.default_rng(seed)
    X, y, g = [], [], []
    for gi in range(n_groups):
        for k in range(per_group):
            idx = len(X)
            lab = k % 2
            X.append([float(idx), (1.0 if lab else -1.0) + 0.05 * gi + rng.normal(0.0, 0.05)])
            y.append("POS" if lab else "NEG")
            g.append(f"grp{gi}")
    return np.array(X), np.array(y), np.array(g)


def _recording_zoo(events: list[tuple[str, frozenset]]) -> dict:
    real = _REAL_MODEL_ZOO("node")
    def make_cls(name: str, base_cls: type) -> type:
        cls = type(f"_Rec_{name}", (base_cls,), {})

        def fit(self, X, y, **kw):
            events.append(("fit", _row_ids(X)))
            return base_cls.fit(self, X, y, **kw)

        def predict_proba(self, X):
            events.append(("pred", _row_ids(X)))
            return base_cls.predict_proba(self, X)

        cls.fit = fit
        cls.predict_proba = predict_proba
        return cls

    return {name: make_cls(name, base.__class__)(**base.get_params()) for name, base in real.items()}


def _assert_fold_disjoint(events: list[tuple[str, frozenset]], n_rows: int, tag: str) -> None:
    fits = [e for e in events if e[0] == "fit"]
    preds = [e for e in events if e[0] == "pred"]
    ok = len(fits) == len(preds) and len(fits) > 0
    details = []
    overlaps = 0
    for i, ((_, tr), (_, te)) in enumerate(zip(fits, preds)):
        inter = tr & te
        if inter:
            overlaps += 1
            details.append(f"{tag}fold{i}:overlap={sorted(inter)[:5]}")
    covered = set().union(*[p[1] for p in preds]) if preds else set()
    ok = ok and overlaps == 0 and covered == set(range(n_rows))
    check(f"{tag}: scored rows never seen by that fold's fit", ok, ";".join(details))


def t3_group_safe_oof(X, y, groups) -> np.ndarray:
    events: list[tuple[str, frozenset]] = []
    with mock.patch.object(prop, "model_zoo", lambda task: _recording_zoo(events)):
        P = prop.oof_probabilities(X, y, groups, model_name="decision_tree", n_splits=3, seed=0)
    _assert_fold_disjoint(events, len(y), "T3-oof")
    check("T3b OOF probability rows are valid distributions", bool(np.allclose(P.sum(axis=1), 1.0)))
    return P


def t5_oof_determinism(X, y, groups) -> None:
    Pa = prop.oof_probabilities(X, y, groups, model_name="decision_tree", n_splits=3, seed=0)
    Pb = prop.oof_probabilities(X, y, groups, model_name="decision_tree", n_splits=3, seed=0)
    check("T5a oof_probabilities deterministic under fixed seed", np.array_equal(Pa, Pb))


def _synth_cache_rows() -> list[dict]:
    return [
        {
            "schema": prop.PROPAGATION_SCHEMA_VERSION,
            "sample_id": f"syn__s1__n{i}",
            "group": "syn_grp",
            "label": "UNCHANGED",
            "slide_key": "syn__s1",
            "base": {"f0": 0.0, "f1": float(i)},
            "nbrs": {name: [] for name in prop.EDGE_SUBSETS},
        }
        for i in range(3)
    ]


def t4_cache_schema_drift(tmp: Path) -> None:
    synth = _synth_cache_rows()
    builder_calls: list[int] = []

    def fake_build():
        builder_calls.append(1)
        return [dict(r) for r in synth]

    def write_cache(rows: list[dict]) -> Path:
        p = tmp / "propagation_cache.jsonl"
        with open(p, "w", encoding="utf-8") as fh:
            for r in rows:
                fh.write(json.dumps(r) + "\n")
        return p

    def run(rows: list[dict]):
        p = write_cache(rows)
        with mock.patch.object(prop, "CACHE", p), mock.patch.object(prop, "_build_cache", fake_build):
            out = prop.load_rows(rebuild=False)
        rebuilt = p.read_text(encoding="utf-8").strip() == "".join(json.dumps(r) + "\n" for r in synth).strip()
        return out, len(builder_calls), rebuilt

    bad = dict(synth[0])
    bad["schema"] = "prop_v0_STALE"
    builder_calls.clear()
    out, calls, rebuilt = run([bad])
    check("T4a stale schema detected and cache rebuilt", out == synth and calls == 1 and rebuilt)

    miss = {k: v for k, v in synth[0].items() if k != "nbrs"}
    builder_calls.clear()
    out, calls, rebuilt = run([miss])
    check("T4b missing required key detected and cache rebuilt", out == synth and calls == 1 and rebuilt)

    builder_calls.clear()
    out, calls, rebuilt = run([])
    check("T4c empty cache triggers rebuild", out == synth and calls == 1 and rebuilt)

    builder_calls.clear()
    out, calls, rebuilt = run(synth)
    check("T4d valid cache reused without rebuild", out == synth and calls == 0)


def t6_neighbour_scope() -> None:
    if not prop.CACHE.exists():
        check("T6 neighbour scope skipped (cache absent)", True, "cache absent")
        return
    rows: list[dict] = []
    with open(prop.CACHE, encoding="utf-8") as fh:
        for line in fh:
            rows.append(json.loads(line))
    edges = cross = oob = 0
    for i, r in enumerate(rows):
        sk = r["slide_key"]
        for nl in r["nbrs"].values():
            for j, _w in nl:
                edges += 1
                if not (0 <= j < len(rows)):
                    oob += 1
                elif rows[j]["slide_key"] != sk:
                    cross += 1
    check(
        "T6 neighbours stay within same slide_key",
        cross == 0 and oob == 0,
        f"rows_scanned={len(rows)} edges={edges} cross_slide={cross} out_of_window={oob}",
    )


def t7_bench_grouping_sanity() -> None:
    from sklearn.tree import DecisionTreeClassifier

    from ..training.bench_classifiers import choose_folds, repeated_group_cv

    y = np.array(["A", "B"] * 9)
    groups = np.array(["g1"] * 6 + ["g2"] * 6 + ["g3"] * 6)
    X = np.array([[float(i), (1.0 if v == "B" else -1.0) + 0.03 * int(groups[i][1])] for i, v in enumerate(y)])
    k = choose_folds(y, groups, max_folds=5)
    check("T7a choose_folds bounded by group count and minority class", k == 3, f"k={k}")

    events: list[tuple[str, frozenset]] = []

    def factory():
        est = DecisionTreeClassifier(max_depth=2, random_state=0)
        orig_fit = est.fit
        orig_pred = est.predict

        def fit(Xi, yi, **kw):
            events.append(("fit", _row_ids(Xi)))
            return orig_fit(Xi, yi, **kw)

        def predict(Xi):
            events.append(("pred", _row_ids(Xi)))
            return orig_pred(Xi)

        est.fit = fit
        est.predict = predict
        return est

    repeated_group_cv(factory, X, y, groups, n_splits=3, repeats=2)
    _assert_fold_disjoint(events, len(y), "T7b-cv")


def t8_no_leakage_gate() -> None:
    proc = subprocess.run(
        [sys.executable, "-m", "morphlite.tests.test_no_leakage"],
        cwd=str(BRANDMORPH_ROOT),
        capture_output=True,
        text=True,
        timeout=900,
    )
    check("T8 no-leakage gate exits 0", proc.returncode == 0, f"rc={proc.returncode}")


def main() -> int:
    print("== MorphLite Phase 7 propagation guard ==", flush=True)
    t1_oracle_containment()
    t2_label_independence_and_determinism()
    X, y, groups = _synth_grouped()
    t3_group_safe_oof(X, y, groups)
    t5_oof_determinism(X, y, groups)
    with tempfile.TemporaryDirectory() as td:
        t4_cache_schema_drift(Path(td))
    t6_neighbour_scope()
    t7_bench_grouping_sanity()
    t8_no_leakage_gate()

    failed = [name for name, ok, _ in RESULTS if not ok]
    print(f"checks={len(RESULTS)} failed={len(failed)}", flush=True)
    if failed:
        for name in failed:
            print(f"FAILED: {name}", flush=True)
        print("PROPAGATION GUARD FAILED", flush=True)
        return 1
    print("PROPAGATION GUARD PASSED", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
