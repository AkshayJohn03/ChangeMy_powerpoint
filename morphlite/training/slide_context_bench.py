"""Phase 9B benchmark harness (frozen contract).

Variants: A node-only | B slide-broadcast MUST | C node+all G1/G3 broadcast |
D node+G2 relative+G4 structural | E appendix (full-42 context).

Protocol: template-hash dedupe pre-pass -> StratifiedGroupKFold(k=5, seed=0,
groups=family) -> pooled metrics + displacement-weighted MOVE recall
(evaluation-only forensic join) -> two-tier gates.

    python -m morphlite.training.slide_context_bench [--skip-e]
"""
from __future__ import annotations

import json
from collections import Counter

import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score, precision_recall_fscore_support
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.tree import DecisionTreeClassifier

from .. import config
from .bench_classifiers import choose_folds
from .propagation import load_rows
from .slide_context import G2, G3, G4, G1, extract

WEAK = ["RESTYLE", "RESIZE", "REMOVE", "MOVE"]
ANCHOR_WEAK = 0.3568
ANCHOR_MOVE_RECALL = 0.1088
GATES = {
    "discovery_move_recall_delta": 0.05,
    "discovery_move_f1_delta": 0.05,
    "unchanged_recall_drop_max_vs_A": 0.03,
    "promotion_move_recall_min": 0.25,
    "promotion_move_f1_min": 0.20,
    "promotion_weak_delta_vs_anchor_min": 0.10,
}


def template_dedupe(rows: list[dict], fp_index: dict):
    """Contract pre-pass: when an exact-hash template cluster spans >1 family,
    keep only the lowest-token family's instances and drop the rest from ALL folds."""
    deck_of = {i: r["sample_id"].rsplit("__s", 1)[0] for i, r in enumerate(rows)}
    fam_of = {i: r["group"] for i, r in enumerate(rows)}

    hash_decks: dict[str, set[str]] = {}
    for did, entry in fp_index.items():
        h = entry.get("exact_hash")
        if h:
            hash_decks.setdefault(h, set()).add(did)

    mask = [True] * len(rows)
    excluded_rows = 0
    spanning = 0
    detail = []
    row_deck = [deck_of[i] for i in range(len(rows))]
    for h, decks in sorted(hash_decks.items()):
        fams = {fam_of[i] for i in range(len(rows)) if row_deck[i] in decks}
        if len(fams) <= 1:
            continue
        spanning += 1
        keep_family = min(fams)
        drop_fams = fams - {keep_family}
        removed_here = 0
        for i in range(len(rows)):
            if mask[i] and row_deck[i] in decks and fam_of[i] in drop_fams:
                mask[i] = False
                removed_here += 1
        excluded_rows += removed_here
        if removed_here:
            detail.append({"hash8": h[:8], "families": sorted(fams), "keep": keep_family, "rows_removed": removed_here})
    report = {
        "clusters_spanning_multiple_families": spanning,
        "rows_excluded": excluded_rows,
        "detail": detail,
        "note": "kept family = lowest token; excluded families dropped from ALL folds",
    }
    return mask, report


def _weighted_move_recall(y, pred, weights):
    m_true = y == "MOVE"
    hit = (pred == "MOVE") & m_true
    denom = float(weights[m_true].sum())
    return round(float(weights[hit].sum()) / max(denom, 1e-9), 4)


def main() -> None:
    skip_e = "--skip-e" in __import__("sys").argv
    rows = load_rows()
    ctx_names, X_ctx = extract(rows)
    base_names = sorted(rows[0]["base"].keys())
    X_base = np.array([[float(r["base"].get(k) or 0.0) for k in base_names] for r in rows])
    y = np.array([r["label"] for r in rows])
    groups = np.array([r["group"] for r in rows])

    fp_path = config.METADATA_DIR / "FINGERPRINT_INDEX.json"
    fp_index = json.loads(fp_path.read_text(encoding="utf-8"))
    mask, dedup_report = template_dedupe(rows, fp_index)
    kept_idx = np.array([i for i, m in enumerate(mask) if m])
    print(f"[dedupe] kept={int(mask.count(True))}/{len(rows)} excluded={dedup_report['rows_excluded']} "
          f"spanning_clusters={dedup_report['clusters_spanning_multiple_families']}", flush=True)

    Xb, yb, gb = X_base[kept_idx], y[kept_idx], groups[kept_idx]
    Cc = X_ctx[kept_idx]
    n_splits = choose_folds(yb, gb)
    sgkf = StratifiedGroupKFold(n_splits=n_splits, shuffle=True, random_state=0)
    folds = list(sgkf.split(Xb, yb, gb))

    bcol = {n: i for i, n in enumerate(ctx_names)}
    must_broadcast = ["n_xbands_log1p", "n_ybands_log1p", "grid_regularity_score",
                      "quad_occupied_count", "occ_col_frac_1"]
    g13_all = [n for n in ctx_names if n in set(G1) | set(G3)]
    spaces = {
        "A_node_only": Xb,
        "B_slide_broadcast_must": np.hstack([Xb, Cc[:, [bcol[n] for n in must_broadcast]]]),
        "C_node_plus_g1g3_broadcast": np.hstack([Xb, Cc[:, [bcol[n] for n in g13_all]]]),
        "D_node_plus_relative_structural": np.hstack([Xb, Cc[:, [bcol[n] for n in (G2 + G4)]]]),
    }
    if not skip_e:
        spaces["E_full_appendix"] = np.hstack([Xb, Cc])

    zoo = {
        "dummy": lambda: Dummy(),
        "decision_tree": lambda: DecisionTreeClassifier(max_depth=8, class_weight="balanced", random_state=0),
        "random_forest": lambda: RandomForestClassifier(n_estimators=300, min_samples_leaf=2, class_weight="balanced_subsample", random_state=0, n_jobs=-1),
        "hist_gbdt": lambda: HistGradientBoostingClassifier(max_depth=4, random_state=0),
    }

    rec_weight = {}
    with open(config.PAIRS_DIR / "transformation_records.jsonl", encoding="utf-8") as fh:
        for line in fh:
            r = json.loads(line)
            if r.get("kind") == "MORPH":
                g = r.get("geometry") or {}
                dx = abs((g.get("x") or {}).get("delta") or 0.0)
                dy = abs((g.get("y") or {}).get("delta") or 0.0)
                rec_weight[r["raw_node_id"]] = float(np.hypot(dx, dy))
    w_all = np.array([rec_weight.get(r["sample_id"], 0.0) for r in rows], dtype=float)[kept_idx]

    labels = sorted(set(yb))
    grid_results = []
    rf_by_space = {}
    rf_preds = {}
    for space_name, X in spaces.items():
        for mname, factory in zoo.items():
            pooled = np.empty(len(yb), dtype=object)
            fold_metrics = []
            for tr, te in folds:
                m = factory()
                m.fit(X[tr], yb[tr])
                p = m.predict(X[te])
                pooled[te] = p
                prf = precision_recall_fscore_support(yb[te], p, labels=labels, zero_division=0)
                mi = labels.index("MOVE") if "MOVE" in labels else None
                fold_metrics.append({
                    "move_recall": round(prf[1][mi], 4) if mi is not None else 0.0,
                    "macro_f1": round(f1_score(yb[te], p, average="macro", zero_division=0), 4),
                })
            prf = precision_recall_fscore_support(yb, pooled, labels=labels, zero_division=0)
            labs = labels
            mi = labs.index("MOVE") if "MOVE" in labs else None
            ui = labs.index("UNCHANGED") if "UNCHANGED" in labs else None
            weak_present = [l for l in WEAK if l in labs]
            wi = [labs.index(l) for l in weak_present]
            destructive = (pooled == "MOVE") | (pooled == "REMOVE")
            truth_destructive = (yb == "MOVE") | (yb == "REMOVE")
            entry = {
                "space": space_name, "model": mname,
                "macro_f1": round(f1_score(yb, pooled, average="macro", zero_division=0), 4),
                "weak_macro_f1": round(float(np.mean([prf[2][i] for i in wi])), 4) if wi else None,
                "move_precision": round(prf[0][mi], 4) if mi is not None else None,
                "move_recall": round(prf[1][mi], 4) if mi is not None else None,
                "move_f1": round(prf[2][mi], 4) if mi is not None else None,
                "unchanged_recall": round(prf[1][ui], 4) if ui is not None else None,
                "unsafe_rate": round(int((destructive & ~truth_destructive).sum()) / len(yb), 4),
                "pooled_accuracy": round(accuracy_score(yb, pooled), 4),
                "fold_move_recall_mean": round(float(np.mean([f["move_recall"] for f in fold_metrics])), 4),
                "fold_move_recall_std": round(float(np.std([f["move_recall"] for f in fold_metrics])), 4),
                "fold_macro_mean": round(float(np.mean([f["macro_f1"] for f in fold_metrics])), 4),
                "fold_macro_std": round(float(np.std([f["macro_f1"] for f in fold_metrics])), 4),
            }
            grid_results.append(entry)
            if mname == "random_forest":
                rf_by_space[space_name] = entry
                rf_preds[space_name] = pooled.copy()
            print(f"[{space_name}] {mname}: macro={entry['macro_f1']} weak={entry['weak_macro_f1']} "
                  f"moveR={entry['move_recall']} moveF1={entry['move_f1']} unchR={entry['unchanged_recall']}", flush=True)

    A = rf_by_space["A_node_only"]

    def deltas(e):
        return {
            "move_recall_delta_vs_A": round(e["move_recall"] - A["move_recall"], 4),
            "move_f1_delta_vs_A": round(e["move_f1"] - A["move_f1"], 4),
            "unchanged_recall_drop_vs_A": round(max(0.0, A["unchanged_recall"] - e["unchanged_recall"]), 4),
            "unsafe_rate_vs_A": round(e["unsafe_rate"] - A["unsafe_rate"], 4),
            "weak_delta_vs_anchor": round((e["weak_macro_f1"] or 0.0) - ANCHOR_WEAK, 4),
        }

    weighted = {
        sp: _weighted_move_recall(yb, rf_preds[sp], w_all) for sp in rf_preds
    }
    discovery_candidates = []
    promotion_candidates = []
    for sp in ("B_slide_broadcast_must", "C_node_plus_g1g3_broadcast",
               "D_node_plus_relative_structural"):
        if sp not in rf_by_space:
            continue
        e = dict(rf_by_space[sp])
        e.update(deltas(e))
        disc = (
            e["move_recall_delta_vs_A"] >= GATES["discovery_move_recall_delta"]
            or e["move_f1_delta_vs_A"] >= GATES["discovery_move_f1_delta"]
        ) and e["unchanged_recall_drop_vs_A"] <= GATES["unchanged_recall_drop_max_vs_A"] \
            and e["unsafe_rate_vs_A"] <= 0.0
        promo = (
            e["move_recall"] >= GATES["promotion_move_recall_min"]
            and e["move_f1"] >= GATES["promotion_move_f1_min"]
            and e["weak_delta_vs_anchor"] >= GATES["promotion_weak_delta_vs_anchor_min"]
            and e["unchanged_recall_drop_vs_A"] <= GATES["unchanged_recall_drop_max_vs_A"]
        )
        e["discovery_signal"] = disc
        e["promotion_pass"] = promo
        if disc:
            discovery_candidates.append(e)
        if promo:
            promotion_candidates.append(e)

    verdict = {
        "discovery_signal_found": bool(discovery_candidates),
        "candidates": discovery_candidates,
        "promotion_pass": bool(promotion_candidates),
        "note": "E_full excluded from verdict unless discovery gate explicitly permits (contract section 2)",
    }
    payload = {
        "schema": "phase9_context_results_v1",
        "n_rows_kept": int(len(yb)),
        "n_groups": int(len(set(gb))),
        "n_splits": n_splits,
        "dedup_report": dedup_report,
        "gates": GATES,
        "baselines": {"anchor_weak_macro_f1": ANCHOR_WEAK, "hybrid_seed_move_recall_ref": ANCHOR_MOVE_RECALL},
        "results": {"rf_by_space": rf_by_space, "grid": grid_results},
        "verdict": verdict,
    }
    out = config.METADATA_DIR / "PHASE_9_CONTEXT_RESULTS.json"
    out.write_text(json.dumps(payload, indent=1), encoding="utf-8")

    md = [
        "# Phase 9 - Slide Context Benchmark (A/B/C/D/E)",
        "",
        f"Rows post-dedupe: {len(yb)} | Groups: {payload['n_groups']} | Folds: {n_splits} | Excluded by dedupe: {dedup_report['rows_excluded']}",
        "",
        "| Space | macro | weak | MOVE P | MOVE R | MOVE F1 | UNCH R | unsafe | disp-wtd R |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for sp, e in rf_by_space.items():
        wr = _weighted_move_recall(yb, None, None) if False else None
        md.append(f"| {sp} | {e['macro_f1']} | {e['weak_macro_f1']} | {e['move_precision']} | {e['move_recall']} | {e['move_f1']} | {e['unchanged_recall']} | {e['unsafe_rate']} | see json |")
    md += ["", f"**Discovery signal:** {verdict['discovery_signal_found']}",
           f"**Promotion pass:** {verdict['promotion_pass']}",
           "", "Displacement-weighted MOVE recall (evaluation-only join): "
           + "; ".join(f"{sp}: {weighted[sp]}" for sp in sorted(weighted)),
           "Deltas (RF): " + "; ".join(f"{sp}: {deltas(e)}" for sp, e in
                                        ((sp, rf_by_space[sp]) for sp in rf_by_space if sp != 'A_node_only'))]
    (config.METADATA_DIR / "PHASE_9_EXPERIMENT_REPORT.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    print(json.dumps(verdict, indent=1))


def Dummy():
    from sklearn.dummy import DummyClassifier

    return DummyClassifier(strategy="most_frequent")


if __name__ == "__main__":
    main()
