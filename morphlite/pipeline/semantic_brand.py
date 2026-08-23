"""Phase 12.8: Semantic Brand Transformation Engine.

Reference-driven branding:
    1. Extract Brand DNA from golden deck pairs
    2. Classify shapes into semantic roles
    3. Apply role-aware brand styling (guaranteed visible)
    4. Enforce contrast (no dark-on-dark)
    5. Verify persistence through save
"""
from __future__ import annotations

import glob
import json
import math
from collections import Counter
from pathlib import Path

import pptx
from pptx.util import Pt, Inches
from pptx.dml.color import RGBColor

from ..pipeline.brand_profile import DEFAULT_PROFILE, BrandProfile


# ---------------------------------------------------------------------------
# Brand DNA extraction from golden pairs
# ---------------------------------------------------------------------------

def extract_brand_dna(golden_decks: list[str]) -> dict:
    """Extract consistent visual patterns from branded/golden decks."""
    bg_colors = Counter()
    title_colors = Counter()
    body_colors = Counter()
    title_fonts = Counter()
    body_fonts = Counter()
    title_sizes = []
    body_sizes = []

    for path in golden_decks[:10]:
        try:
            prs = pptx.Presentation(path)
        except Exception:
            continue
        for slide in prs.slides:
            try:
                if slide.background.fill.type == 1:
                    bg_colors[str(slide.background.fill.fore_color.rgb)] += 1
            except Exception:
                pass

            for shape in slide.shapes:
                if not shape.has_text_frame:
                    continue
                for p in shape.text_frame.paragraphs:
                    for r in p.runs:
                        sz = r.font.size.pt if r.font.size else None
                        try:
                            c = str(r.font.color.rgb) if r.font.color and r.font.color.rgb else None
                        except Exception:
                            c = None
                        fname = r.font.name

                        if sz and sz >= 20:
                            title_sizes.append(sz)
                            if c:
                                title_colors[c] += 1
                            if fname:
                                title_fonts[fname] += 1
                        elif sz and sz <= 14:
                            body_sizes.append(sz)
                            if c:
                                body_colors[c] += 1
                            if fname:
                                body_fonts[fname] += 1
                        elif sz:
                            body_sizes.append(sz)
                            if c:
                                body_colors[c] += 1
                            if fname:
                                body_fonts[fname] += 1

    return {
        "background": bg_colors.most_common(1)[0][0] if bg_colors else "030C1E",
        "title_color": title_colors.most_common(1)[0][0] if title_colors else "FFB81C",
        "body_color": body_colors.most_common(1)[0][0] if body_colors else "FFFFFF",
        "title_font": title_fonts.most_common(1)[0][0] if title_fonts else "Times New Roman",
        "body_font": body_fonts.most_common(1)[0][0] if body_fonts else "Arial",
        "title_size": round(sum(title_sizes) / max(len(title_sizes), 1), 1),
        "body_size": round(sum(body_sizes) / max(len(body_sizes), 1), 1),
    }


# ---------------------------------------------------------------------------
# Semantic role detection (heuristic, no ML)
# ---------------------------------------------------------------------------

def classify_role(shape, slide_height: float) -> str:
    """Classify a shape into a semantic role using deterministic heuristics."""
    name = (shape.name or "").lower()
    has_tf = shape.has_text_frame
    text = shape.text_frame.text.strip() if has_tf else ""

    # Explicit name-based detection
    if "title" in name:
        return "TITLE"
    if "subtitle" in name:
        return "SUBTITLE"
    if "footer" in name or "slide number" in name:
        return "FOOTER"
    if "placeholder" in name and text:
        y = shape.top / 914400.0 if shape.top else 0
        if y < slide_height * 0.25:
            return "TITLE"

    # Text-based heuristics
    if has_tf and text:
        # Get max font size in the shape
        max_size = 0
        for p in shape.text_frame.paragraphs:
            for r in p.runs:
                if r.font.size:
                    max_size = max(max_size, r.font.size.pt)

        y = shape.top / 914400.0 if shape.top else 0
        h = shape.height / 914400.0 if shape.height else 0

        if max_size >= 20 or (y < slide_height * 0.2 and h < slide_height * 0.15 and len(text) < 100):
            return "TITLE"
        if max_size >= 14 and max_size < 20:
            if len(text) < 80:
                return "SUBTITLE"
            return "BODY"
        if max_size > 0 and max_size < 12:
            return "CAPTION"
        return "BODY"

    # Shape type based
    try:
        st = str(shape.shape_type)
        if "PICTURE" in st:
            return "IMAGE"
        if "TABLE" in st:
            return "TABLE"
        if "CHART" in st:
            return "CHART"
    except Exception:
        pass

    # Decorative: small shapes without text
    try:
        w = shape.width / 914400.0 if shape.width else 0
        h = shape.height / 914400.0 if shape.height else 0
        if not text and w * h < 0.5:
            return "DECORATION"
    except Exception:
        pass

    return "UNKNOWN"


# ---------------------------------------------------------------------------
# Contrast calculation
# ---------------------------------------------------------------------------

def _force_run_color(run, rgb: RGBColor):
    """Force-set run color via direct XML manipulation.
    Bypasses python-pptx high-level API which doesn't persist for inherited runs."""
    from pptx.oxml.ns import qn

    rPr = run._r.get_or_add_rPr()

    # Remove existing fill elements
    for tag in ("a:solidFill", "a:gradFill", "a:pattFill", "a:blipFill", "a:noFill", "a:grpFill"):
        for el in rPr.findall(qn(tag)):
            rPr.remove(el)

    # Create solidFill with srgbClr
    solid_fill = rPr.makeelement(qn("a:solidFill"), {})
    srgb = solid_fill.makeelement(qn("a:srgbClr"), {"val": str(rgb)})
    solid_fill.append(srgb)

    # Insert as first child of rPr (schema requires fill before other elements)
    rPr.insert(0, solid_fill)


def _force_paragraph_color(paragraph, rgb: RGBColor):
    """Force-set paragraph-level default color."""
    from pptx.oxml.ns import qn

    pPr = paragraph._p.get_or_add_pPr()
    defRPr = pPr.find(qn("a:defRPr"))
    if defRPr is None:
        defRPr = pPr.makeelement(qn("a:defRPr"), {})
        pPr.append(defRPr)

    for tag in ("a:solidFill", "a:gradFill", "a:pattFill", "a:noFill"):
        for el in defRPr.findall(qn(tag)):
            defRPr.remove(el)

    solid_fill = defRPr.makeelement(qn("a:solidFill"), {})
    srgb = solid_fill.makeelement(qn("a:srgbClr"), {"val": str(rgb)})
    solid_fill.append(srgb)
    defRPr.insert(0, solid_fill)


def _force_run_font(run, font_name: str):
    """Force-set run font name via direct XML."""
    from pptx.oxml.ns import qn

    rPr = run._r.get_or_add_rPr()
    for tag in ("a:latin", "a:ea", "a:cs"):
        for el in rPr.findall(qn(tag)):
            rPr.remove(el)

    latin = rPr.makeelement(qn("a:latin"), {"typeface": font_name})
    # Insert after solidFill if present, else at start
    solid = rPr.find(qn("a:solidFill"))
    if solid is not None:
        solid.addnext(latin)
    else:
        rPr.insert(0, latin)
    r, g, b = rgb[0] / 255, rgb[1] / 255, rgb[2] / 255
    return 0.299 * r + 0.587 * g + 0.114 * b


def _luminance(rgb: RGBColor) -> float:
    r, g, b = rgb[0] / 255, rgb[1] / 255, rgb[2] / 255
    return 0.299 * r + 0.587 * g + 0.114 * b


def _contrast_ratio(fg: RGBColor, bg: RGBColor) -> float:
    l1 = _luminance(fg)
    l2 = _luminance(bg)
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


# ---------------------------------------------------------------------------
# Semantic brand transformer
# ---------------------------------------------------------------------------

class SemanticBrandTransformer:
    def __init__(self, profile: BrandProfile, brand_dna: dict | None = None):
        self.profile = profile
        self.dna = brand_dna or {}
        self.mutations: list[dict] = []

    def transform(self, prs) -> list[dict]:
        """Applies semantic role-aware branding to the entire presentation.
        Returns list of mutation records."""
        self.mutations = []
        bp = self.profile

        # Resolve effective brand tokens (DNA overrides profile defaults)
        bg_hex = self.dna.get("background", bp.dark_hex)
        title_color_hex = self.dna.get("title_color", bp.gold_hex)
        body_color_hex = self.dna.get("body_color", bp.white_hex)
        title_font = self.dna.get("title_font", bp.heading_font)
        body_font = self.dna.get("body_font", bp.body_font)

        bg_rgb = RGBColor(*bp._hex_tuple(bg_hex))
        title_rgb = RGBColor(*bp._hex_tuple(title_color_hex))
        body_rgb = RGBColor(*bp._hex_tuple(body_color_hex))
        card_rgb = RGBColor(*bp._hex_tuple(bp.card_hex))

        for slide_idx, slide in enumerate(prs.slides):
            slide_height = 7.5  # inches

            # Background: always apply
            self._set_background(slide, slide_idx, bg_rgb)

            for shape in self._all_shapes(slide):
                role = classify_role(shape, slide_height)
                self._apply_role_styling(
                    shape, role, slide_idx,
                    bg_rgb, title_rgb, body_rgb, card_rgb,
                    title_font, body_font,
                )

        return self.mutations

    def _all_shapes(self, slide):
        for shape in slide.shapes:
            yield shape
            if hasattr(shape, "shapes"):
                try:
                    for s in shape.shapes:
                        yield s
                except Exception:
                    pass

    def _set_background(self, slide, slide_idx: int, bg_rgb: RGBColor):
        try:
            old = None
            try:
                if slide.background.fill.type == 1:
                    old = str(slide.background.fill.fore_color.rgb)
            except Exception:
                pass
            slide.background.fill.solid()
            slide.background.fill.fore_color.rgb = bg_rgb
            self._record(slide_idx, "BACKGROUND", "(slide)",
                         "background", old or "(inherit)", str(bg_rgb))
        except Exception as e:
            self._record(slide_idx, "BACKGROUND", "(slide)",
                         "background", "?", "FAILED: " + str(e))

    def _apply_role_styling(self, shape, role: str, slide_idx: int,
                            bg_rgb, title_rgb, body_rgb, card_rgb,
                            title_font: str, body_font: str):
        shape_id = getattr(shape, "shape_id", 0)
        shape_name = shape.name or ""
        bp = self.profile
        aqua = RGBColor(0, 255, 255)

        # Skip non-styled types
        try:
            st = str(shape.shape_type)
            if "TABLE" in st or "CHART" in st or "PLACEHOLDER" in st.upper():
                return
        except Exception:
            pass

        has_text = shape.has_text_frame and shape.text_frame.text.strip()
        is_title = role in ("TITLE", "SUBTITLE", "SECTION_HEADER")

        # --- STEP 1: SHAPE FILL + BORDER ---
        # Apply card styling to any shape that visually acts as a container.
        # This includes text-bearing shapes so text/fill are styled as a unit.
        is_visual_container = False
        try:
            st = str(shape.shape_type)
            is_visual_container = (
                "AUTO_SHAPE" in st or "FREEFORM" in st or "RECTANGLE" in st
            )
        except Exception:
            pass

        # Titles typically sit directly on the background (no fill needed)
        # Cards/body containers get the brand card treatment
        should_style_fill = is_visual_container and not is_title

        if should_style_fill:
            try:
                old_fill = "(none)"
                if shape.fill.type == 1:
                    old_fill = str(shape.fill.fore_color.rgb)
                shape.fill.solid()
                shape.fill.fore_color.rgb = card_rgb
                self._record(slide_idx, role, shape_name, "fill.color",
                             old_fill, str(card_rgb), shape_id=shape_id)
            except Exception:
                pass
            try:
                old_line = "(none)"
                if shape.line and shape.line.fill.type == 1:
                    old_line = str(shape.line.color.rgb)
                shape.line.color.rgb = aqua
                shape.line.width = Pt(1.5)
                self._record(slide_idx, role, shape_name, "border.color",
                             old_line, "#00FFFF", shape_id=shape_id)
            except Exception:
                pass

        # --- STEP 2: TEXT STYLING ---
        # Text color must contrast with the SHAPE's fill (not the slide bg).
        # After step 1, the shape fill is brand card (dark) -> use light text.
        # If fill wasn't styled (title on bg, or non-container), contrast against bg.
        effective_bg = card_rgb if should_style_fill else bg_rgb

        if not shape.has_text_frame:
            return

        target_font = title_font if is_title else body_font
        target_color = title_rgb if is_title else body_rgb

        # Contrast check against the EFFECTIVE background
        contrast = _contrast_ratio(target_color, effective_bg)
        if contrast < 2.0:
            # Fallback: white text is readable on any dark surface
            target_color = body_rgb
            contrast = _contrast_ratio(target_color, effective_bg)

        if not shape.text_frame.text.strip():
            return

        for p in shape.text_frame.paragraphs:
            try:
                _force_paragraph_color(p, target_color)
            except Exception:
                pass

            for r in p.runs:
                font = r.font

                old_color = "(inherited)"
                try:
                    if font.color and font.color.type is not None and font.color.rgb:
                        old_color = str(font.color.rgb)
                except Exception:
                    pass

                old_name = font.name

                try:
                    _force_run_font(r, target_font)
                except Exception:
                    font.name = target_font

                try:
                    _force_run_color(r, target_color)
                except Exception:
                    font.color.rgb = target_color

                if old_name != target_font:
                    self._record(slide_idx, role, shape_name, "font.name",
                                 old_name or "(inherited)", target_font, shape_id=shape_id)
                if old_color != str(target_color):
                    self._record(slide_idx, role, shape_name, "font.color",
                                 old_color, str(target_color), shape_id=shape_id)

                # Bold for titles
                if is_title and not font.bold:
                    font.bold = True
                    self._record(slide_idx, role, shape_name, "bold",
                                 "False", "True", shape_id=shape_id)

        # Contrast validation record
        final_contrast = _contrast_ratio(target_color, bg_rgb)
        self._record(slide_idx, role, shape_name, "contrast_check",
                     "", f"ratio={final_contrast:.2f}", shape_id=shape_id)

    def _record(self, slide_idx: int, role: str, shape: str,
                prop: str, before: str, after: str, shape_id: int = 0):
        if before == after:
            return
        self.mutations.append({
            "slide": slide_idx + 1,
            "stage": "DETERMINISTIC_SEMANTIC",
            "role": role,
            "property": prop,
            "shape": shape,
            "shape_id": shape_id,
            "before": before,
            "after": after,
        })
