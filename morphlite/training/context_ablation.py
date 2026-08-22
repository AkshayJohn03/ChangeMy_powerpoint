"""Phase 8.6/8.7: context representation ablation and conditional ambiguity test.

Feature spaces (all deployable, raw-side only):
    A  node features (V2)
    B  node + slide composition context
    C  node + local graph aggregates
    D  node + local + slide context

    python -m morphlite.training.context_ablation
"""
from __future__ import annotations

import json
import math
from collections import Counter

import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score, precision_recall_fscore_support
from sklearn.model_selection import StratifiedGroupKFold

from .. import config
from .bench_classifiers import choose_folds
from .propagation import load_rows

WEAK = ["RESTYLE", "RESIZE", "REMOVE", "MOVE"]
KNN_K = 10


def _entropy(counts) -> float:
    total = sum(counts)
    if total == 0:
        return 0.0
    h = 0.0
    for c in counts:
        if c:
            p = c / total
            h -= p * math.log2(p)
    return round(h, 4)


def _mean(v):
    return float(np.mean(v)) if v else 0.0


def _pstd(v):
    return float(np.std(v)) if len(v) > 1 else 0.0


def slide_context(members_base: list[dict]) -> dict:
    n = len(members_base)

    def col(key):
        return [float(b.get(key) or 0.0) for b in members_base]

    cx, cy = col("cx"), col("cy")
    xs, ws = col("x"), col("w")
    ys, hs = col("y"), col("h")
    area, eff, tlen = col("area_log1p"), col("eff_size_pt"), col("text_len_log1p")
    ovl = col("overlap_frac_max")

    x_span = max(x + w for x, w in zip(xs, ws)) - min(xs) if xs else 0.0
    y_span = max(y + h for y, h in zip(ys, hs)) - min(ys) if ys else 0.0
    occupied = min(sum(w * h for w, h in zip(ws, hs)), 1.0)
    gx = Counter(int(c * 24) for c in cx)
    gy = Counter(int(c * 24) for c in cy)

    out = {
        "n_log1p": math.log1p(n),
        "text_frac": sum(1 for b in members_base if b.get("is_text")) / n,
        "image_frac": sum(1 for b in members_base if b.get("is_image")) / n,
        "shape_frac": sum(1 for b in members_base if b.get("is_shape")) / n,
        "line_frac": sum(1 for b in members_base if b.get("is_line")) / n,
        "table_chart_frac": (sum(1 for b in members_base if b.get("is_table")) + sum(1 for b in members_base if b.get("is_chart"))) / n,
        "cx_mean": round(_mean(cx), 5), "cx_std": round(_pstd(cx), 5),
        "cy_mean": round(_mean(cy), 5), "cy_std": round(_pstd(cy), 5),
        "x_span": round(x_span, 5), "y_span": round(y_span, 5),
        "occupied_area": round(occupied, 5),
        "density": round(n / (x_span * y_span + 1e-6), 4),
        "align_x_conc": round(max(gx.values()) / n, 4) if gx else 0.0,
        "align_y_conc": round(max(gy.values()) / n, 4) if gy else 0.0,
        "overlap_mean": round(_mean(ovl), 5),
        "area_mean": round(_mean(area), 5), "area_std": round(_pstd(area), 5),
        "eff_size_mean": round(_mean([e for e in eff if e > 0]), 4),
        "eff_size_max": round(max(eff) if eff else 0.0, 4),
        "bold_frac": round(_mean(col("bold")), 4),
        "largest_frac": round(_mean(col("is_largest_font")), 4),
        "short_text_frac": round(sum(1 for t in tlen if 0 < t < 3.7) / n, 4),
        "long_text_frac": round(sum(1 for t in tlen if t >= 5) / n, 4),
    }
    return out


def local_features(rows: list[dict], i: int) -> dict:
    nbr_idx = [j for j, _w in rows[i]["nbrs"].get("ALL", [])]
    b = rows[i]["base"]
    own_eff = float(b.get("eff_size_pt") or 0.0)
    own_area = float(b.get("area_log1p") or 0.0)
    ci = (float(b.get("cx") or 0.0), float(b.get("cy") or 0.0))
    if not nbr_idx:
        return {
            "deg_all": 0, "nbr_text_frac": 0.0, "nbr_eff_delta_mean": 0.0,
            "nbr_cxdist_mean": 0.0, "nbr_cydist_mean": 0.0,
            "nbr_overlap_mean": 0.0, "nbr_area_delta_mean": 0.0, "nbr_image_frac": 0.0,
        }
    cxs, cys, areas, effs = [], [], [], []
    text_n = img_n = ovl_sum = 0.0
    for j in nbr_idx:
        nb = rows[j]["base"]
        if nb.get("is_text"):
            text_n += 1
        if nb.get("is_image"):
            img_n += 1
        ovl_sum += float(nb.get("overlap_frac_max") or 0.0)
        cxs.append(float(nb.get("cx") or 0.0))
        cys.append(float(nb.get("cy") or 0.0))
        areas.append(float(nb.get("area_log1p") or 0.0))
        e = float(nb.get("eff_size_pt") or 0.0)
        if e > 0:
            effs.append(e)
    m = len(nbr_idx)
    return {
        "deg_all": len(nbr_idx),
        "nbr_text_frac": round(text_n / m, 4),
        "nbr_eff_delta_mean": round((_mean(effs) - own_eff) if effs else 0.0, 4),
        "nbr_cxdist_mean": round(_mean([abs(ci[0] - c) for c in cxs]), 4),
        "nbr_cydist_mean": round(_mean([abs(ci[1] - c) for c in cys]), 4),
        "nbr_overlap_mean": round(ovl_sum / m, 4),
        "nbr_area_delta_mean": round((_mean(areas) - own_area), 4),
        "nbr_image_frac": round(img_n / m, 4),
    }


LOCAL_FEATURE_NAMES = [
    "deg_all", "nbr_text_frac", "nbr_eff_delta_mean", "nbr_cxdist_mean",
    "nbr_cydist_mean", "nbr_overlap_mean", "nbr_area_delta_mean", "nbr_image_frac",
]


def build_spaces():
    rows = load_rows()
    by_slide: dict[str, list[int]] = {}
    for i, r in enumerate(rows):
        by_slide.setdefault(r["slide_key"], []).append(i)

    slide_vec = {}
    for sk, idxs in by_slide.items():
        vec = slide_context([rows[i]["base"] for i in idxs])
        slide_vec[sk] = vec
    SLIDE_FEATURE_NAMES = list(next(iter(slide_vec.values())).keys())

    local_rows = []
    for i in range(len(rows)):
        lf = local_features(rows, i)
        if i == 0:
            assert sorted(lf.keys()) == sorted(LOCAL_FEATURE_NAMES)
        local_rows.append(lf)

    feat_names = sorted(rows[0]["base"].keys())

    def mat(names_getter):
        return np.array(names_getter(), dtype=float)

    X_A = mat(lambda: [[float(r["base"].get(k) or 0.0) for k in feat_names] for r in rows])
    S = mat(lambda: [[slide_vec[r["slide_key"]][k] for k in SLIDE_FEATURE_NAMES] for r in rows])
    L = mat(lambda: [[local_rows[i][k] for k in LOCAL_FEATURE_NAMES] for i in range(len(rows))])
    y = np.array([r["label"] for r in rows])
    groups = np.array([r["group"] for r in rows])
    return rows, feat_names, SLIDE_FEATURE_NAMES, LOCAL_FEATURE_NAMES, X_A, S, L, y, groups


def _score(y, pred) -> dict:
    prf = precision_recall_fscore_support(y, pred, labels=sorted(set(y)), zero_division=0)
    labs = sorted(set(y))
    mi = labs.index("MOVE") if "MOVE" in labs else None
    ui = labs.index("UNCHANGED") if "UNCHANGED" in labs else None
    weak_present = [l for l in WEAK if l in labs]
    wi = [labs.index(l) for l in weak_present]
    destructive = (pred == "MOVE") | (pred == "REMOVE")
    truth_destructive = (y == "MOVE") | (y == "REMOVE")
    return {
        "macro_f1": round(f1_score(y, pred, average="macro", zero_division=0), 4),
        "weak_macro_f1": round(float(np.mean([prf[2][i] for i in wi])), 4) if wi else None,
        "move_precision": round(prf[0][mi], 4) if mi is not None else None,
        "move_recall": round(prf[1][mi], 4) if mi is not None else None,
        "move_f1": round(prf[2][mi], 4) if mi is not None else None,
        "unchanged_recall": round(prf[1][ui], 4) if ui is not None else None,
        "unsafe_rate": round(int((destructive & ~truth_destructive).sum()) / len(y), 4),
    }


def main() -> None:
    rows, feat_names, slide_names, local_names, X_A, S, L, y, groups = build_spaces()
    n_splits = choose_folds(y, groups)
    sgkf = StratifiedGroupKFold(n_splits=n_splits, shuffle=True, random_state=0)
    folds = list(sgkf.split(X_A, y, groups))

    spaces = {
        "A_node_only": X_A,
        "B_node_slide": np.hstack([X_A, S]),
        "C_node_local": np.hstack([X_A, L]),
        "D_full": np.hstack([X_A, L, S]),
    }

    results = {}
    rf_move_recalls = {}
    for space_name, X in spaces.items():
        entry = {}
        for mname, factory in (
            ("random_forest", lambda: RandomForestClassifier(n_estimators=300, min_samples_leaf=2, class_weight="balanced_subsample", random_state=0, n_jobs=-1)),
            ("hist_gbdt", lambda: HistGradientBoostingClassifier(max_depth=4, random_state=0)),
        ):
            preds = np.empty(len(y), dtype=object)
            for tr, te in folds:
                m = factory()
                m.fit(X[tr], y[tr])
                preds[te] = m.predict(X[te])
            sc = _score(y, preds)
            entry[mname] = sc
            if mname == "random_forest":
                rf_move_recalls[space_name] = sc["move_recall"]
            print(f"[{space_name}] {mname}: macro={sc['macro_f1']} weak={sc['weak_macro_f1']} moveR={sc['move_recall']} moveF1={sc['move_f1']} unchR={sc['unchanged_recall']}", flush=True)
        results[space_name] = entry

    # ---- Phase 8.7: conditional ambiguity across feature spaces ----
    amb = {}
    move_true = y == "MOVE"
    for space_name, X in spaces.items():
        mu = X.mean(axis=0)
        sd = np.maximum(X.std(axis=0), 1e-9)
        Z = (X - mu) / sd
        Zn = Z / np.maximum(np.linalg.norm(Z, axis=1, keepdims=True), 1e-9)
        sims = (Zn @ Zn.T).astype(np.float32)
        ent_list, mvf_list, correct = [], [], 0
        total = 0
        for i in range(len(rows)):
            order = np.argsort(-sims[i])
            counts = Counter()
            picked = 0
            for j in order:
                if j == i or rows[j]["slide_key"] == rows[i]["slide_key"]:
                    continue
                counts[y[j]] += 1
                picked += 1
                if picked >= KNN_K:
                    break
            ent = _entropy(list(counts.values()))
            mvf = counts.get("MOVE", 0) / max(picked, 1)
            maj = counts.most_common(1)[0][0]
            total += 1
            correct += int(maj == y[i])
            if move_true[i]:
                ent_list.append(ent)
                mvf_list.append(mvf)
        amb[space_name] = {
            "knn_accuracy_all_nodes": round(correct / total, 4),
            "move_knn_entropy_mean": round(float(np.mean(ent_list)), 4),
            "move_knn_movefrac_mean": round(float(np.mean(mvf_list)), 4),
        }
        print(f"[ambiguity {space_name}] {amb[space_name]}", flush=True)

    d_weak = round(results["D_full"]["random_forest"]["weak_macro_f1"] - results["A_node_only"]["random_forest"]["weak_macro_f1"], 4)
    d_move = round(rf_move_recalls["D_full"] - rf_move_recalls["A_node_only"], 4)
    ent_drop = round(amb["A_node_only"]["move_knn_entropy_mean"] - amb["D_full"]["move_knn_entropy_mean"], 4)

    if d_move >= 0.10 or d_weak >= 0.05 or ent_drop >= 0.25:
        verdict = "CONTEXT_CARRIER"
        action = "Reopen simple relational aggregation (context features justified); small message-passing experiment becomes a research candidate afterwards."
    else:
        verdict = "OUTCOME_1_GENUINE_AMBIGUITY"
        action = "NO-GO reinforced: neither slide context nor local aggregation reduces ambiguity or improves MOVE. Targeted label collection (Pool A/B) is the next investment."

    payload = {
        "schema": "context_ablation_v1",
        "n_rows": len(rows),
        "n_groups": int(len(set(groups))),
        "n_splits": n_splits,
        "feature_space_dims": {k: int(v.shape[1]) for k, v in spaces.items()},
        "ablation": results,
        "conditional_ambiguity": amb,
        "deltas_rf_vs_A": {"weak_macro_f1": d_weak, "move_recall": d_move, "entropy_drop_bits": ent_drop},
        "verdict": {"classification": verdict, "action": action},
    }
    (config.METADATA_DIR / "CONTEXT_ABLATION.json").write_text(json.dumps(payload, indent=1), encoding="utf-8")

    md = [
        "# Phase 8.6/8.7 - Context Representation Ablation & Conditional Ambiguity",
        "",
        f"Rows: {len(rows)} | Groups: {payload['n_groups']} | Folds: {n_splits}",
        "",
        "## Ablation (RandomForest pooled)",
        "",
        "| Space | dims | macro F1 | weak macro F1 | MOVE recall | MOVE F1 | UNCH recall |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for sp in spaces:
        e = results[sp]["random_forest"]
        md.append(f"| {sp} | {spaces[sp].shape[1]} | {e['macro_f1']} | {e['weak_macro_f1']} | {e['move_recall']} | {e['move_f1']} | {e['unchanged_recall']} |")
    md += ["", "## Conditional ambiguity (true-MOVE nodes)", "", "| Space | kNN acc (all) | MOVE entropy | MOVE nbr-move-frac |", "|---|---:|---:|---:|"]
    for sp in spaces:
        a = amb[sp]
        md.append(f"| {sp} | {a['knn_accuracy_all_nodes']} | {a['move_knn_entropy_mean']} | {a['move_knn_movefrac_mean']} |")
    md += [
        "",
        f"Deltas vs A (RF): weak {d_weak:+}, MOVE recall {d_move:+}, entropy drop {ent_drop} bits",
        "",
        f"**VERDICT: {verdict}**",
        "",
        action,
    ]
    (config.METADATA_DIR / "PHASE_86_87_CONTEXT_REPORT.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(json.dumps(payload["verdict"], indent=1))


if __name__ == "__main__":
    main()
