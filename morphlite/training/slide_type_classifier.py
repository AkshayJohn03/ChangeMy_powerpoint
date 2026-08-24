"""Phase 13: ML slide-type classifier trained on golden deck pairs.

Learns to classify raw slides into template types:
    TITLE, AGENDA, GENERIC_CONTENT, CASE_STUDY, SECTION_SPLITTER,
    THANK_YOU, WHO_WE_ARE, GENERIC_MINIMAL

    python -m morphlite.training.slide_type_classifier
"""
from __future__ import annotations

import glob
import json
import os
import sys

import numpy as np
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from sklearn.metrics import classification_report, f1_score
from sklearn.model_selection import StratifiedGroupKFold

sys.path.insert(0, ".")

from morphlite.pipeline.template_driven import classify_slide


def extract_slide_features(slide) -> dict:
    """Deployable features from a raw slide for slide-type classification."""
    n_shapes = len(slide.shapes)
    n_text = 0
    n_images = 0
    n_tables = 0
    n_charts = 0
    n_groups = 0
    n_lines = 0
    max_font = 0.0
    min_font = 999.0
    total_text_len = 0
    n_text_shapes = 0
    has_fullslide_image = False
    has_title_placeholder = False
    title_text_len = 0
    n_paragraphs = 0
    y_positions = []
    shape_areas = []

    for shape in slide.shapes:
        st = str(getattr(shape, "shape_type", ""))
        if "TEXT_BOX" in st or shape.has_text_frame:
            n_text += 1
        if "PICTURE" in st:
            n_images += 1
        if "TABLE" in st:
            n_tables += 1
        if "CHART" in st:
            n_charts += 1
        if "GROUP" in st:
            n_groups += 1
        if "LINE" in st:
            n_lines += 1

        try:
            w = shape.width / 914400.0
            h = shape.height / 914400.0
            if w > 12 and h > 6:
                has_fullslide_image = True
            shape_areas.append(w * h)
        except Exception:
            pass

        try:
            y_positions.append(shape.top / 914400.0 if shape.top else 0)
        except Exception:
            pass

        if "title" in (shape.name or "").lower():
            has_title_placeholder = True

        if shape.has_text_frame:
            txt = shape.text_frame.text.strip()
            if txt:
                total_text_len += len(txt)
                n_text_shapes += 1
                n_paragraphs += len(shape.text_frame.paragraphs)

            for p in shape.text_frame.paragraphs:
                for r in p.runs:
                    if r.font.size:
                        pt = r.font.size.pt
                        max_font = max(max_font, pt)
                        min_font = min(min_font, pt)

    if min_font > 998:
        min_font = 0

    content_w = max(1e-6, 13.333)
    content_h = max(1e-6, 7.5)

    return [
        n_shapes,
        n_text,
        n_images,
        n_tables,
        n_charts,
        n_groups,
        n_lines,
        max_font,
        min_font,
        total_text_len,
        n_text_shapes,
        n_paragraphs,
        int(has_fullslide_image),
        int(has_title_placeholder),
        title_text_len,
        round(total_text_len / max(n_text, 1), 2),
        round(max_font / max(min_font, 1), 2),
        len(set(round(yy) for yy in y_positions)),
        round(sum(shape_areas) / (content_w * content_h), 3),
        round(max(shape_areas) if shape_areas else 0, 2),
    ]


FEATURE_NAMES = [
    "n_shapes", "n_text", "n_images", "n_tables", "n_charts", "n_groups", "n_lines",
    "max_font", "min_font", "total_text_len", "n_text_shapes", "n_paragraphs",
    "has_fullslide_image", "has_title_placeholder", "title_text_len",
    "avg_text_len", "font_ratio", "n_distinct_y_positions",
    "total_shape_area_frac", "max_shape_area",
]


def build_training_data(raw_decks: list[str]) -> tuple:
    """Extract features + heuristic labels from all available raw decks."""
    import pptx

    X = []
    y = []
    groups = []

    for di, deck_path in enumerate(raw_decks):
        try:
            prs = pptx.Presentation(deck_path)
        except Exception:
            continue

        for si, slide in enumerate(prs.slides):
            feats = extract_slide_features(slide)
            heuristic_label = classify_slide(slide)
            X.append(feats)
            y.append(heuristic_label)
            groups.append(f"deck_{di}")

    return np.array(X), np.array(y), np.array(groups)


def main() -> None:
    # Collect decks
    all_decks = []
    for pattern in [
        "data/source/paired/raw/**/*.pptx",
        "data/source/paired/branded/**/*.pptx",
        "data/source/alternating/**/*.pptx",
    ]:
        all_decks.extend(sorted(glob.glob(pattern, recursive=True)))

    # Limit for speed
    all_decks = all_decks[:30]

    print(f"Processing {len(all_decks)} decks for training data...")
    X, y, groups = build_training_data(all_decks)
    if len(X) == 0:
        print("ERROR: no training data extracted")
        return
    labels = sorted(set(y))
    print(f"samples={len(X)} classes={labels}")
    print(f"class distribution: {dict(Counter(y))}")
    if len(set(groups)) < 2:
        print("WARNING: fewer than 2 groups, skipping CV")
        return

    # CV evaluation with robust fallback
    min_class = min(Counter(y).values())
    n_splits = max(2, min(3, min_class, len(set(groups))))

    models = {
        "random_forest": lambda: RandomForestClassifier(n_estimators=200, random_state=0, n_jobs=-1),
        "hist_gbdt": lambda: HistGradientBoostingClassifier(max_depth=4, random_state=0),
    }

    results = {}
    for mname, factory in models.items():
        y_true_all, y_pred_all = [], []
        fold_count = 0
        try:
            sgkf = StratifiedGroupKFold(n_splits=n_splits, shuffle=True, random_state=0)
            splits = list(sgkf.split(X, y, groups))
        except Exception:
            from sklearn.model_selection import train_test_split
            tr, te = train_test_split(np.arange(len(y)), test_size=0.3, random_state=0, stratify=y)
            splits = [(tr, te)]

        for tr, te in splits:
            if len(te) == 0 or len(tr) == 0:
                continue
            m = factory()
            m.fit(X[tr], y[tr])
            preds = m.predict(X[te])
            y_pred_all.extend(preds)
            y_true_all.extend(y[te])
            fold_count += 1
        if not y_true_all:
            results[mname] = 0.0
            continue
        f1 = f1_score(y_true_all, y_pred_all, average="macro", zero_division=0)
        results[mname] = round(f1, 4)
        print(f"  {mname}: macro F1 = {f1:.4f} ({fold_count} folds, {len(y_true_all)} test samples)")

    # Train final model on all data
    best_model_name = max(results, key=results.get)
    best_factory = models[best_model_name]
    final_model = best_factory()
    final_model.fit(X, y)

    # Compare against heuristic baseline
    y_heuristic = []
    for di, deck_path in enumerate(all_decks):
        try:
            prs = pptx.Presentation(deck_path)
            for slide in prs.slides:
                y_heuristic.append(classify_slide(slide))
        except Exception:
            pass
    y_heuristic = np.array(y_heuristic[:len(y)])
    if len(y_heuristic) > 0:
        heuristic_f1 = f1_score(y[:len(y_heuristic)], y_heuristic, average="macro", zero_division=0)
    else:
        heuristic_f1 = 0.0
        print("  heuristic baseline: skipped (empty)")
    print(f"\n  heuristic baseline: macro F1 = {heuristic_f1:.4f}")
    print(f"  best ML: {best_model_name} = {results[best_model_name]:.4f}")
    print(f"  improvement: {results[best_model_name] - heuristic_f1:+.4f}")

    # Save model + metadata
    import joblib
    os.makedirs("models", exist_ok=True)
    model_path = "models/slide_type_classifier.joblib"
    joblib.dump({
        "model": final_model,
        "feature_names": FEATURE_NAMES,
        "labels": labels,
        "model_type": best_model_name,
        "cv_macro_f1": results[best_model_name],
        "heuristic_macro_f1": round(heuristic_f1, 4),
        "n_training_samples": len(X),
        "n_decks": len(all_decks),
    }, model_path)
    print(f"\nmodel saved: {model_path}")

    # Save report
    report = {
        "n_samples": len(X),
        "n_decks": len(all_decks),
        "labels": labels,
        "class_distribution": dict(Counter(y)),
        "models": results,
        "heuristic_baseline": round(heuristic_f1, 4),
        "best_model": best_model_name,
        "improvement_over_heuristic": round(results[best_model_name] - heuristic_f1, 4),
        "recommendation": (
            "ML classifier provides meaningful improvement over heuristics"
            if results[best_model_name] > heuristic_f1 + 0.02
            else "Heuristics sufficient at current dataset size"
        ),
    }
    with open("research/SLIDE_TYPE_CLASSIFIER.json", "w") as f:
        json.dump(report, f, indent=1)
    print(f"report saved: research/SLIDE_TYPE_CLASSIFIER.json")


from collections import Counter

if __name__ == "__main__":
    main()
