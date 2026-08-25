"""Phase 12.8: Template Filling Pipeline.

Opens the brand template, duplicates matching slides, replaces text content
within existing shapes. All template styling (backgrounds, shapes, transparency,
borders) is preserved because we're filling the template, not mutating the raw deck.
"""
from __future__ import annotations

import copy
import hashlib
import os
import re
import uuid
from pathlib import Path

import pptx
from pptx.util import Pt, Inches
from pptx.dml.color import RGBColor
from pptx.oxml.ns import qn

from ..pipeline.brand_profile import DEFAULT_PROFILE, BrandProfile


def _duplicate_slide(prs, slide_index: int):
    """Deep-copy a slide within the same presentation, preserving all shapes,
    backgrounds, and styling. Returns the new slide."""
    template_slide = prs.slides[slide_index]
    blank_layout = template_slide.slide_layout

    # Add a new slide with the same layout
    new_slide = prs.slides.add_slide(blank_layout)

    # Remove any placeholder shapes that came with the layout
    for ph in list(new_slide.placeholders):
        ph_elem = ph._element
        ph_elem.getparent().remove(ph_elem)

    # Deep-copy all shapes from the template slide
    for shape in template_slide.shapes:
        el = copy.deepcopy(shape._element)
        new_slide.shapes._spTree.append(el)

    # Copy background if the template slide has explicit background
    try:
        src_bg = template_slide.background
        dst_bg = new_slide.background
        if src_bg.fill.type is not None:
            import copy as cp
            bg_xml = cp.deepcopy(src_bg._element)
            # Replace the new slide's background element
            new_slide._element.remove(new_slide._element.find(qn("p:cSld")).find(qn("p:bg")))
            new_slide._element.find(qn("p:cSld")).insert(0, bg_xml.find(qn("p:bg")))
    except Exception:
        pass

    return new_slide


def _set_text_preserving_style(shape, new_text: str, font_size: float | None = None):
    """Replace text content in a shape while preserving all formatting.
    If the shape has multiple paragraphs, fills the first and clears the rest."""
    if not shape.has_text_frame:
        return

    tf = shape.text_frame
    paragraphs = tf.paragraphs

    if not paragraphs:
        return

    # Use the first paragraph's first run as a style template
    first_para = paragraphs[0]
    if first_para.runs:
        template_run = first_para.runs[0]
        template_font_name = template_run.font.name
        template_font_size = template_run.font.size
        template_font_color = None
        try:
            if template_run.font.color and template_run.font.color.rgb:
                template_font_color = template_run.font.color.rgb
        except Exception:
            pass
        template_bold = template_run.font.bold
    else:
        template_font_name = None
        template_font_size = Pt(font_size) if font_size else None
        template_font_color = None
        template_bold = None

    # Clear all paragraphs except the first
    for p in paragraphs[1:]:
        p._p.getparent().remove(p._p)

    # Clear all runs in the first paragraph
    for r in list(first_para.runs):
        r._r.getparent().remove(r._r)

    # Add the new text as a single run
    run = first_para.add_run()
    run.text = new_text

    # Apply the preserved formatting
    if template_font_name:
        run.font.name = template_font_name
    if template_font_size:
        run.font.size = template_font_size
    elif font_size:
        run.font.size = Pt(font_size)
    if template_font_color:
        run.font.color.rgb = template_font_color
    if template_bold is not None:
        run.font.bold = template_bold


def _add_text_box(slide, text: str, left: float, top: float, width: float, height: float,
                  font_size: float = 10, font_name: str = "Arial",
                  color: str = "FFFFFF", bold: bool = False):
    """Add a text box as a new layer above existing shapes."""
    txbox = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
    tf = txbox.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    run = p.add_run()
    run.text = text
    run.font.size = Pt(font_size)
    run.font.name = font_name
    run.font.color.rgb = RGBColor.from_string(color)
    run.font.bold = bold
    return txbox


def _get_text_content(slide) -> list[dict]:
    """Extract all text content from a slide's shapes, ordered by position."""
    items = []
    for shape in slide.shapes:
        if not shape.has_text_frame:
            continue
        text = shape.text_frame.text.strip()
        if not text:
            continue
        try:
            top = shape.top / 914400.0
            left = shape.left / 914400.0
        except Exception:
            top, left = 0, 0

        max_size = 0
        font_name = None
        for p in shape.text_frame.paragraphs:
            for r in p.runs:
                if r.font.size:
                    max_size = max(max_size, r.font.size.pt)
                if r.font.name:
                    font_name = r.font.name

        is_title = "title" in (shape.name or "").lower() or max_size >= 20

        items.append({
            "text": text,
            "top": top,
            "left": left,
            "max_size": max_size,
            "font_name": font_name,
            "is_title": is_title,
            "shape_name": shape.name,
        })

    items.sort(key=lambda x: (x["top"], x["left"]))
    return items


def _classify_template_slide(slide, slide_idx: int) -> str:
    """Classify template slides by their known structure."""
    if slide_idx == 0:
        return "TITLE"
    texts = []
    for shape in slide.shapes:
        if shape.has_text_frame:
            texts.append(shape.text_frame.text.strip().lower())
    all_text = " ".join(texts)

    if "agenda" in all_text:
        return "AGENDA"
    if "who we are" in all_text:
        return "WHO_WE_ARE"
    if "case stud" in all_text and len(slide.shapes) < 8:
        return "SECTION_SPLITTER"
    if "thank" in all_text:
        return "THANK_YOU"
    if slide_idx == 3 or slide_idx == 4:
        return "GENERIC_CONTENT"
    if slide_idx == 5:
        return "EMPTY_TITLE"
    if slide_idx == 6:
        return "SECTION_SPLITTER"
    return "GENERIC_CONTENT"


def _classify_raw_slide(slide, slide_idx: int, n_slides: int) -> str:
    """Classify raw slides to match them to template types."""
    texts = []
    max_font = 0.0
    n_shapes = len(slide.shapes)
    has_image = False

    for shape in slide.shapes:
        try:
            if "PICTURE" in str(shape.shape_type):
                w = shape.width / 914400.0 if shape.width else 0
                h = shape.height / 914400.0 if shape.height else 0
                if w > 10 and h > 5:
                    has_image = True
        except Exception:
            pass
        if shape.has_text_frame:
            t = shape.text_frame.text.strip()
            if t:
                texts.append(t)
            for p in shape.text_frame.paragraphs:
                for r in p.runs:
                    if r.font.size:
                        max_font = max(max_font, r.font.size.pt)

    all_text = " ".join(texts).lower()

    if slide_idx == 0 and n_slides > 1:
        return "TITLE"
    if "thank" in all_text:
        return "THANK_YOU"
    if "agenda" in all_text:
        return "AGENDA"
    if "who we are" in all_text or "akkodis" in all_text and n_shapes > 15:
        return "WHO_WE_ARE"
    if "case stud" in all_text and n_shapes < 8:
        return "SECTION_SPLITTER"
    if "case stud" in all_text or "challenge" in all_text or "solution" in all_text or "results" in all_text:
        return "CASE_STUDY"
    if max_font >= 28:
        return "TITLE"
    if n_shapes <= 3:
        return "EMPTY_TITLE"
    return "GENERIC_CONTENT"


class TemplateFiller:
    """Fills the brand template with content from a raw deck.

    The template provides ALL styling. We only replace text content
    and add new text layers where the raw deck has more content
    than the template has shapes.
    """

    def __init__(self, template_path: str):
        self.template_path = template_path

        # Classify template slides
        tpl_prs = pptx.Presentation(template_path)
        self.template_slide_types = {}
        for si, slide in enumerate(tpl_prs.slides):
            self.template_slide_types[si] = _classify_template_slide(slide, si)

    def process(self, raw_deck_path: str, output_path: str | None = None) -> dict:
        input_hash = hashlib.sha256(Path(raw_deck_path).read_bytes()).hexdigest()

        # Open the brand template as the base
        prs = pptx.Presentation(self.template_path)

        # Classify raw slides
        raw_prs = pptx.Presentation(raw_deck_path)
        raw_slides = []
        for si, slide in enumerate(raw_prs.slides):
            stype = _classify_raw_slide(slide, si, len(raw_prs.slides))
            texts = _get_text_content(slide)
            raw_slides.append({"index": si, "type": stype, "texts": texts})

        # Map template slide indices by type
        type_to_tpl_idx = {}
        for tidx, ttype in self.template_slide_types.items():
            if ttype not in type_to_tpl_idx:
                type_to_tpl_idx[ttype] = tidx

        # Strategy:
        # 1. For slides 1-10 of the output, use the template's own slides
        #    (replacing text content where raw content exists)
        # 2. For slides beyond 10, duplicate the GENERIC_CONTENT template slide
        # 3. Thank you slides from the template are kept at the end

        n_template = len(prs.slides)
        n_raw = len(raw_slides)

        # Find the thank-you slide indices in the template (keep at end)
        thank_you_indices = [i for i, t in self.template_slide_types.items() if t == "THANK_YOU"]

        # Find the generic content template index (for duplication)
        generic_idx = type_to_tpl_idx.get("GENERIC_CONTENT", 3)

        # Process: replace text in template slides where raw content matches
        mutations = []
        raw_slide_map = {}  # raw_idx -> (template_idx, action)

        for ri, rs in enumerate(raw_slides):
            rtype = rs["type"]

            # Find matching template slide
            tpl_idx = type_to_tpl_idx.get(rtype)
            if tpl_idx is None:
                # Fallback: use generic content
                tpl_idx = generic_idx

            raw_slide_count = sum(1 for r in raw_slides[:ri+1] if r["type"] == rtype)

            if ri < n_template:
                # This raw slide maps to a template slide directly
                raw_slide_map[ri] = (tpl_idx, "fill_existing")
            else:
                # Need to duplicate the generic template slide
                raw_slide_map[ri] = (generic_idx, "duplicate")

        # Now build the output presentation
        # Strategy: use the template presentation, modify slides in-place where
        # raw content maps to them, and add new slides for excess raw content

        # For each raw slide, find the matching template slide and replace text
        for ri, rs in enumerate(raw_slides):
            tpl_idx, action = raw_slide_map[ri]

            if action == "fill_existing" and ri < n_template:
                # Replace text in the existing template slide
                template_slide = prs.slides[tpl_idx]
                self._fill_slide_text(template_slide, rs["texts"])
            elif action == "duplicate":
                # Duplicate the generic template slide and fill it
                new_slide = _duplicate_slide(prs, generic_idx)
                self._fill_slide_text(new_slide, rs["texts"])

        # Remove unused template slides (those without matching raw content)
        # This is tricky in python-pptx, so we'll mark them for manual removal
        # For now, keep all template slides

        output_hash = ""
        if output_path:
            prs.save(output_path)
            output_hash = hashlib.sha256(Path(output_path).read_bytes()).hexdigest()

        binary_changed = True
        if output_path and os.path.exists(output_path):
            output_hash = hashlib.sha256(Path(output_path).read_bytes()).hexdigest()
            binary_changed = input_hash != output_hash

        return {
            "deck_id": str(uuid.uuid4())[:8],
            "input_path": raw_deck_path,
            "output_path": output_path,
            "n_raw_slides": n_raw,
            "n_template_slides": n_template,
            "binary_changed": binary_changed,
            "input_sha256": input_hash,
            "output_sha256": output_hash,
            "slide_type_map": [
                {"slide": rs["index"] + 1, "type": rs["type"]}
                for rs in raw_slides
            ],
            "mutations": mutations,
            "template_used": self.template_path,
        }

    def _fill_slide_text(self, slide, raw_texts: list[dict]):
        """Replace text content in a slide's existing text frames with raw deck content."""
        # Get all text-bearing shapes from the template slide, ordered by position
        text_shapes = []
        for shape in slide.shapes:
            if not shape.has_text_frame:
                continue
            text = shape.text_frame.text.strip()
            if not text:
                continue
            # Skip guidance text
            if "font guidance" in text.lower() or "do not change" in text.lower() or "do not move" in text.lower():
                continue
            try:
                top = shape.top / 914400.0
            except Exception:
                top = 0
            max_size = 0
            for p in shape.text_frame.paragraphs:
                for r in p.runs:
                    if r.font.size:
                        max_size = max(max_size, r.font.size.pt)
            text_shapes.append({
                "shape": shape, "top": top,
                "max_size": max_size,
                "current_text": text,
            })

        text_shapes.sort(key=lambda x: (x["top"], -x["max_size"]))

        # Sort raw texts: titles first, then body
        raw_sorted = sorted(raw_texts, key=lambda x: (not x.get("is_title", False), x["top"]))

        # Map raw texts to template shapes
        for i, ts in enumerate(text_shapes):
            if i < len(raw_sorted):
                raw = raw_sorted[i]
                _set_text_preserving_style(
                    ts["shape"], raw["text"],
                    font_size=raw["max_size"] if raw["max_size"] > 0 else None
                )
