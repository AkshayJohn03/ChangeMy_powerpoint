"""Phase 14: Integrated v0.2 pipeline with deterministic brand layer + ML node model."""
import glob
import hashlib
import json
import os
import shutil
import sys
import uuid
from pathlib import Path

import numpy as np
import pptx
from pptx.util import Pt, Inches
from pptx.dml.color import RGBColor
from pptx.oxml.ns import qn

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from morphlite.pipeline.brand_profile import DEFAULT_PROFILE, BrandProfile
from morphlite.pipeline.mutation_engine import MutationEngine
from morphlite.inference.v2_engine import NodeModelInference, PolicyEngineV2, SlideRemoveBudget


def _force_run_color(run, rgb: RGBColor):
    rPr = run._r.get_or_add_rPr()
    for tag in ("a:solidFill", "a:gradFill", "a:pattFill", "a:blipFill", "a:noFill", "a:grpFill"):
        for el in rPr.findall(qn(tag)):
            rPr.remove(el)
    sf = rPr.makeelement(qn("a:solidFill"), {})
    srgb = sf.makeelement(qn("a:srgbClr"), {"val": str(rgb)})
    sf.append(srgb)
    rPr.insert(0, sf)


def _force_run_font(run, name: str):
    rPr = run._r.get_or_add_rPr()
    for tag in ("a:latin", "a:ea", "a:cs"):
        for el in rPr.findall(qn(tag)):
            rPr.remove(el)
    latin = rPr.makeelement(qn("a:latin"), {"typeface": name})
    sf = rPr.find(qn("a:solidFill"))
    if sf is not None:
        sf.addnext(latin)
    else:
        rPr.insert(0, latin)


def _force_paragraph_color(paragraph, rgb: RGBColor):
    pPr = paragraph._p.get_or_add_pPr()
    defRPr = pPr.find(qn("a:defRPr"))
    if defRPr is None:
        defRPr = pPr.makeelement(qn("a:defRPr"), {})
        pPr.append(defRPr)
    for tag in ("a:solidFill", "a:gradFill", "a:noFill"):
        for el in defRPr.findall(qn(tag)):
            defRPr.remove(el)
    sf = defRPr.makeelement(qn("a:solidFill"), {})
    srgb = sf.makeelement(qn("a:srgbClr"), {"val": str(rgb)})
    sf.append(srgb)
    defRPr.insert(0, sf)


def _luminance(rgb):
    r, g, b = rgb[0] / 255, rgb[1] / 255, rgb[2] / 255
    return 0.299 * r + 0.587 * g + 0.114 * b


def _luminance(rgb):
    r, g, b = rgb[0] / 255, rgb[1] / 255, rgb[2] / 255
    return 0.299 * r + 0.587 * g + 0.114 * b


def _contrast_ratio(fg, bg):
    l1, l2 = _luminance(fg), _luminance(bg)
    return (max(l1, l2) + 0.05) / (min(l1, l2) + 0.05)


def _all_shapes(slide):
    for shape in slide.shapes:
        yield shape
        if hasattr(shape, "shapes"):
            try:
                for s in shape.shapes:
                    yield s
            except Exception:
                pass


def _is_title_like(shape):
    try:
        if "title" in (shape.name or "").lower():
            return True
        if shape.has_text_frame:
            for p in shape.text_frame.paragraphs:
                for r in p.runs:
                    if r.font.size and r.font.size.pt >= 20:
                        return True
        y = shape.top / 914400.0 if shape.top else 99
        return y < 1.5
    except Exception:
        return False


class IntegratedPipelineV2:
    def __init__(self, template_path: str, profile: BrandProfile | None = None,
                 node_model_path: str | None = None):
        self.profile = profile or DEFAULT_PROFILE
        self.template_path = template_path

        from morphlite.pipeline.mutation_engine import MutationEngine
        self.mutation_engine = MutationEngine(self.profile)

        # Load v2 node model
        model_path = node_model_path or str(
            Path(__file__).resolve().parent.parent.parent / "models" / "brandmorph_node_model_v2.joblib"
        )
        if os.path.exists(model_path):
            import joblib
            bundle = joblib.load(model_path)
            self.node_model = bundle
            self.ml_available = True
        else:
            self.node_model = None
            self.ml_available = False

    def process(self, input_path: str, output_path: str | None = None) -> dict:
        input_hash = hashlib.sha256(Path(input_path).read_bytes()).hexdigest()
        prs = pptx.Presentation(input_path)
        n_slides = len(prs.slides)
        bp = self.profile

        bg_rgb = RGBColor(*bp._hex_tuple(bp.dark_hex))
        card_rgb = RGBColor(*bp._hex_tuple(bp.card_hex))
        gold_rgb = bp.gold_rgb
        white_rgb = bp.white_rgb

        all_mutations = []
        slide_info_list = []

        # Extract template assets for font/color resolution
        from morphlite.pipeline.template_styled import TemplateStyledPipeline
        temp_pipeline = TemplateStyledPipeline(self.template_path)
        assets = temp_pipeline._template_assets

        title_font = assets.get("title_font", "Times New Roman")
        body_font = assets.get("body_font", "Arial")
        title_color_hex = assets.get("title_color", "FFB81C")
        body_color_hex = assets.get("body_color", "FFFFFF")
        title_rgb = RGBColor.from_string(title_color_hex)
        body_rgb = RGBColor.from_string(body_color_hex)

        # Load ML model
        ml_available = self.ml_available and self.node_model is not None

        for si, slide in enumerate(prs.slides):
            slide_mut = {"deterministic": 0, "ml_changed": 0, "ml_review": 0, "ml_preserve": 0}

            # --- 1. BACKGROUND ---
            try:
                old_bg = None
                try:
                    if slide.background.fill.type == 1:
                        old_bg = str(slide.background.fill.fore_color.rgb)
                except Exception:
                    pass
                slide.background.fill.solid()
                slide.background.fill.fore_color.rgb = bg_rgb
                all_mutations.append({"slide": si + 1, "stage": "BRAND_BG",
                                      "property": "background", "before": old_bg or "(inherit)",
                                      "after": str(bg_rgb)})
                slide_mut["deterministic"] += 1
            except Exception:
                pass

            # --- 2. SHAPE-LEVEL PROCESSING ---
            shapes_list = list(_all_shapes(slide))

            # Compute features for ML (if available)
            ml_decisions = {}
            if ml_available and shapes_list:
                try:
                    feature_dicts = []
                    for shape in shapes_list:
                        fd = self._compute_base_features(shape)
                        feature_dicts.append(fd)

                    # Build feature matrix
                    all_feat_names = self.node_model["feature_names_base"]
                    X_base = np.array([[fd.get(k, 0.0) for k in all_feat_names] for fd in feature_dicts])

                    # Relational features (simplified for inline computation)
                    n = len(shapes_list)
                    X_rel = np.zeros((n, 14))
                    for i in range(n):
                        bi = feature_dicts[i]
                        others = [j for j in range(n) if j != i]
                        if others:
                            nbr_cx = [feature_dicts[j].get("cx", 0) for j in others]
                            nbr_cy = [feature_dicts[j].get("cy", 0) for j in others]
                            own_cx = bi.get("cx", 0)
                            own_cy = bi.get("cy", 0)
                            X_rel[i, 0] = len(others)
                            X_rel[i, 1] = sum(1 for j in others if feature_dicts[j].get("is_text")) / max(len(others), 1)
                            X_rel[i, 2] = 0
                            X_rel[i, 3] = sum(abs(own_cx - c) for c in nbr_cx) / max(len(nbr_cx), 1)
                            X_rel[i, 4] = sum(abs(own_cy - c) for c in nbr_cy) / max(len(nbr_cy), 1)

                    X_slide_type = np.zeros((n, 3))
                    X_slide_type[:, 2] = 1  # default: content slide
                    if si == 0:
                        X_slide_type[:, 0] = 1

                    from morphlite.inference.v2_engine import NodeModelInference
                    inf = NodeModelInference.__new__(NodeModelInference)
                    inf.multiclass = self.node_model["multiclass"]
                    inf.move_detector = self.node_model["move_detector"]
                    inf.remove_detector = self.node_model["remove_detector"]
                    inf.labels = self.node_model["labels"]
                    inf.move_threshold = self.node_model.get("move_threshold", 0.2)
                    inf.remove_threshold = self.node_model.get("remove_threshold", 0.5)

                    X_full = np.hstack([X_base, X_rel, X_slide_type])
                    expected = inf.multiclass.n_features_in_
                    if X_full.shape[1] > expected:
                        X_full = X_full[:, :expected]
                    elif X_full.shape[1] < expected:
                        pad = np.zeros((X_full.shape[0], expected - X_full.shape[1]))
                        X_full = np.hstack([X_full, pad])
                    mc_probs = inf.multiclass.predict_proba(X_full)
                    mc_labels = inf.multiclass.classes_
                    move_p = inf.move_detector.predict_proba(X_full)
                    remove_p = inf.remove_detector.predict_proba(X_full)

                    move_col = list(inf.move_detector.classes_).index(1) if 1 in inf.move_detector.classes_ else 0
                    rem_col = list(inf.remove_detector.classes_).index(1) if 1 in inf.remove_detector.classes_ else 0

                    for i in range(n):
                        mc_idx = int(np.argmax(mc_probs[i]))
                        action = str(mc_labels[mc_idx])
                        conf = float(mc_probs[i][mc_idx])
                        move_p_i = float(move_p[i][move_col]) if move_p.shape[1] > move_col else 0.0
                        remove_p_i = float(remove_p[i][rem_col]) if remove_p.shape[1] > rem_col else 0.0

                        if remove_p_i > 0.5 and remove_p_i > conf:
                            action = "REMOVE"
                            conf = remove_p_i
                        if move_p_i > 0.3 and move_p_i > conf:
                            action = "MOVE"
                            conf = move_p_i

                        ml_decisions[i] = {"action": action, "confidence": conf}
                except Exception as e:
                    print(f"  [warn] ML inference failed on slide {si+1}: {e}", flush=True)

            # --- 3. PER-SHAPE PROCESSING ---
            policy = PolicyEngineV2() if ml_available else None
            budget = SlideRemoveBudget() if ml_available else None

            for ni, shape in enumerate(shapes_list):
                shape_name = shape.name or "?"
                has_tf = shape.has_text_frame
                text = shape.text_frame.text.strip() if has_tf else ""

                # Skip guidance text
                if text and ("font guidance" in text.lower() or "do not change" in text.lower()):
                    continue

                # Get ML decision for this shape
                ml_dec = ml_decisions.get(ni, {"action": "UNCHANGED", "confidence": 0})

                # Deterministic: font normalization
                if has_tf:
                    is_title = _is_title_like(shape)
                    target_font = title_font if is_title else body_font
                    for p in shape.text_frame.paragraphs:
                        for r in p.runs:
                            old_font = r.font.name
                            try:
                                _force_run_font(r, target_font)
                            except Exception:
                                r.font.name = target_font
                            if old_font != target_font:
                                all_mutations.append({
                                    "slide": si + 1, "stage": "DETERMINISTIC",
                                    "property": "font.name", "shape": shape_name,
                                    "before": old_font or "(inh)", "after": target_font,
                                })
                                slide_mut["deterministic"] += 1

                # ML-gated REMOVE
                if ml_available and ml_dec.get("action") == "REMOVE":
                    remove_conf = ml_dec["confidence"]
                    policy_v2 = policy.decide("REMOVE", remove_conf, {
                        "is_table": getattr(shape, "has_table", False),
                        "is_chart": getattr(shape, "has_chart", False),
                        "text_len": len(text),
                    })

                    if policy_v2 == "APPLY":
                        try:
                            shape._element.getparent().remove(shape._element)
                            all_mutations.append({
                                "slide": si + 1, "stage": "ML_REMOVE",
                                "property": "element", "shape": shape_name,
                                "before": text[:50] if text else "(no text)",
                                "after": "(removed)", "confidence": remove_conf,
                            })
                            slide_mut["ml_changed"] += 1
                        except Exception:
                            pass
                    elif policy_v2 == "REVIEW":
                        slide_mut["ml_review"] += 1
                    continue

                # Deterministic: text color normalization
                if has_tf:
                    is_title = _is_title_like(shape)
                    effective_bg = bg_rgb
                    target_color = title_rgb if is_title else body_rgb

                    # Check shape fill
                    try:
                        if shape.fill.type == 1:
                            fill_rgb = shape.fill.fore_color.rgb
                            fill_lum = _luminance(fill_rgb)
                            if fill_lum > 0.5:
                                effective_bg = fill_rgb
                    except Exception:
                        pass

                    cr = _contrast_ratio(target_color, effective_bg)
                    if cr < 2.0:
                        target_color = body_rgb

                    for p in shape.text_frame.paragraphs:
                        try:
                            _force_paragraph_color(p, target_color)
                        except Exception:
                            pass
                        for r in p.runs:
                            old_c = "(inh)"
                            try:
                                if r.font.color and r.font.color.rgb:
                                    old_c = str(r.font.color.rgb)
                            except Exception:
                                pass
                            try:
                                _force_run_color(r, target_color)
                            except Exception:
                                r.font.color.rgb = target_color
                            if old_c != str(target_color):
                                all_mutations.append({
                                    "slide": si + 1, "stage": "DETERMINISTIC",
                                    "property": "font.color", "shape": shape_name,
                                    "before": old_c, "after": str(target_color),
                                })
                                slide_mut["deterministic"] += 1

                # ML-gated RESIZE
                if ml_available and ml_dec.get("action") == "RESIZE" and has_tf:
                    conf = ml_dec["confidence"]
                    if conf >= 0.35:
                        resize_map = {12.0: 10.0, 14.0: 12.0, 16.0: 12.0, 16.7: 12.0,
                                      20.0: 12.0, 32.0: 28.0, 36.0: 24.0}
                        for p in shape.text_frame.paragraphs:
                            for r in p.runs:
                                if r.font.size:
                                    pt_val = round(r.font.size.pt, 1)
                                    mapped = resize_map.get(pt_val)
                                    if mapped is not None and abs(pt_val - mapped) >= 0.5:
                                        old_sz = pt_val
                                        r.font.size = Pt(mapped)
                                        all_mutations.append({
                                            "slide": si + 1, "stage": "ML_RESIZE",
                                            "property": "font.size", "shape": shape_name,
                                            "before": f"{old_sz}pt", "after": f"{mapped}pt",
                                            "confidence": conf,
                                        })
                                        slide_mut["ml_changed"] += 1

            # Slide budget enforcement
            remove_count = sum(1 for m in all_mutations
                               if m.get("slide") == si + 1 and m.get("stage") == "ML_REMOVE")
            if remove_count > 5:
                slide_mut["ml_changed"] -= (remove_count - 5)
                slide_mut["ml_review"] += (remove_count - 5)

            slide_info_list.append({
                "slide": si + 1, "type": "processed",
                "deterministic": slide_mut["deterministic"],
                "ml_changed": slide_mut["ml_changed"],
                "ml_review": slide_mut["ml_review"],
                "preserved": len(shapes_list) - slide_mut["deterministic"] - slide_mut["ml_changed"],
            })

        # Integrity
        output_hash = ""
        if output_path:
            prs.save(output_path)
            output_hash = hashlib.sha256(Path(output_path).read_bytes()).hexdigest()

        binary_changed = input_hash != output_hash if output_hash else False

        return {
            "deck_id": str(uuid.uuid4())[:8],
            "input_path": input_path,
            "output_path": output_path,
            "n_slides": n_slides,
            "input_sha256": input_hash,
            "output_sha256": output_hash,
            "binary_changed": binary_changed,
            "mutations": all_mutations,
            "mutation_count": len(all_mutations),
            "mutation_summary": {
                "total": len(all_mutations),
                "by_stage": dict(Counter(m.get("stage", "?") for m in all_mutations)),
                "by_property": dict(Counter(m.get("property", "?") for m in all_mutations).most_common(10)),
            },
            "ml_available": ml_available,
            "slide_info": slide_info_list,
        }

    def _compute_base_features(self, shape) -> dict:
        """Compute V2-compatible base features from a python-pptx shape.

        Returns all 49 feature names expected by brandmorph_node_model_v2.
        Missing/unknown values default to 0.0 or sensible fallbacks.
        """
        try:
            x = shape.left / 914400.0 if shape.left else 0.0
            y = shape.top / 914400.0 if shape.top else 0.0
            w = shape.width / 914400.0 if shape.width else 0.0
            h = shape.height / 914400.0 if shape.height else 0.0
        except Exception:
            x = y = w = h = 0.0

        st = str(getattr(shape, "shape_type", ""))
        text = shape.text_frame.text.strip() if shape.has_text_frame else ""

        eff_size = 0.0
        bold = False
        italic_flag = False
        if shape.has_text_frame:
            for p in shape.text_frame.paragraphs:
                for r in p.runs:
                    if r.font.size:
                        eff_size = max(eff_size, float(r.font.size.pt))
                    if r.font.bold:
                        bold = True
                    if r.font.italic:
                        italic_flag = True

        # --- shape type flags ---
        is_shape_flag = int("AUTO_SHAPE" in st or "FREEFORM" in st)
        is_arrow = int("ARROW" in st.upper())
        is_line = int("LINE" in st or "CONNECTOR" in st.upper())
        is_image = int("PICTURE" in st)
        is_chart = int(getattr(shape, "has_chart", False))
        is_table = int(getattr(shape, "has_table", False))
        is_group = int("GROUP" in st)

        # --- layout / position ---
        cx = x + w / 2 if w and h else 0.0
        cy = y + h / 2 if w and h else 0.0
        aspect = min(max(w / h, 0) if h else 0, 50)
        rotation_flag = int(abs(getattr(shape, "rotation", 0)) > 1)

        # --- text features ---
        text_len = len(text)
        word_count = len(text.split()) if text else 0
        numeric_cnt = sum(c.isdigit() for c in text)
        upper_cnt = sum(c.isupper() for c in text)
        alpha_cnt = sum(c.isalpha() for c in text)

        return {
            # geometry / position
            "align_x_resid": 0.0,      # placeholder: residual after alignment
            "align_y_resid": 0.0,      # placeholder: residual after alignment
            "area_log1p": float(np.log1p(abs(w * h))),
            "aspect": aspect,
            "bold": int(bold),
            "container_depth": 0,      # not extractable from pptx directly
            "ctx_n_nodes_log1p": 0,    # placeholder: context node count
            "ctx_n_text_frac": 0,      # placeholder: context text fraction
            "cx": cx,
            "cy": cy,
            "eff_color_present": int(
                getattr(shape.fill, "type", 0) == 1
                if hasattr(shape, "fill") else 0
            ),
            "eff_conf_mean": 0.0,      # placeholder: font confidence mean
            "eff_family_run": 0.0,        # placeholder: font family run (not extractable as float from pptx)
            "eff_family_theme": 0.0,    # placeholder: theme font family (not extractable as float from pptx)
            "eff_is_largest": int(
                eff_size == max(
                    [float(r.font.size.pt) for p in shape.text_frame.paragraphs
                     for r in p.runs] + [0])
                if text and eff_size > 0 else 0
            ),
            "eff_rel_max": 0.0,        # placeholder: relative font size max
            "eff_rel_median": 0.0,     # placeholder: relative font size median
            "eff_size_pt": eff_size,
            "fill_present": int(getattr(shape.fill, "type", 0) == 1
                                if hasattr(shape, "fill") else 0),
            "font_size_pt": eff_size,
            "grid_occupancy": 0,       # placeholder: grid cell occupancy
            "guidance_flag": int(
                "font guidance" in text.lower() or "do not change" in text.lower()
            ),
            "h": h,
            "is_arrow": is_arrow,
            "is_chart": is_chart,
            "is_group": is_group,
            "is_image": is_image,
"is_largest_font": int(
                eff_size > 0 and all(
                    r.font.size and float(r.font.size.pt) <= eff_size
                    for p in shape.text_frame.paragraphs
                    for r in p.runs
                ) if text and eff_size > 0 else 0
            ),
            "is_line": is_line,
            "is_shape": is_shape_flag,
            "is_table": is_table,
            "is_text": int(bool(text)),
            "italic": int(italic_flag),
            "nn3_mean": 0.0,           # placeholder: 3-nearest-neighbors mean
            "nn_dist": 0.0,            # placeholder: nearest neighbor distance
            "numeric_ratio": numeric_cnt / max(text_len, 1) if text else 0,
            "overlap_frac_max": 0.0,   # placeholder: max overlap fraction
            "rotation_flag": rotation_flag,
            "same_type_frac": 0,       # placeholder: fraction of same-type siblings
            "size_rel_max": 0,         # placeholder: size relative to max in deck
            "size_rel_median": 0,      # placeholder: size relative to median in deck
            "text_len_log1p": float(np.log1p(text_len)),
            "upper_ratio": upper_cnt / max(alpha_cnt, 1) if text else 0,
            "w": w,
            "word_count_log1p": float(np.log1p(word_count)),
            "x": x,
            "x_rank_frac": 0,          # placeholder: x-rank within slide
            "y": y,
            "y_rank_frac": 0,          # placeholder: y-rank within slide
        }


from collections import Counter
