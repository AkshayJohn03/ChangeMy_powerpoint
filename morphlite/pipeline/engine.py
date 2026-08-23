"""BrandMorph v0.1 end-to-end pipeline.

    result = BrandMorphPipeline.process("input.pptx", "output.pptx")

Flow:
    PPTX -> AST extraction -> V2 features -> RF model -> policy -> applier -> PPTX

MOVE is never auto-applied. UNCHANGED is a no-op. Only RESTYLE, RESIZE,
REMOVE and RECOLOR pass through the safety gate into the mutation layer.
"""
from __future__ import annotations

import json
import tempfile
import uuid
from pathlib import Path

import numpy as np
import pptx
from pptx.util import Pt, Inches
from pptx.dml.color import RGBColor

from ..ast.extractor import flatten_nodes
from ..features.node_features_v2 import extract_slide_node_features_v2
from ..inference.decision import DecisionEngine
from ..inference.policy import APPLY, REVIEW, PRESERVE, NOOP
from .brand_profile import DEFAULT_PROFILE, BrandProfile

APPLYABLE = {"RESTYLE", "RESIZE", "RECOLOR", "REMOVE"}


class DeckAnalysis:
    def __init__(self):
        self.deck_id = str(uuid.uuid4())[:8]
        self.slides: list[dict] = []
        self.plan: dict = {}
        self.integrity: dict = {}
        self.input_path: str = ""
        self.output_path: str = ""

    def to_json(self) -> dict:
        return {
            "deck_id": self.deck_id,
            "input_path": self.input_path,
            "output_path": self.output_path,
            "n_slides": len(self.slides),
            "slides": self.slides,
            "transformation_plan": self.plan,
            "integrity": self.integrity,
        }


def _shape_text(shape) -> str:
    if not shape.has_text_frame:
        return ""
    return shape.text_frame.text.strip()


def _walk_shapes(slide):
    for shape in slide.shapes:
        yield shape
        if shape.shape_type == 6:  # GROUP
            try:
                yield from _walk_shapes_recursive(shape)
            except Exception:
                pass


def _walk_shapes_recursive(group):
    for s in group.shapes:
        yield s


class BrandMorphPipeline:

    def __init__(self, profile: BrandProfile | None = None):
        from morphlite.inference.decision import DecisionEngine

        self.profile = profile or DEFAULT_PROFILE
        self.engine = DecisionEngine()
        from .mutation_engine import MutationEngine

        self.mutation_engine = MutationEngine(self.profile)

    def process(self, input_path: str, output_path: str | None = None) -> DeckAnalysis:
        analysis = DeckAnalysis()
        analysis.input_path = input_path

        prs = pptx.Presentation(input_path)

        # --- STAGE 1: SEMANTIC BRAND LAYER (always runs, always visible) ---
        from .semantic_brand import SemanticBrandTransformer

        transformer = SemanticBrandTransformer(self.profile)
        deterministic_mutations = transformer.transform(prs)

        # --- STAGE 2: AST EXTRACTION + ML ANALYSIS ---
        from ..ast.extractor import extract_deck as _extract_ast
        from ..features.node_features_v2 import extract_slide_node_features_v2
        from ..features.node_features_v2 import FEATURE_NAMES_V2

        dummy_md5 = "0" * 32
        deck = _extract_ast(Path(input_path), "user_upload", "session", "", dummy_md5)

        all_decisions = []
        plan_slides = []
        shape_table = {}
        for slide_idx, slide_obj in enumerate(prs.slides):
            shape_table[slide_idx] = list(_walk_shapes(slide_obj))

        for slide_idx, ast_slide in enumerate(deck["slides"]):
            slide_info = {"slide_number": slide_idx + 1, "decisions": [], "summary": {}}
            ast_nodes_flat = flatten_nodes(ast_slide["nodes"])
            if not ast_nodes_flat:
                slide_info["summary"] = {"total": 0, "applied": 0, "review": 0, "preserved": 0}
                analysis.slides.append(slide_info)
                continue

            feature_dicts = extract_slide_node_features_v2(ast_slide)
            node_ids = [nd["id"] for nd in ast_nodes_flat]

            shape_map = {}
            for shape in shape_table.get(slide_idx, []):
                sid = getattr(shape, "shape_id", None)
                if sid is not None:
                    shape_map[sid] = shape

            decisions = self.engine.decide_batch(feature_dicts)
            decisions = self.engine.policy.apply_slide_budget(decisions)

            changed = no_change = unsupported = failed = review = preserved = noop = 0
            mutation_results = []
            for ni, dec in enumerate(decisions):
                nid = node_ids[ni]
                node_shape_id = ast_nodes_flat[ni].get("shape_id")
                target_shape = shape_map.get(node_shape_id) if node_shape_id is not None else None

                entry = {
                    "node_id": nid,
                    "shape_id": node_shape_id,
                    "predicted_action": dec["action"],
                    "confidence": dec["confidence"],
                    "policy": dec["policy"],
                    "reason": dec["reason"],
                }

                if dec["policy"] == APPLY and dec["action"] in APPLYABLE and target_shape is not None:
                    mr = self.mutation_engine.apply(target_shape, dec)
                    md = mr.to_dict()
                    entry["mutation"] = md
                    mutation_results.append(md)
                    if mr.status == "CHANGED":
                        changed += 1
                    elif mr.status == "NO_CHANGE":
                        no_change += 1
                    elif mr.status == "UNSUPPORTED":
                        unsupported += 1
                    elif mr.status == "FAILED":
                        failed += 1
                    else:
                        preserved += 1
                elif dec["policy"] == REVIEW:
                    review += 1
                elif dec["policy"] == NOOP:
                    noop += 1
                else:
                    preserved += 1

                slide_info["decisions"].append(entry)
                all_decisions.append(entry)

            slide_info["summary"] = {
                "total": len(decisions),
                "changed": changed,
                "no_change": no_change,
                "unsupported": unsupported,
                "failed": failed,
                "review": review,
                "preserved": preserved + noop,
            }
            slide_info["mutation_results"] = [
                m.to_dict() if hasattr(m, "to_dict") else m
                for m in mutation_results
            ]
            analysis.slides.append(slide_info)
            plan_slides.append({"slide": slide_idx + 1, "decisions": slide_info["decisions"]})

        analysis.plan = {
            "plan_version": "v0.2",
            "generated_by": "BrandMorphPipeline",
            "deterministic_mutations": deterministic_mutations,
            "deterministic_changed": len(deterministic_mutations),
            "slides": plan_slides,
            "totals": self._totals_v2(all_decisions),
        }

        # --- STAGE 4: INTEGRITY VERIFICATION ---
        import hashlib
        input_hash = hashlib.sha256(Path(input_path).read_bytes()).hexdigest()
        integrity = {"input_sha256": input_hash, "deterministic_mutations": len(deterministic_mutations)}

        if output_path:
            prs.save(output_path)
            analysis.output_path = output_path
            output_hash = hashlib.sha256(Path(output_path).read_bytes()).hexdigest()
            integrity["output_sha256"] = output_hash
            integrity["binary_changed"] = input_hash != output_hash
            integrity["content_changed"] = integrity["binary_changed"]
            if not integrity["binary_changed"] and deterministic_mutations:
                integrity["integrity_failure"] = True

        analysis.integrity = integrity
        return analysis

    def _apply_deterministic_brand(self, prs) -> list[dict]:
        """Applies visible brand styling to every slide. Always runs before ML."""
        bp = self.profile
        mutations = []

        bg_color = RGBColor(*bp._hex_tuple(bp.dark_hex))
        card_color = RGBColor(*bp._hex_tuple(bp.card_hex))
        gold_color = bp.gold_rgb
        white_color = bp.white_rgb

        for slide_idx, slide in enumerate(prs.slides):
            # 1. Background
            try:
                old_bg = None
                try:
                    if slide.background.fill.type == 1:
                        old_bg = str(slide.background.fill.fore_color.rgb)
                except Exception:
                    pass
                slide.background.fill.solid()
                slide.background.fill.fore_color.rgb = bg_color
                mutations.append({
                    "slide": slide_idx + 1, "stage": "DETERMINISTIC",
                    "property": "slide.background", "shape": "(background)",
                    "before": old_bg or "(inherit)", "after": str(bg_color),
                    "visible_expected": True,
                })
            except Exception:
                pass

            for shape in _walk_shapes(slide):
                shape_id = getattr(shape, "shape_id", 0)
                shape_name = shape.name or ""
                has_tf = shape.has_text_frame

                # 2. Card/rectangle shapes: brand fill + border
                st = str(getattr(shape, "shape_type", ""))
                if "AUTO_SHAPE" in st or "FREEFORM" in st:
                    try:
                        if shape.fill.type == 1:
                            old_fill = str(shape.fill.fore_color.rgb)
                            shape.fill.fore_color.rgb = card_color
                            mutations.append({
                                "slide": slide_idx + 1, "stage": "DETERMINISTIC",
                                "property": "fill.color", "shape": shape_name,
                                "shape_id": shape_id,
                                "before": old_fill, "after": str(card_color),
                                "visible_expected": True,
                            })
                    except Exception:
                        pass
                    try:
                        if shape.line and shape.line.fill.type == 1:
                            old_line = str(shape.line.color.rgb) if shape.line.color else "(none)"
                            shape.line.color.rgb = RGBColor(0, 255, 255)
                            mutations.append({
                                "slide": slide_idx + 1, "stage": "DETERMINISTIC",
                                "property": "line.color", "shape": shape_name,
                                "shape_id": shape_id,
                                "before": old_line, "after": "#00FFFF",
                                "visible_expected": True,
                            })
                    except Exception:
                        pass

                # 3. Text normalization
                if not has_tf:
                    continue
                is_title = self._is_title_like(shape, slide_idx)
                for p in shape.text_frame.paragraphs:
                    for run in p.runs:
                        font = run.font

                        # Font family
                        old_font = font.name
                        target_font = bp.heading_font if is_title else bp.body_font
                        if old_font != target_font:
                            font.name = target_font
                            mutations.append({
                                "slide": slide_idx + 1, "stage": "DETERMINISTIC",
                                "property": "font.name", "shape": shape_name,
                                "shape_id": shape_id,
                                "before": old_font or "(inherited)", "after": target_font,
                                "visible_expected": True,
                            })

                        # Font color
                        try:
                            old_color = None
                            if font.color and font.color.rgb:
                                old_color = str(font.color.rgb)
                            target_color = gold_color if is_title else white_color
                            if old_color != str(target_color):
                                font.color.rgb = target_color
                                mutations.append({
                                    "slide": slide_idx + 1, "stage": "DETERMINISTIC",
                                    "property": "font.color", "shape": shape_name,
                                    "shape_id": shape_id,
                                    "before": old_color or "(theme)", "after": str(target_color),
                                    "visible_expected": True,
                                })
                        except Exception:
                            pass
        return mutations

    def _is_title_like(self, shape, slide_idx) -> bool:
        try:
            name_lower = (shape.name or "").lower()
            if "title" in name_lower:
                return True
            if not shape.has_text_frame:
                return False
            tf = shape.text_frame
            for p in tf.paragraphs:
                for r in p.runs:
                    if r.font.size and r.font.size.pt >= 20:
                        return True
            y = shape.top / 914400.0 if shape.top else 0
            h = shape.height / 914400.0 if shape.height else 0
            return y < 1.5 and h > 0.5
        except Exception:
            return False
        """Compute a minimal V2-compatible feature dict from a python-pptx shape."""
        try:
            x = shape.left / 914400.0 if shape.left else 0.0
            y = shape.top / 914400.0 if shape.top else 0.0
            w = shape.width / 914400.0 if shape.width else 0.0
            h = shape.height / 914400.0 if shape.height else 0.0
        except Exception:
            return None

        st = str(shape.shape_type) if hasattr(shape, "shape_type") else ""
        text = _shape_text(shape)

        has_tf = shape.has_text_frame
        font_sizes, bolds, italics = [], [], []
        if has_tf:
            for p in shape.text_frame.paragraphs:
                for r in p.runs:
                    if r.font.size:
                        font_sizes.append(r.font.size.pt)
                    if r.font.bold is not None:
                        bolds.append(r.font.bold)
                    if r.font.italic is not None:
                        italics.append(r.font.italic)

        eff_size = font_sizes[0] if font_sizes else 0.0
        chars = len(text)
        words = len(text.split())
        depth = 0

        fd = {
            "is_text": int(bool(text)),
            "is_shape": int("AUTO_SHAPE" in st or "FREEFORM" in st),
            "is_arrow": int("ARROW" in st.upper()),
            "is_line": int("LINE" in st or "CONNECTOR" in st.upper()),
            "is_image": int("PICTURE" in st),
            "is_table": int(shape.has_table if hasattr(shape, "has_table") else False),
            "is_chart": int(shape.has_chart if hasattr(shape, "has_chart") else False),
            "is_group": int("GROUP" in st),
            "x": round(x, 5), "y": round(y, 5),
            "w": round(w, 5), "h": round(h, 5),
            "cx": round(x + w / 2, 5), "cy": round(y + h / 2, 5),
            "area_log1p": round(np.log1p(abs(w * h)), 4),
            "aspect": round(min(max(w / h, 0) if h else 0, 50), 4),
            "rotation_flag": int(abs(getattr(shape, "rotation", 0)) > 1),
            "container_depth": depth,
            "font_size_pt": eff_size,
            "eff_size_pt": eff_size,
            "size_rel_max": 0.0, "size_rel_median": 0.0, "is_largest_font": 0,
            "bold": int(any(bolds)), "italic": int(any(italics)),
            "text_len_log1p": round(np.log1p(chars), 4),
            "word_count_log1p": round(np.log1p(words), 4),
            "numeric_ratio": round(sum(c.isdigit() for c in text) / max(chars, 1), 4) if chars else 0.0,
            "upper_ratio": round(sum(c.isupper() for c in text) / max(sum(c.isalpha() for c in text), 1), 4) if chars else 0.0,
            "guidance_flag": int(("font guidance" in text.lower()) or ("do not change" in text.lower())),
            "fill_present": 0,
            "y_rank_frac": 0.0, "x_rank_frac": 0.0, "nn_dist": 0.0,
            "ctx_n_nodes_log1p": 0.0, "ctx_n_text_frac": 0.0,
        }
        return fd

    @staticmethod
    def _totals_v2(all_decisions: list[dict]) -> dict:
        policy_counts: dict[str, int] = {}
        action_counts: dict[str, int] = {}
        mutation_statuses: dict[str, int] = {}
        for d in all_decisions:
            policy_counts[d.get("policy", "?")] = policy_counts.get(d.get("policy", "?"), 0) + 1
            action_counts[d.get("predicted_action", "?")] = action_counts.get(d.get("predicted_action", "?"), 0) + 1
            mr = d.get("mutation", {})
            if mr:
                st = mr.get("status", "?")
                mutation_statuses[st] = mutation_statuses.get(st, 0) + 1
        return {
            "nodes_total": len(all_decisions),
            "by_policy": dict(policy_counts),
            "by_action": dict(action_counts),
            "mutation_verification": dict(mutation_statuses),
            "changed": mutation_statuses.get("CHANGED", 0),
            "no_change": mutation_statuses.get("NO_CHANGE", 0),
            "failed": mutation_statuses.get("FAILED", 0),
        }

    def _totals(decisions: list[dict]) -> dict:
        counts: dict[str, int] = {}
        for d in decisions:
            key = d.get("policy", "unknown")
            counts[key] = counts.get(key, 0) + 1
        by_action: dict[str, int] = {}
        for d in decisions:
            k = d.get("predicted_action", "?")
            by_action[k] = by_action.get(k, 0) + 1
        return {"nodes_total": len(decisions), **{f"policy_{k.lower()}": v for k, v in counts.items()},
                "by_action": by_action}
