"""Phase 7: label-propagation over the slide dependency graph.

Builds a propagation cache (V2 features + per-subset graph neighbourhoods),
computes grouped-OOF probabilities for the base node classifier, smooths them
over the graph (personalized-PageRank style), and benchmarks argmax vs
meta-model heads against the round-0 baseline and the ANCHOR_CONTEXT reference.

    python -m morphlite.training.propagation [--rebuild-cache]
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
from sklearn.base import clone
from sklearn.metrics import f1_score
from sklearn.model_selection import StratifiedGroupKFold

from .. import config
from ..features.node_features_v2 import FEATURE_NAMES_V2
from .bench_classifiers import model_zoo
from .dataset_builder import label_from_tags, load_json, truth_node_labels

PROPAGATION_SCHEMA_VERSION = "prop_v1"
LABELS = ["ADD", "MOVE", "RECOLOR", "REMOVE", "RESIZE", "RESTYLE", "UNCHANGED"]
EDGE_SUBSETS = {
    "ALIGNMENT": {"LEFT_ALIGNED", "RIGHT_ALIGNED", "TOP_ALIGNED", "BOTTOM_ALIGNED"},
    "CONTAINMENT": {"CONTAINS", "OVERLAPS"},
    "GROUP": {"SAME_GROUP"},
    "ALL": None,
}
WEAK = ["RESTYLE", "RESIZE", "REMOVE", "MOVE"]
ALPHAS = (0.9, 0.8, 0.7, 0.6)
ROUNDS = (1, 2, 3)
META_HEADS = (("dt", "decision_tree"), ("rf", "random_forest"), ("hgb", "hist_gbdt"))

CACHE = config.DATA_DIR / "processed" / "propagation_cache.jsonl"
RESULTS_PATH = config.METADATA_DIR / "PROPAGATION_RESULTS.json"
ROW_KEYS = {"schema", "sample_id", "group", "label", "slide_key", "base", "nbrs"}
GATES = {
    "weak_delta_vs_anchor_min": 0.10,
    "move_recall_min": 0.25,
    "move_f1_min": 0.20,
    "unchanged_recall_drop_max": 0.03,
}


# --------------------------------------------------------------------------- #
# cache builder
# --------------------------------------------------------------------------- #
def _build_cache() -> list[dict]:
    from ..ast import extractor
    from ..features.node_features_v2 import extract_slide_node_features_v2
    from ..graph.builder import build_slide_graph

    paths: dict[str, str] = {}
    with open(config.EXTRACTED_DIR / "ast_v2" / "extraction_manifest_v2.jsonl", encoding="utf-8") as fh:
        for line in fh:
            rec = json.loads(line)
            paths[rec["deck_id"]] = rec["ast_v2_path"]

    truth = truth_node_labels()
    rows: list[dict] = []
    n_pairs = n_skipped = n_slides = 0

    with open(config.PAIRS_DIR / "validated_pairs.jsonl", encoding="utf-8") as fh:
        pairs = [json.loads(line) for line in fh]

    for v in pairs:
        deck_id = v["raw_deck"]
        if deck_id not in paths:
            n_skipped += 1
            continue
        deck = load_json(Path(paths[deck_id]))
        group = v["name_key"] or deck_id
        pending: list[tuple[list[dict], dict[str, dict[int, list[int]]]]] = []

        for sm in v["slide_mappings"]:
            ri = int(sm["raw_slide_id"].rsplit("__s", 1)[1]) - 1
            slide = deck["slides"][ri]
            graph = build_slide_graph(slide, deck_id=deck_id)
            feats = extract_slide_node_features_v2(slide)
            ids = [nd["id"] for nd in extractor.flatten_nodes(slide["nodes"])]
            local = {nid: i for i, nid in enumerate(ids)}

            adj: dict[str, dict[int, set[int]]] = {name: {} for name in EDGE_SUBSETS}
            for e in graph["edges"]:
                etype = e["type"]
                s = local.get(e["src"])
                d = local.get(e["dst"])
                if s is None or d is None:
                    continue
                for name, types in EDGE_SUBSETS.items():
                    if types is None or etype in types:
                        adj[name].setdefault(s, set()).add(d)

            staged = []
            for i, nid in enumerate(ids):
                entry = truth.get(nid)
                staged.append(
                    {
                        "schema": PROPAGATION_SCHEMA_VERSION,
                        "sample_id": nid,
                        "group": group,
                        "label": label_from_tags(entry["tags"]) if entry else "UNCHANGED",
                        "slide_key": nid.rsplit("__n", 1)[0],
                        "base": feats[i],
                    }
                )
            pending.append((staged, adj))
            n_slides += 1

        for staged, adj in pending:
            offset = len(rows)
            for i, row in enumerate(staged):
                row["nbrs"] = {
                    name: [[offset + j, 1.0] for j in sorted(nb.get(i, ()))]
                    for name, nb in adj.items()
                }
                rows.append(row)
        n_pairs += 1

    print(f"[propagation] cache built: {n_pairs} pairs ({n_skipped} skipped), {n_slides} slides, {len(rows)} rows", flush=True)
    return rows


def load_rows(rebuild: bool = False) -> list[dict]:
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    if CACHE.exists() and not rebuild:
        rows = [json.loads(line) for line in open(CACHE, encoding="utf-8")]

        def _valid(row) -> bool:
            return (
                isinstance(row, dict)
                and ROW_KEYS <= set(row)
                and row.get("schema") == PROPAGATION_SCHEMA_VERSION
                and row.get("label") in LABELS
                and isinstance(row.get("nbrs"), dict)
                and set(row["nbrs"]) == set(EDGE_SUBSETS)
            )

        if rows and all(_valid(r) for r in rows):
            return rows
        print("propagation cache schema drift -> rebuilding", flush=True)

    rows = _build_cache()
    with open(CACHE, "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    return rows


# --------------------------------------------------------------------------- #
# OOF probabilities
# --------------------------------------------------------------------------- #
def oof_probabilities(
    X: np.ndarray,
    y: np.ndarray,
    groups: np.ndarray,
    model_name: str = "random_forest",
    n_splits: int = 5,
    seed: int = 0,
) -> np.ndarray:
    classes = np.array(sorted(set(y)))
    col_of = {c: i for i, c in enumerate(classes)}
    P = np.zeros((len(y), len(classes)), dtype=float)
    filled = np.zeros(len(y), dtype=int)
    sgkf = StratifiedGroupKFold(n_splits=n_splits, shuffle=True, random_state=seed)
    for tr, te in sgkf.split(X, y, groups):
        clf = clone(model_zoo("node")[model_name])
        clf.fit(X[tr], y[tr])
        proba = clf.predict_proba(X[te])
        cols = [col_of[c] for c in clf.classes_]
        P[np.asarray(te)[:, None], np.asarray(cols)[None, :]] = proba
        filled[te] += 1
    assert (filled == 1).all(), "OOF assembly left unfilled/duplicated rows"
    return P


# --------------------------------------------------------------------------- #
# propagation
# --------------------------------------------------------------------------- #
def _flatten_nbrs(nbrs) -> tuple[np.ndarray, np.ndarray]:
    indptr = [0]
    indices: list[int] = []
    for nb in nbrs:
        arr = np.asarray(nb, dtype=np.int64).ravel()
        indices.extend(arr.tolist())
        indptr.append(len(indices))
    return np.asarray(indptr, dtype=np.int64), np.asarray(indices, dtype=np.int64)


def _neighbour_mean(P: np.ndarray, indptr: np.ndarray, indices: np.ndarray) -> np.ndarray:
    n = P.shape[0]
    counts = np.diff(indptr)
    out = np.zeros_like(P)
    if indices.size == 0:
        return out
    rows = np.repeat(np.arange(n, dtype=np.int64), counts)
    denom = np.maximum(counts, 1).astype(float)
    for c in range(P.shape[1]):
        sums = np.bincount(rows, weights=P[indices, c], minlength=n)
        out[:, c] = sums / denom
    return out


def propagate(P: np.ndarray, nbrs, alpha: float, rounds: int) -> np.ndarray:
    indptr, indices = _flatten_nbrs(nbrs)
    has_nbr = np.diff(indptr) > 0
    Q = np.asarray(P, dtype=float).copy()
    for _ in range(int(rounds)):
        upd = alpha * Q + (1.0 - alpha) * _neighbour_mean(Q, indptr, indices)
        Q = np.where(has_nbr[:, None], upd, Q)
    return Q


# --------------------------------------------------------------------------- #
# meta features
# --------------------------------------------------------------------------- #
def meta_features(P_self: np.ndarray, P_nbr_r1: np.ndarray, P_nbr_r2: np.ndarray) -> np.ndarray:
    P_self = np.asarray(P_self, dtype=float)
    r1 = np.asarray(P_nbr_r1, dtype=float)
    r2 = np.asarray(P_nbr_r2, dtype=float)
    pos = np.clip(r2, 1e-12, None)
    entropy = -(pos * np.log(pos)).sum(axis=1, keepdims=True)
    blocks = [P_self, r1, r2, r1 - P_self, r2 - P_self, np.max(r2, axis=1, keepdims=True), entropy]
    return np.hstack(blocks)


# --------------------------------------------------------------------------- #
# metrics
# --------------------------------------------------------------------------- #
def _pooled_metrics(y: np.ndarray, pred: np.ndarray, probs: np.ndarray) -> dict:
    n = len(y)
    classes = np.array(sorted(set(y)))
    col_of = {c: i for i, c in enumerate(classes)}
    y_idx = np.array([col_of[v] for v in y])

    macro = f1_score(y, pred, average="macro", zero_division=0)
    per_f1 = {lab: f1_score(y == lab, pred == lab, zero_division=0) for lab in classes}
    weak_present = [k for k in WEAK if k in per_f1]
    weak_macro = sum(per_f1[k] for k in weak_present) / max(len(weak_present), 1)

    m_true, m_pred = y == "MOVE", pred == "MOVE"
    tp = int((m_true & m_pred).sum())
    move_prec = tp / max(int(m_pred.sum()), 1)
    move_rec = tp / max(int(m_true.sum()), 1)
    move_f1 = 2 * move_prec * move_rec / max(move_prec + move_rec, 1e-12)

    u_true = y == "UNCHANGED"
    unchanged_rec = float(((pred == "UNCHANGED") & u_true).sum() / max(int(u_true.sum()), 1))

    unsafe = int(((pred == "MOVE") & ~m_true).sum() + ((pred == "REMOVE") & (y != "REMOVE")).sum()) / max(n, 1)

    Y = np.zeros_like(np.asarray(probs, dtype=float))
    Y[np.arange(n), y_idx] = 1.0
    brier = float(np.mean((np.asarray(probs, dtype=float) - Y) ** 2))

    return {
        "pooled_macro_f1": round(float(macro), 4),
        "weak_macro_f1": round(float(weak_macro), 4),
        "move_precision": round(float(move_prec), 4),
        "move_recall": round(float(move_rec), 4),
        "move_f1": round(float(move_f1), 4),
        "unchanged_recall": round(float(unchanged_rec), 4),
        "unsafe_rate": round(float(unsafe), 4),
        "brier": round(brier, 6),
    }


def _fold_probs(preds: np.ndarray, proba_rows: list[tuple[np.ndarray, np.ndarray]], classes: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    col_of = {c: i for i, c in enumerate(classes)}
    P = np.zeros((len(preds), len(classes)), dtype=float)
    for te, proba, cls in proba_rows:
        if proba is None:
            for k, lab in zip(te, preds[te]):
                P[k, col_of[lab]] = 1.0
            continue
        cols = [col_of[c] for c in cls]
        P[np.asarray(te)[:, None], np.asarray(cols)[None, :]] = proba
    return P


def _leave_fold_out(M: np.ndarray, y: np.ndarray, groups: np.ndarray, model_name: str, seed: int) -> tuple[np.ndarray, np.ndarray]:
    classes = np.array(sorted(set(y)))
    preds = np.empty(len(y), dtype=y.dtype)
    proba_rows: list[tuple[np.ndarray, np.ndarray | None, np.ndarray]] = []
    sgkf = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=seed)
    for tr, te in sgkf.split(M, y, groups):
        clf = clone(model_zoo("node")[model_name])
        clf.fit(M[tr], y[tr])
        preds[te] = clf.predict(M[te])
        proba = clf.predict_proba(M[te]) if hasattr(clf, "predict_proba") else None
        proba_rows.append((te, proba, np.asarray(clf.classes_)))
    P = _fold_probs(preds, proba_rows, classes)
    return preds, P


# --------------------------------------------------------------------------- #
# main
# --------------------------------------------------------------------------- #
def main() -> None:
    t0 = time.time()
    rebuild = "--rebuild-cache" in sys.argv
    rows = load_rows(rebuild=rebuild)

    X = np.array([[float(r["base"].get(f) or 0.0) for f in FEATURE_NAMES_V2] for r in rows], dtype=float)
    y = np.array([r["label"] for r in rows])
    groups = np.array([r["group"] for r in rows])

    nbr_lists = {}
    for name in EDGE_SUBSETS:
        nbr_lists[name] = [
            np.array([int(j) for j, _w in r["nbrs"][name]], dtype=np.int64) for r in rows
        ]

    P_oof = oof_probabilities(X, y, groups, seed=0)
    classes = np.array(sorted(set(y)))
    base_pred = classes[np.argmax(P_oof, axis=1)]
    base = _pooled_metrics(y, base_pred, P_oof)
    print(f"[baseline] round0 rf-oof weak={base['weak_macro_f1']:.3f} moveR={base['move_recall']:.3f} moveF1={base['move_f1']:.3f} macro={base['pooled_macro_f1']:.3f}", flush=True)

    rel = json.loads((config.METADATA_DIR / "RELATIONAL_BENCHMARK.json").read_text(encoding="utf-8"))
    anchor_rf = rel["results"]["ANCHOR_CONTEXT"]["random_forest"]
    anchor_per = anchor_rf["pooled_per_class_f1"]
    anchor_weak = round(sum(anchor_per[k] for k in WEAK if k in anchor_per) / max(len([k for k in WEAK if k in anchor_per]), 1), 4)
    anchor_ref = {"cv_macro_f1": anchor_rf["cv_macro_f1_mean"], "weak_macro_f1": anchor_weak}

    meta_cache: dict[tuple[str, float], dict[str, tuple[np.ndarray, np.ndarray]]] = {}
    for edges in EDGE_SUBSETS:
        nbrs = nbr_lists[edges]
        for alpha in ALPHAS:
            P1 = propagate(P_oof, nbrs, alpha, 1)
            P2 = propagate(P_oof, nbrs, alpha, 2)
            M = meta_features(P_oof, _neighbour_mean(P1, *_flatten_nbrs(nbrs)), _neighbour_mean(P2, *_flatten_nbrs(nbrs)))
            meta_cache[(edges, alpha)] = {
                head: _leave_fold_out(M, y, groups, mname, seed=0) for head, mname in META_HEADS
            }

    grid: list[dict] = []
    for edges in EDGE_SUBSETS:
        nbrs = nbr_lists[edges]
        for rounds in ROUNDS:
            for alpha in ALPHAS:
                P_prop = propagate(P_oof, nbrs, alpha, rounds)
                pred = classes[np.argmax(P_prop, axis=1)]
                entry = {"rounds": rounds, "alpha": alpha, "edges": edges, "head": "argmax", **_pooled_metrics(y, pred, P_prop)}
                grid.append(entry)
                print(f"[grid] edges={edges:11s} rounds={rounds} alpha={alpha:.2f} head=argmax weak={entry['weak_macro_f1']:.3f} moveR={entry['move_recall']:.3f} moveF1={entry['move_f1']:.3f} macro={entry['pooled_macro_f1']:.3f}", flush=True)
                for head, (mpred, mproba) in meta_cache[(edges, alpha)].items():
                    entry = {"rounds": rounds, "alpha": alpha, "edges": edges, "head": head, **_pooled_metrics(y, mpred, mproba)}
                    grid.append(entry)
                    print(f"[grid] edges={edges:11s} rounds={rounds} alpha={alpha:.2f} head={head:6s} weak={entry['weak_macro_f1']:.3f} moveR={entry['move_recall']:.3f} moveF1={entry['move_f1']:.3f} macro={entry['pooled_macro_f1']:.3f}", flush=True)

    Pa = oof_probabilities(X, y, groups, seed=0)
    Pb = oof_probabilities(X, y, groups, seed=0)
    det = bool(np.array_equal(
        np.round(propagate(Pa, nbr_lists["ALL"], 0.8, 2), 10),
        np.round(propagate(Pb, nbr_lists["ALL"], 0.8, 2), 10),
    ))

    def gate_reasons(e: dict) -> list[str]:
        rs = []
        if e["weak_macro_f1"] < anchor_weak + GATES["weak_delta_vs_anchor_min"]:
            rs.append("weak_delta_vs_anchor_below_min")
        if e["move_recall"] < GATES["move_recall_min"]:
            rs.append("move_recall_below_min")
        if e["move_f1"] < GATES["move_f1_min"]:
            rs.append("move_f1_below_min")
        if e["unchanged_recall"] < base["unchanged_recall"] - GATES["unchanged_recall_drop_max"]:
            rs.append("unchanged_recall_drop_exceeds_max")
        if e["unsafe_rate"] > base["unsafe_rate"]:
            rs.append("unsafe_rate_above_base")
        return rs

    passing = [e for e in grid if not gate_reasons(e)]
    pool = passing if passing else grid
    best = max(pool, key=lambda e: (e["weak_macro_f1"], e["move_f1"]))
    promotion = {"promoted": bool(passing), "best_config": best, "reasons": [] if passing else gate_reasons(best)}

    payload = {
        "schema": "prop_results_v1",
        "seed": 0,
        "n_splits": 5,
        "n_rows": len(rows),
        "n_groups": int(len(set(groups))),
        "labels": LABELS,
        "baselines": {"base_rf_round0": base, "anchor_reference": anchor_ref},
        "promotion_gates": GATES,
        "grid": grid,
        "determinism_check": det,
        "promotion": promotion,
    }
    RESULTS_PATH.write_text(json.dumps(payload, indent=1), encoding="utf-8")

    bc = promotion["best_config"]
    print(
        f"[summary] rows={len(rows)} groups={payload['n_groups']} configs={len(grid)} determinism={det}",
        flush=True,
    )
    print(
        f"[summary] best edges={bc['edges']} rounds={bc['rounds']} alpha={bc['alpha']} head={bc['head']} "
        f"weak={bc['weak_macro_f1']:.3f} moveR={bc['move_recall']:.3f} moveF1={bc['move_f1']:.3f} promoted={promotion['promoted']}",
        flush=True,
    )
    if promotion["reasons"]:
        print(f"[summary] gate failures: {','.join(promotion['reasons'])}", flush=True)
    print(f"[summary] runtime_s={time.time() - t0:.1f}", flush=True)


if __name__ == "__main__":
    main()
