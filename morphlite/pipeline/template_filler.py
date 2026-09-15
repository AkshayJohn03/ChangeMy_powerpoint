"""Phase 12.8: Template Filling Pipeline — Path 1 hard-coded matcher.

Opens the brand template, duplicates matching slides, replaces text content
within existing shapes. All template styling (backgrounds, shapes, transparency,
borders) is preserved because we're filling the template, not mutating the raw deck.
Keyword -> template slot -> fill with hard-coded scoring (100% Python, no ML).
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


# ---------------------------------------------------------------------------
# Keyword vocabularies — simple scored matching, not ML
# ---------------------------------------------------------------------------

# Raw TestPPT vocab: ADAS, Sensors, ECU, Validation, PASS/FAIL, Diagnostics, etc.
ADAS_SENSORS_KWS = [
    "adas", "sensor", "camera", "radar", "ultrasonic", "lidar",
    "perception", "actuation", "calibration",
    "acc", "adaptive cruise", "lka", "lca", "lane keep", "lane centering",
    "tsr", "traffic sign", "surround view", "svs", "aeb", "fcw",
    "hil", "hardware-in-the-loop", "sil", "mil",
]

ECU_DIAG_KWS = [
    "ecu", "can bus", "can ", "uds", "diagnostics", "diagnostic",
    "canoe", "capl", "vteststudio", "vt system", "flashing", "flash",
    "j1939", "lin bus", "ethernet",
]

VALIDATION_KWS = [
    "validation", "verification", "pass", "fail", "test case", "test design",
    "traceability", "bidirectional", "defect", "bug", "jira",
    "jenkins", "automation", "python", "webots", "yolo", "roboflow",
    "google colab", "simulation", "infotainment", "bluetooth", "usb",
    "requirement", "requirement to test", "v-model", "aspice",
]

AKKODIS_SVC_KWS = [
    "akkodis", "adecco", "smart industry", "talent & tech", "consulting",
    "service offering", "corporate overview", "microsoft partnership",
    "who we are", "about us", "global tech", "powerhouse",
    "engineering", "digital transformation", "workforce",
]

CASE_STUDY_KWS = [
    "case study", "case studies", "client challenge", "client challenges",
    "our solution", "results", "challenge", "solution",
    "ford", "bosch", "daimler", "volkswagen", "vw ", "harman", "aptiv",
    "apc", "pts ", "parking", "hmi", "la county", "voting", "technology provider",
    "project", "volkswagen | akkodis", "ford &", "general motors",
]

THANK_KWS = ["thank you", "thank-you", "thankyou", "any questions", "q&a", "questions?"]

AGENDA_KWS = ["agenda", "contents", "outline", "table of contents", "overview"]


def _duplicate_slide(prs, slide_index: int):
    """Deep-copy a slide within the same presentation, preserving all shapes,
    backgrounds, and styling. Returns the new slide.
    Preserves: shapes/arrows/backgrounds/borders/transparency via deepcopy of
    underlying XML elements (not rebuilding blank slide)."""
    template_slide = prs.slides[slide_index]
    blank_layout = template_slide.slide_layout

    # Add a new slide with the same layout
    new_slide = prs.slides.add_slide(blank_layout)

    # Remove any placeholder shapes that came with the layout
    for ph in list(new_slide.placeholders):
        ph_elem = ph._element
        ph_elem.getparent().remove(ph_elem)

    # Deep-copy all shapes from the template slide (preserves borders/transparency/arrows)
    for shape in template_slide.shapes:
        el = copy.deepcopy(shape._element)
        new_slide.shapes._spTree.append(el)

    # Copy background if the template slide has explicit background
    # Full-bleed bg_images at slides 0,1,9 are PICTURE shapes already copied above;
    # this handles solid bg_colors (001F33) and any p:bg picture fills.
    try:
        src_bg = template_slide.background
        if src_bg.fill.type is not None:
            import copy as cp
            bg_xml = cp.deepcopy(src_bg._element)
            bg_el = bg_xml.find(qn("p:bg"))
            if bg_el is not None:
                cSld = new_slide._element.find(qn("p:cSld"))
                old_bg = cSld.find(qn("p:bg"))
                if old_bg is not None:
                    cSld.remove(old_bg)
                cSld.insert(0, bg_el)
    except Exception:
        pass

    return new_slide


def _remove_first_n_slides(prs, n: int):
    """Remove first n slides from prs (used to drop original template slides after duplication)."""
    for _ in range(n):
        if len(prs.slides) == 0:
            break
        slide_id = prs.slides._sldIdLst[0]
        try:
            prs.part.drop_rel(slide_id.rId)
        except Exception:
            pass
        del prs.slides._sldIdLst[0]


def _set_text_preserving_style(shape, new_text: str, font_size: float | None = None):
    """Replace text content in a shape while preserving all formatting.
    If the shape has multiple paragraphs, fills the first and clears the rest.
    Empty new_text clears the shape but keeps the shape/border."""
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
        template_italic = template_run.font.italic
    else:
        template_font_name = None
        template_font_size = Pt(font_size) if font_size else None
        template_font_color = None
        template_bold = None
        template_italic = None

    # Clear all paragraphs except the first
    for p in paragraphs[1:]:
        p._p.getparent().remove(p._p)

    # Clear all runs in the first paragraph
    for r in list(first_para.runs):
        r._r.getparent().remove(r._r)

    # Add the new text as a single run (empty string clears)
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
        try:
            run.font.color.rgb = template_font_color
        except Exception:
            pass
    if template_bold is not None:
        run.font.bold = template_bold
    if template_italic is not None:
        run.font.italic = template_italic


def _add_text_box(slide, text: str, left: float, top: float, width: float, height: float,
                  font_size: float = 10, font_name: str = "Arial",
                  color: str = "FFFFFF", bold: bool = False):
    """Add a text box as a new layer above existing shapes. Uses template font/color."""
    txbox = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
    tf = txbox.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    run = p.add_run()
    run.text = text
    run.font.size = Pt(font_size)
    run.font.name = font_name
    try:
        run.font.color.rgb = RGBColor.from_string(color.replace("#", ""))
    except Exception:
        try:
            run.font.color.rgb = RGBColor(255, 255, 255)
        except Exception:
            pass
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
        font_color = "FFFFFF"
        bold = False
        for p in shape.text_frame.paragraphs:
            for r in p.runs:
                if r.font.size:
                    try:
                        max_size = max(max_size, r.font.size.pt)
                    except Exception:
                        pass
                if r.font.name:
                    font_name = r.font.name
                if r.font.bold:
                    bold = True
                try:
                    if r.font.color and r.font.color.rgb:
                        font_color = str(r.font.color.rgb)
                except Exception:
                    pass

        is_title = "title" in (shape.name or "").lower() or max_size >= 20

        items.append({
            "text": text,
            "top": top,
            "left": left,
            "max_size": max_size,
            "font_name": font_name,
            "font_color": font_color,
            "bold": bold,
            "is_title": is_title,
            "shape_name": shape.name,
        })

    items.sort(key=lambda x: (x["top"], x["left"]))
    return items


# ---------------------------------------------------------------------------
# Template slide classification — hard-coded for Brand_guideline_Akkodis 10 slides
# ---------------------------------------------------------------------------

def _classify_template_slide(slide, slide_idx: int) -> str:
    """Classify template slides by known structure + keyword scoring.
    Covers Akkodis service vocabulary and preserves GENERIC fallback."""
    texts = []
    for shape in slide.shapes:
        if shape.has_text_frame:
            t = shape.text_frame.text.strip().lower()
            if t:
                texts.append(t)
    all_text = " ".join(texts)

    # Deterministic baseline for the 10-slide Akkodis master (13.33x7.5in, 3 masters)
    baseline = {
        0: "TITLE",
        1: "AGENDA",
        2: "WHO_WE_ARE",
        3: "GENERIC_CONTENT",
        4: "GENERIC_CONTENT",
        5: "SECTION_SPLITTER",
        6: "CASE_STUDY",
        7: "THANK_YOU",
        8: "THANK_YOU",
        9: "CLOSING",
    }

    if slide_idx == 0:
        return "TITLE"
    if any(k in all_text for k in AGENDA_KWS):
        return "AGENDA"
    if "who we are" in all_text or "the adecco group" in all_text:
        return "WHO_WE_ARE"
    if ("case stud" in all_text) and len(slide.shapes) < 8:
        return "SECTION_SPLITTER"
    if "client challenges" in all_text and "our solution" in all_text:
        return "CASE_STUDY"
    if "leading us" in all_text and "technology provider" in all_text:
        return "CASE_STUDY"
    if any(k in all_text for k in THANK_KWS):
        return "THANK_YOU"
    # Service vocab on template should map to WHO_WE_ARE / GENERIC
    if "global smart industry leader" in all_text:
        return "GENERIC_CONTENT"
    if slide_idx in baseline:
        return baseline[slide_idx]
    return "GENERIC_CONTENT"


def _score_keywords(text: str, keywords: list[str]) -> int:
    """Simple keyword hit counter (case-insensitive substring)."""
    score = 0
    for kw in keywords:
        if kw.lower() in text:
            score += 1
    return score


def _classify_raw_slide(slide, slide_idx: int, n_slides: int) -> str:
    """Classify raw slides to match them to template types via keyword scoring.
    Covers TestPPT vocabulary: ADAS, Sensors, ECU, Validation, PASS/FAIL, Diagnostics,
    plus Akkodis service vocab. Every return maps to template index 0-9."""
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
                    try:
                        if r.font.size:
                            max_font = max(max_font, r.font.size.pt)
                    except Exception:
                        pass

    all_text = " ".join(texts).lower()

    # Positional TITLE — first slide is always title
    if slide_idx == 0 and n_slides > 1:
        return "TITLE"
    # Thank-you high priority (last slides)
    if any(k in all_text for k in THANK_KWS):
        return "THANK_YOU"
    if "thank" in all_text:
        return "THANK_YOU"
    # Agenda
    if any(k in all_text for k in AGENDA_KWS):
        # limit to early slides but still score
        return "AGENDA"
    # Who We Are — needs both keyword and corporate density
    if "who we are" in all_text:
        return "WHO_WE_ARE"
    if "akkodis" in all_text and n_shapes > 12:
        return "WHO_WE_ARE"

    # --- Keyword scoring for remaining types ---
    scores: dict[str, int] = {
        "CASE_STUDY": 0,
        "SECTION_SPLITTER": 0,
        "GENERIC_CONTENT": 0,
        "WHO_WE_ARE": 0,
        "TITLE": 0,
    }

    # Case study signals
    scores["CASE_STUDY"] += _score_keywords(all_text, CASE_STUDY_KWS) * 3
    if "case stud" in all_text:
        scores["CASE_STUDY"] += 5
        if n_shapes < 8 and max_font >= 20:
            scores["SECTION_SPLITTER"] += 8
    if "challenge" in all_text or "solution" in all_text or "results" in all_text:
        scores["CASE_STUDY"] += 2
    # Akkodis service vocab in raw (e.g., VW | Akkodis) should push CASE_STUDY if paired with tech
    if "akkodis" in all_text and any(k in all_text for k in ["hil", "python", "automation", "test"]):
        scores["CASE_STUDY"] += 3

    # ADAS / Sensors / ECU / Diagnostics / Validation -> GENERIC_CONTENT
    scores["GENERIC_CONTENT"] += _score_keywords(all_text, ADAS_SENSORS_KWS) * 2
    scores["GENERIC_CONTENT"] += _score_keywords(all_text, ECU_DIAG_KWS) * 2
    scores["GENERIC_CONTENT"] += _score_keywords(all_text, VALIDATION_KWS) * 2
    # Akkodis generic vocab also maps to GENERIC unless WHO_WE_ARE already won
    scores["GENERIC_CONTENT"] += _score_keywords(all_text, AKKODIS_SVC_KWS) * 1

    # Section splitter structural cues
    if max_font >= 28 and n_shapes <= 6:
        scores["SECTION_SPLITTER"] += 4
    if n_shapes <= 3:
        scores["SECTION_SPLITTER"] += 2

    # Title cue
    if max_font >= 28:
        scores["TITLE"] += 3

    # Generic baseline
    if n_shapes > 8:
        scores["GENERIC_CONTENT"] += 1
    if not all_text.strip():
        scores["GENERIC_CONTENT"] += 1

    # Pick max; tie -> GENERIC_CONTENT (fallback to slide 3)
    best_type = max(scores, key=lambda k: scores[k])
    best_score = scores[best_type]

    # If no strong signal, default GENERIC_CONTENT (maps to slide 3)
    if best_score == 0:
        return "GENERIC_CONTENT"
    # If top two are close and GENERIC is contender, prefer GENERIC for technical slides
    # to avoid over-triggering CASE_STUDY on generic ADAS content
    if scores["GENERIC_CONTENT"] >= 4 and "adas" in all_text:
        # Technical content should stay generic even if case study words appear
        if scores["CASE_STUDY"] <= scores["GENERIC_CONTENT"] + 2:
            return "GENERIC_CONTENT"
    return best_type


class TemplateFiller:
    """Fills the brand template with content from a raw deck.

    The template provides ALL styling. We only replace text content
    and add new text layers where the raw deck has more content
    than the template has shapes. Backgrounds (001F33, bg_images at 0,1,9)
    are preserved via deepcopy.
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

        # Open the brand template as the base — will duplicate per raw slide
        prs = pptx.Presentation(self.template_path)
        orig_template_count = len(prs.slides)

        # Classify raw slides
        raw_prs = pptx.Presentation(raw_deck_path)
        raw_slides = []
        for si, slide in enumerate(raw_prs.slides):
            stype = _classify_raw_slide(slide, si, len(raw_prs.slides))
            texts = _get_text_content(slide)
            raw_slides.append({"index": si, "type": stype, "texts": texts})

        # Map template slide indices by type (first occurrence)
        type_to_tpl_idx: dict[str, int] = {}
        for tidx, ttype in self.template_slide_types.items():
            if ttype not in type_to_tpl_idx:
                type_to_tpl_idx[ttype] = tidx

        # Generic fallback must be slide 3 but not hard-coded 3 only — use mapping
        generic_idx = type_to_tpl_idx.get("GENERIC_CONTENT", 3)
        # Validate fallback is within 0-9
        if generic_idx < 0 or generic_idx >= orig_template_count:
            generic_idx = 3

        n_raw = len(raw_slides)

        # --- Core: keyword -> template slot -> fill (one duplicate per raw slide) ---
        for ri, rs in enumerate(raw_slides):
            rtype = rs["type"]
            # Every raw slide type must map to 0-9; fallback to GENERIC_CONTENT slide 3
            tpl_idx = type_to_tpl_idx.get(rtype, generic_idx)
            if tpl_idx is None or tpl_idx < 0 or tpl_idx >= orig_template_count:
                tpl_idx = generic_idx
            # Duplicate the matched template slide (preserves shapes/arrows/borders/transparency)
            new_slide = _duplicate_slide(prs, tpl_idx)
            self._fill_slide_text(new_slide, rs["texts"])

        # Remove original template slides (keep only duplicated content slides -> 29)
        _remove_first_n_slides(prs, orig_template_count)

        # Safety: ensure we have exactly n_raw slides
        assert len(prs.slides) == n_raw, f"Expected {n_raw} slides after duplication, got {len(prs.slides)}"

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
            "n_template_slides": orig_template_count,
            "n_output_slides": len(prs.slides),
            "binary_changed": binary_changed,
            "input_sha256": input_hash,
            "output_sha256": output_hash,
            "slide_type_map": [
                {"slide": rs["index"] + 1, "type": rs["type"]}
                for rs in raw_slides
            ],
            "mutations": [],
            "template_used": self.template_path,
            "mapping": {k: v for k, v in type_to_tpl_idx.items()},
            "generic_fallback_idx": generic_idx,
        }

    def _fill_slide_text(self, slide, raw_texts: list[dict]):
        """Replace text content in a slide's existing text frames with raw deck content.
        Robust for variable lengths:
        - if raw has more text shapes than template, duplicate via _add_text_box preserving font/color
        - if raw has fewer, clear extra template shapes (but never delete guidance shapes)
        """
        # Get all text-bearing shapes from the template slide, ordered by position
        text_shapes: list[dict] = []
        guidance_shapes: list = []
        for shape in slide.shapes:
            if not shape.has_text_frame:
                continue
            text = shape.text_frame.text.strip()
            if not text:
                continue
            # Never delete guidance shapes; skip them for filling and keep them visible
            low = text.lower()
            if "font guidance" in low or "do not change" in low or "do not move" in low:
                guidance_shapes.append(shape)
                continue
            try:
                top = shape.top / 914400.0
                left = shape.left / 914400.0
                width = shape.width / 914400.0
                height = shape.height / 914400.0
            except Exception:
                top, left, width, height = 0, 0, 2, 0.5
            max_size = 0.0
            font_name = None
            font_color = "FFFFFF"
            bold = False
            for p in shape.text_frame.paragraphs:
                for r in p.runs:
                    try:
                        if r.font.size:
                            max_size = max(max_size, float(r.font.size.pt))
                    except Exception:
                        pass
                    if r.font.name:
                        font_name = r.font.name
                    try:
                        if r.font.color and r.font.color.rgb:
                            font_color = str(r.font.color.rgb)
                    except Exception:
                        pass
                    if r.font.bold:
                        bold = True
            text_shapes.append({
                "shape": shape, "top": top, "left": left,
                "width": width, "height": height,
                "max_size": max_size,
                "font_name": font_name,
                "font_color": font_color,
                "bold": bold,
                "current_text": text,
            })

        text_shapes.sort(key=lambda x: (x["top"], -x["max_size"]))

        # Sort raw texts: titles first, then body (visual order)
        raw_sorted = sorted(raw_texts, key=lambda x: (not x.get("is_title", False), x["top"]))

        # Case 1: raw has fewer texts than template — fill what we can, clear extras
        # Case 2: raw has more — fill all template shapes, then add overflow boxes
        n_template_fillable = len(text_shapes)
        n_raw = len(raw_sorted)

        # Fill overlapping range
        for i in range(min(n_template_fillable, n_raw)):
            ts = text_shapes[i]
            raw = raw_sorted[i]
            # Preserve template style; only override font_size if raw had explicit size
            _set_text_preserving_style(
                ts["shape"], raw["text"],
                font_size=raw["max_size"] if raw["max_size"] and raw["max_size"] > 0 else None
            )

        # Clear extra template shapes when raw has fewer (keep shape/border, empty text)
        if n_raw < n_template_fillable:
            for i in range(n_raw, n_template_fillable):
                ts = text_shapes[i]
                # Clear but keep formatting (shape remains for border/bg)
                _set_text_preserving_style(ts["shape"], "")

        # Add overflow text boxes when raw has more shapes than template
        if n_raw > n_template_fillable:
            # Derive template style from last fillable shape or defaults (brand colors)
            if text_shapes:
                last = text_shapes[-1]
                base_left = last["left"]
                base_width = last["width"]
                # Start below last shape's bottom
                last_bottom = last["top"] + last["height"]
                gap = 0.15
                tmpl_font = last["font_name"] or DEFAULT_PROFILE.body_font
                tmpl_color = last["font_color"] or DEFAULT_PROFILE.white_hex
                tmpl_size = last["max_size"] if last["max_size"] and last["max_size"] > 0 else 10
                tmpl_bold = last["bold"]
            else:
                # Template had no fillable text (e.g., pure image slide) — use brand defaults
                base_left = 0.5
                base_width = 12.33
                last_bottom = 1.5
                gap = 0.2
                tmpl_font = DEFAULT_PROFILE.body_font
                tmpl_color = DEFAULT_PROFILE.white_hex
                tmpl_size = 10
                tmpl_bold = False

            for idx in range(n_template_fillable, n_raw):
                raw = raw_sorted[idx]
                # Cascade vertically; wrap if exceeding slide height (7.5in)
                overflow_index = idx - n_template_fillable
                top = last_bottom + gap + overflow_index * 0.6
                # If overflow would go off slide, clamp and reduce height
                if top > 6.8:
                    top = 6.8 - (overflow_index * 0.05)
                left = base_left
                width = base_width
                height = 0.5
                # Use raw's font size if available else template size
                font_size = raw["max_size"] if raw["max_size"] and raw["max_size"] > 0 else tmpl_size
                # Preserve template font/color (task: preserving template font/color)
                font_name = tmpl_font
                color = tmpl_color.replace("#", "")
                bold = tmpl_bold
                # Ensure text still appears if raw was title-like -> make bold/size larger
                if raw.get("is_title"):
                    bold = True
                    font_size = max(font_size, 14)
                _add_text_box(slide, raw["text"], left, top, width, height,
                              font_size=font_size, font_name=font_name,
                              color=color, bold=bold)
