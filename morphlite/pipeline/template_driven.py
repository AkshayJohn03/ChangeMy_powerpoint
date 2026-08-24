"""BrandMorph v0.3: Template-driven transformation.

Opens the brand template as the base presentation, then imports content from
the raw deck into matching template slides. The template's layouts, masters,
and backgrounds provide all branding automatically.

    result = TemplateDrivenPipeline(template_path).process(raw_deck_path, output_path)
"""
from __future__ import annotations

import copy
import hashlib
import os
import re
import uuid
from pathlib import Path

import numpy as np
import pptx
from pptx.util import Pt, Inches

from ..pipeline.brand_profile import DEFAULT_PROFILE, BrandProfile


def classify_slide(slide) -> str:
    """Heuristic slide-type classifier."""
    layout = slide.slide_layout.name if slide.slide_layout else ""
    texts = []
    max_font = 0
    n_shapes = len(slide.shapes)
    has_image = False
    title_text = ""

    for shape in slide.shapes:
        try:
            if hasattr(shape, "image"):
                w = shape.width / 914400.0
                h = shape.height / 914400.0
                if w > 10 and h > 5:
                    has_image = True
        except (ValueError, AttributeError):
            pass
        if shape.has_text_frame:
            t = shape.text_frame.text.strip()
            if t:
                texts.append(t)
            for p in shape.text_frame.paragraphs:
                for r in p.runs:
                    if r.font.size:
                        max_font = max(max_font, r.font.size.pt)
                        if not title_text and r.text.strip():
                            title_text = r.text.strip()

    all_text = " ".join(texts).lower()

    if "thank" in all_text:
        return "THANK_YOU"
    if "agenda" in all_text:
        return "AGENDA"
    if "who we are" in all_text:
        return "WHO_WE_ARE"
    if "case stud" in all_text or "case study" in all_text:
        if n_shapes > 10:
            return "CASE_STUDY"
        return "SECTION_SPLITTER"
    if max_font >= 28 or "title" in layout.lower() or (title_text and len(title_text) < 80 and max_font >= 24):
        return "TITLE"
    if n_shapes <= 5:
        return "GENERIC_MINIMAL"
    return "GENERIC_CONTENT"


class TemplateDrivenPipeline:
    def __init__(self, template_path: str, profile: BrandProfile | None = None):
        self.template_path = template_path
        self.profile = profile or DEFAULT_PROFILE
        self.template_prs = pptx.Presentation(template_path)

        # Load ML slide type classifier
        self._clf = None
        clf_path = Path(__file__).resolve().parent.parent / "models" / "slide_type_classifier.joblib"
        if clf_path.exists():
            import joblib
            bundle = joblib.load(clf_path)
            self._clf = bundle["model"]
            self._clf_features = bundle["feature_names"]
            self._clf_labels = bundle["labels"]

        # Classify template slides
        self.template_types = {}
        for si, slide in enumerate(self.template_prs.slides):
            stype = classify_slide(slide)
            self.template_types[si] = stype

    def _classify_with_ml(self, slide) -> str:
        """ML classifier with heuristic fallback."""
        if self._clf is not None:
            try:
                from ..training.slide_type_classifier import extract_slide_features
                feats = np.array([extract_slide_features(slide)])
                pred_idx = self._clf.predict(feats)[0]
                return str(pred_idx)
            except Exception:
                pass
        return classify_slide(slide)

    def process(self, raw_deck_path: str, output_path: str | None = None) -> dict:
        raw_prs = pptx.Presentation(raw_deck_path)
        input_hash = hashlib.sha256(Path(raw_deck_path).read_bytes()).hexdigest()

        slide_type_map = []
        for si, slide in enumerate(raw_prs.slides):
            stype = self._classify_with_ml(slide)
            slide_type_map.append({"slide": si + 1, "type": stype})

        # Find best template slide for each type
        type_to_template = {}
        for si, stype in self.template_types.items():
            if stype not in type_to_template:
                type_to_template[stype] = si

        # Build output from template (keep template slides as reference/layout source)
        output_prs = pptx.Presentation(self.template_path)
        n_template_slides = len(output_prs.slides)

        # Map template layouts by name for easy lookup
        layout_map = {}
        for si, slide in enumerate(self.template_prs.slides):
            stype = self.template_types.get(si, "GENERIC_CONTENT")
            layout_name = slide.slide_layout.name
            if stype not in layout_map:
                layout_map[stype] = layout_name

        # Add slides matching raw deck structure
        for raw_idx, raw_slide in enumerate(raw_prs.slides):
            raw_type = slide_type_map[raw_idx]["type"]

            # Find the best template layout for this type
            layout_name = layout_map.get(raw_type, layout_map.get("GENERIC_CONTENT", ""))
            layout = None
            for l in output_prs.slide_layouts:
                if l.name == layout_name:
                    layout = l
                    break
            if layout is None:
                layout = output_prs.slide_layouts[0]

            new_slide = output_prs.slides.add_slide(layout)

            # Copy text content from raw slide
            raw_texts = []
            for shape in raw_slide.shapes:
                if shape.has_text_frame and shape.text_frame.text.strip():
                    raw_texts.append({
                        "text": shape.text_frame.text,
                        "size": None,
                        "bold": None,
                        "is_title": "title" in (shape.name or "").lower(),
                    })
                    for p in shape.text_frame.paragraphs:
                        for r in p.runs:
                            if r.font.size:
                                raw_texts[-1]["size"] = r.font.size.pt
                            if r.font.bold is not None:
                                raw_texts[-1]["bold"] = r.font.bold

            # Place text on the new slide
            if raw_texts:
                # Add a title text box
                title_text = raw_texts[0]
                txbox = new_slide.shapes.add_textbox(
                    Inches(0.5), Inches(0.3), Inches(12), Inches(1.2)
                )
                tf = txbox.text_frame
                tf.word_wrap = True
                p = tf.paragraphs[0]
                run = p.add_run()
                run.text = title_text["text"][:200]
                run.font.size = Pt(28)
                run.font.color.rgb = __import__("pptx.dml.color", fromlist=["RGBColor"]).RGBColor(0xFF, 0xB8, 0x1C)
                run.font.name = "Times New Roman"
                run.font.bold = True

                # Add body text boxes for remaining content
                y_offset = 1.8
                for rt in raw_texts[1:6]:  # limit to 5 body items
                    if not rt["text"].strip():
                        continue
                    bx = new_slide.shapes.add_textbox(
                        Inches(0.8), Inches(y_offset), Inches(11.5), Inches(0.8)
                    )
                    btf = bx.text_frame
                    btf.word_wrap = True
                    bp = btf.paragraphs[0]
                    br = bp.add_run()
                    br.text = rt["text"][:300]
                    br.font.size = Pt(14)
                    br.font.color.rgb = __import__("pptx.dml.color", fromlist=["RGBColor"]).RGBColor(0xFF, 0xFF, 0xFF)
                    br.font.name = "Arial"
                    y_offset += 0.9

        # Save
        if output_path:
            output_prs.save(output_path)

        output_hash = hashlib.sha256(Path(output_path).read_bytes()).hexdigest() if output_path else ""

        # Analysis summary
        decisions = []
        for si, stm in enumerate(slide_type_map):
            decisions.append({
                "raw_slide": stm["slide"],
                "classified_type": stm["type"],
                "template_layout": layout_map.get(stm["type"], "GENERIC_CONTENT"),
            })

        return {
            "deck_id": str(uuid.uuid4())[:8],
            "input_path": raw_deck_path,
            "output_path": output_path,
            "input_sha256": input_hash,
            "output_sha256": output_hash,
            "binary_changed": input_hash != output_hash,
            "slide_type_map": slide_type_map,
            "decisions": decisions,
            "n_slides": len(raw_prs.slides),
            "template_used": self.template_path,
        }


