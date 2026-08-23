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
from ..rules.brand_tokens import BRAND_COLORS

BRAND_FONT_BODY = "Arial"
BRAND_GOLD = RGBColor(0xFF, 0xB8, 0x1C)
BRAND_WHITE = RGBColor(0xFF, 0xFF, 0xFF)
BRAND_DARK = RGBColor(0x03, 0x0C, 0x1E)

LEGACY_COLOR_MAP = {
    RGBColor(0xFF, 0xC0, 0x00): BRAND_GOLD,
    RGBColor(0xFF, 0xB2, 0x12): BRAND_GOLD,
    RGBColor(0xEB, 0xAC, 0x00): BRAND_GOLD,
}

RESIZE_MAP = {12.0: 10.0, 14.0: 12.0, 16.0: 12.0, 20.0: 12.0,
              32.0: 28.0, 36.0: 24.0, 16.7: 12.0}

APPLYABLE = {"RESTYLE", "RESIZE", "RECOLOR", "REMOVE"}


class DeckAnalysis:
    def __init__(self):
        self.deck_id = str(uuid.uuid4())[:8]
        self.slides: list[dict] = []
        self.plan: dict = {}
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

    def __init__(self):
        from morphlite.inference.decision import DecisionEngine

        self.engine = DecisionEngine()

    def process(self, input_path: str, output_path: str | None = None) -> DeckAnalysis:
        analysis = DeckAnalysis()
        analysis.input_path = input_path

        prs = pptx.Presentation(input_path)
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

            decisions = self.engine.decide_batch(feature_dicts)
            shapes_list = shape_table.get(slide_idx, [])

            applied = review = preserved = noop = 0
            for ni, dec in enumerate(decisions):
                nid = node_ids[ni]
                sid = int(nid.rsplit("__n", 1)[1])
                si_shape = shapes_list[sid] if sid < len(shapes_list) else None

                entry = {
                    "shape_index": sid,
                    "node_id": nid,
                    "predicted_action": dec["action"],
                    "confidence": dec["confidence"],
                    "policy": dec["policy"],
                    "reason": dec["reason"],
                }

                if dec["policy"] == APPLY and dec["action"] in APPLYABLE and si_shape is not None:
                    self._apply_mutation(si_shape, dec)
                    entry["executed"] = True
                    applied += 1
                elif dec["policy"] == REVIEW:
                    entry["executed"] = False
                    review += 1
                elif dec["policy"] == NOOP:
                    entry["executed"] = False
                    noop += 1
                else:
                    entry["executed"] = False
                    preserved += 1

                slide_info["decisions"].append(entry)
                all_decisions.append(entry)

            slide_info["summary"] = {
                "total": len(decisions),
                "applied": applied,
                "review": review,
                "preserved": preserved + noop,
            }
            analysis.slides.append(slide_info)
            plan_slides.append({"slide": slide_idx + 1, "decisions": slide_info["decisions"]})

        analysis.plan = {
            "plan_version": "v0.1",
            "generated_by": "BrandMorphPipeline",
            "slides": plan_slides,
            "totals": self._totals(all_decisions),
        }

        if output_path:
            prs.save(output_path)
            analysis.output_path = output_path

        return analysis

    def _apply_mutation(self, shape, decision: dict):
        action = decision["action"]
        if action == "REMOVE":
            try:
                shape._element.getparent().remove(shape._element)
            except Exception:
                pass
            return
        if not shape.has_text_frame:
            return
        for p in shape.text_frame.paragraphs:
            for run in p.runs:
                font = run.font
                if action == "RESTYLE":
                    if font.name and font.name.lower() not in ("roboto", "arial"):
                        font.name = BRAND_FONT_BODY
                elif action == "RESIZE":
                    sz = font.size
                    if sz is None:
                        continue
                    pt = sz.pt
                    mapped = RESIZE_MAP.get(round(pt, 1))
                    if mapped is not None:
                        font.size = Pt(mapped)
                elif action == "RECOLOR":
                    try:
                        if font.color and font.color.rgb:
                            rgb = font.color.rgb
                            mapped = LEGACY_COLOR_MAP.get(rgb)
                            if mapped:
                                font.color.rgb = mapped
                    except Exception:
                        pass

    def _compute_inline_features(self, shape) -> dict | None:
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
