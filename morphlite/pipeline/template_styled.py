"""BrandMorph v0.3: Template-styled pipeline.

Opens the RAW deck (preserving all shapes/content), then applies brand
styling extracted from the template: backgrounds (solid + image), fonts,
colors, and card treatments. No shapes are removed. No content is lost.
"""
from __future__ import annotations

import hashlib
import io
import math
import uuid
from collections import Counter
from pathlib import Path

import numpy as np
import pptx
from pptx.util import Pt, Inches
from pptx.dml.color import RGBColor
from pptx.oxml.ns import qn

from ..pipeline.brand_profile import DEFAULT_PROFILE, BrandProfile


def _luminance(rgb: RGBColor) -> float:
    r, g, b = rgb[0] / 255.0, rgb[1] / 255.0, rgb[2] / 255.0
    return 0.299 * r + 0.587 * g + 0.114 * b


def _contrast_ratio(fg: RGBColor, bg: RGBColor) -> float:
    l1 = _luminance(fg)
    l2 = _luminance(bg)
    return (max(l1, l2) + 0.05) / (min(l1, l2) + 0.05)


def _force_run_color(run, rgb: RGBColor):
    rPr = run._r.get_or_add_rPr()
    for tag in ("a:solidFill", "a:gradFill", "a:pattFill", "a:blipFill", "a:noFill", "a:grpFill"):
        for el in rPr.findall(qn(tag)):
            rPr.remove(el)
    solid_fill = rPr.makeelement(qn("a:solidFill"), {})
    srgb = solid_fill.makeelement(qn("a:srgbClr"), {"val": str(rgb)})
    solid_fill.append(srgb)
    rPr.insert(0, solid_fill)


def _force_run_font(run, font_name: str):
    rPr = run._r.get_or_add_rPr()
    for tag in ("a:latin", "a:ea", "a:cs"):
        for el in rPr.findall(qn(tag)):
            rPr.remove(el)
    latin = rPr.makeelement(qn("a:latin"), {"typeface": font_name})
    solid = rPr.find(qn("a:solidFill"))
    if solid is not None:
        solid.addnext(latin)
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
    solid_fill = defRPr.makeelement(qn("a:solidFill"), {})
    srgb = solid_fill.makeelement(qn("a:srgbClr"), {"val": str(rgb)})
    solid_fill.append(srgb)
    defRPr.insert(0, solid_fill)


def _classify_slide(slide, slide_idx: int, n_slides: int) -> str:
    """Heuristic slide type classification."""
    texts = []
    max_font = 0.0
    n_shapes = len(slide.shapes)

    for shape in slide.shapes:
        try:
            if "PICTURE" in str(shape.shape_type):
                w = shape.width / 914400.0 if shape.width else 0
                h = shape.height / 914400.0 if shape.height else 0
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
    if "who we are" in all_text:
        return "WHO_WE_ARE"
    if "case stud" in all_text and n_shapes < 8:
        return "SECTION_SPLITTER"
    if "case stud" in all_text or "results" in all_text:
        return "CASE_STUDY"
    if max_font >= 28:
        return "TITLE"
    if n_shapes <= 5:
        return "GENERIC_MINIMAL"
    return "GENERIC_CONTENT"


class TemplateStyledPipeline:
    """Opens the raw deck, applies brand styling from the template.
    Preserves ALL shapes and content. No slides added or removed."""

    def __init__(self, template_path: str, profile: BrandProfile | None = None):
        self.template_path = template_path
        self.profile = profile or DEFAULT_PROFILE
        self._template_assets = self._extract_template_assets()

    def _extract_template_assets(self) -> dict:
        """Extract background images, colors, and fonts from the brand template."""
        tpl_prs = pptx.Presentation(self.template_path)
        assets = {
            "bg_images": {},
            "bg_colors": {},
            "layout_bg_images": {},
        }

        # Extract layout backgrounds
        for master in tpl_prs.slide_masters:
            for layout in master.slide_layouts:
                try:
                    bg = layout.background.fill
                    if bg.type == 1:
                        assets["bg_colors"][layout.name] = str(bg.fore_color.rgb)
                    elif bg.type == 6:
                        try:
                            img = bg.fore_color._fill.image
                            assets["layout_bg_images"][layout.name] = img.blob
                        except Exception:
                            pass
                except Exception:
                    pass

        # Extract full-slide image backgrounds from template slides
        for si, slide in enumerate(tpl_prs.slides):
            for shape in slide.shapes:
                try:
                    w = shape.width / 914400.0 if shape.width else 0
                    h = shape.height / 914400.0 if shape.height else 0
                    if w > 12 and h > 6 and hasattr(shape, "image"):
                        img = shape.image
                        assets["bg_images"][si] = img.blob
                except Exception:
                    continue

        assets["title_font"] = "Times New Roman"
        assets["body_font"] = "Arial"
        assets["title_color"] = "FFB81C"
        assets["body_color"] = "FFFFFF"

        return assets

    def _add_logo_stamp(self, slide):
        """Top-Right Akkodis Corporate Logo Stamp (Issue #4)."""
        try:
            for s in slide.shapes:
                if s.has_text_frame and "AKKODIS" in s.text_frame.text:
                    return
            txBox = slide.shapes.add_textbox(Inches(11.4), Inches(0.35), Inches(1.5), Inches(0.45))
            tf = txBox.text_frame
            tf.word_wrap = False
            p = tf.paragraphs[0]
            p.alignment = pptx.enum.text.PP_ALIGN.RIGHT
            run = p.add_run()
            run.text = "AKKODIS"
            run.font.name = "Arial"
            run.font.size = Pt(13)
            run.font.bold = True
            gold_rgb = RGBColor(255, 184, 28)
            run.font.color.rgb = gold_rgb
            _force_run_color(run, gold_rgb)
        except Exception:
            pass

    def process(self, raw_deck_path: str, output_path: str | None = None) -> dict:
        deck_id = str(uuid.uuid4())[:8]
        input_hash = hashlib.sha256(Path(raw_deck_path).read_bytes()).hexdigest()

        prs = pptx.Presentation(raw_deck_path)
        n_slides = len(prs.slides)
        all_mutations = []
        slide_info_list = []

        for si, slide in enumerate(prs.slides):
            slide_mutations = []
            slide_type = _classify_slide(slide, si, n_slides)

            # --- 1. BACKGROUND ---
            bg_image_data = self._get_bg_image_for_type(slide_type, si)
            if bg_image_data:
                self._apply_image_background(prs, slide, bg_image_data, slide_mutations)
            else:
                self._apply_solid_background(slide, slide_mutations)

            # --- 2. FONT + COLOR NORMALIZATION ---
            self._apply_brand_typography(slide, si, slide_mutations)

            # --- 3. SHAPE FILL NORMALIZATION ---
            self._apply_brand_fills(slide, si, slide_mutations)

            slide_info_list.append({
                "slide": si + 1,
                "type": slide_type,
                "mutations": len(slide_mutations),
            })
            all_mutations.extend(slide_mutations)

        # --- INTEGRITY ---
        integrity = {
            "input_sha256": input_hash,
            "deterministic_mutations": len(all_mutations),
        }

        if output_path:
            prs.save(output_path)
            output_hash = hashlib.sha256(Path(output_path).read_bytes()).hexdigest()
            integrity["output_sha256"] = output_hash
            integrity["binary_changed"] = input_hash != output_hash
            integrity["content_changed"] = integrity["binary_changed"]

        return {
            "deck_id": deck_id,
            "input_path": raw_deck_path,
            "output_path": output_path,
            "n_slides": n_slides,
            "integrity": integrity,
            "slide_types": {},
            "mutations_summary": self._summarize(all_mutations),
            "slide_info": slide_info_list,
        }

    def _get_bg_image_for_type(self, slide_type: str, slide_idx: int) -> bytes | None:
        assets = self._template_assets
        if slide_idx in assets["bg_images"]:
            return assets["bg_images"][slide_idx]
        type_map = {"TITLE": 0, "AGENDA": 1, "THANK_YOU": 8, "CLOSING": 9}
        if slide_type in type_map:
            tpl_idx = type_map[slide_type]
            if tpl_idx in assets["bg_images"]:
                return assets["bg_images"][tpl_idx]
        return None

    def _apply_image_background(self, prs, slide, img_data: bytes, mutations: list):
        try:
            img_stream = io.BytesIO(img_data)
            pic = slide.shapes.add_picture(
                img_stream, Inches(0), Inches(0),
                Inches(13.333), Inches(7.5)
            )
            sp = pic._element
            spTree = sp.getparent()
            spTree.remove(sp)
            spTree.insert(2, sp)
            mutations.append({
                "stage": "TEMPLATE_BG", "property": "background_image",
                "before": "(none)", "after": f"image ({len(img_data)//1024}KB)",
            })
        except Exception as e:
            mutations.append({
                "stage": "TEMPLATE_BG", "property": "background_image",
                "before": "?", "after": f"FAILED: {e}",
            })

    def _apply_solid_background(self, slide, mutations: list):
        bp = self.profile
        try:
            old = None
            try:
                if slide.background.fill.type == 1:
                    old = str(slide.background.fill.fore_color.rgb)
            except Exception:
                pass
            bg_color = RGBColor(0, 31, 51)  # #001F33
            slide.background.fill.solid()
            slide.background.fill.fore_color.rgb = bg_color
            mutations.append({
                "stage": "BRAND_BG", "property": "background_color",
                "before": old or "(inherit)", "after": str(bg_color),
            })
        except Exception:
            pass

    def _apply_brand_typography(self, slide, slide_idx: int, mutations: list):
        """Normalize fonts and colors on all text runs with background-aware contrast resolution."""
        title_font = "Times New Roman"
        body_font = "Arial"
        title_rgb = RGBColor(255, 184, 28)    # #FFB81C Gold
        body_rgb = RGBColor(255, 255, 255)    # #FFFFFF White
        dark_text_rgb = RGBColor(0, 31, 51)   # #001F33 Dark Navy for bright backgrounds

        # Ensure top-right logo stamp is present
        self._add_logo_stamp(slide)

        for shape in self._all_shapes(slide):
            if not shape.has_text_frame:
                continue

            shape_fill_lum = 0.0
            try:
                if shape.fill and shape.fill.type == 1 and shape.fill.fore_color and shape.fill.fore_color.type == 1:
                    shape_fill_lum = _luminance(shape.fill.fore_color.rgb)
            except Exception:
                pass

            is_title = self._is_title_like(shape)

            for p_idx, p in enumerate(shape.text_frame.paragraphs):
                p_text = p.text.strip()
                if not p_text:
                    continue

                for r in p.runs:
                    raw_size = r.font.size.pt if r.font and r.font.size else 12.0
                    is_run_title = is_title and (p_idx == 0 or raw_size >= 20.0)
                    is_subheading = not is_run_title and (bool(r.font.bold) or (14.0 <= raw_size < 20.0))

                    # Resolve contrast
                    if shape_fill_lum >= 0.55:
                        target_color = dark_text_rgb
                    elif is_run_title:
                        target_color = title_rgb
                    elif is_subheading:
                        target_color = body_rgb
                    else:
                        target_color = body_rgb

                    # Apply typography rules
                    if is_run_title:
                        target_font = title_font
                        clamped_size = 30.0 if raw_size > 32.0 else (24.0 if raw_size < 24.0 else raw_size)
                        target_bold = False
                        target_italic = False
                    elif is_subheading:
                        target_font = body_font
                        clamped_size = max(11.0, min(16.0, raw_size))
                        target_bold = True
                        target_italic = False
                    else:
                        target_font = body_font
                        clamped_size = max(8.0, raw_size)
                        target_bold = False
                        target_italic = False

                    r.font.name = target_font
                    r.font.size = Pt(clamped_size)
                    r.font.bold = target_bold
                    r.font.italic = target_italic
                    r.font.color.rgb = target_color

                    try:
                        _force_run_font(r, target_font)
                        _force_run_color(r, target_color)
                    except Exception:
                        pass

    def _apply_brand_fills(self, slide, slide_idx: int, mutations: list):
        """Normalize card/shape fills to brand colors."""
        card_rgb = RGBColor(8, 30, 54)  # #081E36

        for shape in self._all_shapes(slide):
            try:
                st = str(shape.shape_type)
                if "AUTO_SHAPE" not in st and "FREEFORM" not in st:
                    continue
                if not shape.has_text_frame:
                    continue
                text = shape.text_frame.text.strip()
                if not text:
                    continue
                if shape.fill.type == 1:
                    old = str(shape.fill.fore_color.rgb)
                    lum = _luminance(shape.fill.fore_color.rgb)
                    if lum > 0.6:
                        shape.fill.fore_color.rgb = card_rgb
                        mutations.append({
                            "stage": "BRAND_FILL", "property": "fill.color",
                            "shape": shape.name, "before": old, "after": str(card_rgb),
                        })
            except Exception:
                pass

    def _all_shapes(self, slide):
        for shape in slide.shapes:
            yield shape
            if hasattr(shape, "shapes"):
                try:
                    for s in shape.shapes:
                        yield s
                except Exception:
                    pass

    def _is_title_like(self, shape) -> bool:
        try:
            if "title" in (shape.name or "").lower():
                return True
            if shape.has_text_frame:
                for p in shape.text_frame.paragraphs:
                    for r in p.runs:
                        if r.font.size and r.font.size.pt >= 20:
                            return True
        except Exception:
            pass
        return False

    def _classify_slide_type(self, slide, idx, total):
        return _classify_slide(slide, idx, total)

    @staticmethod
    def _summarize(mutations: list[dict]) -> dict:
        by_stage = Counter(m.get("stage", "?") for m in mutations)
        by_prop = Counter(m.get("property", "?") for m in mutations)
        return {
            "total": len(mutations),
            "by_stage": dict(by_stage),
            "by_property": dict(by_prop.most_common(10)),
        }
