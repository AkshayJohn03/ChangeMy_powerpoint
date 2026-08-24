"""BrandMorph v0.3: Template-styled pipeline.

Opens the RAW deck (preserving all shapes/content), then applies brand
styling extracted from the template: backgrounds (solid + image), fonts,
colors, and card treatments. No shapes are removed. No content is lost.

    pipeline = TemplateStyledPipeline(template_path, raw_deck_path)
    result = pipeline.process(output_path)
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
    r, g, b = rgb[0] / 255, rgb[1] / 255, rgb[2] / 255
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
            "bg_images": {},     # slide_idx -> image bytes
            "bg_colors": {},     # layout_name -> hex color
            "layout_bg_images": {},  # layout_name -> image bytes
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
                except (ValueError, AttributeError):
                    continue
                except Exception:
                    continue

        # Extract font/color patterns from template text
        title_fonts, body_fonts = Counter(), Counter()
        title_colors, body_colors = Counter(), Counter()
        for slide in tpl_prs.slides:
            for shape in slide.shapes:
                if not shape.has_text_frame:
                    continue
                for p in shape.text_frame.paragraphs:
                    for r in p.runs:
                        if not r.font.size:
                            continue
                        sz = r.font.size.pt
                        try:
                            c = str(r.font.color.rgb) if r.font.color and r.font.color.rgb else None
                        except Exception:
                            c = None
                        fn = r.font.name
                        if sz >= 24:
                            if fn:
                                title_fonts[fn] += 1
                            if c:
                                title_colors[c] += 1
                        elif sz:
                            if fn:
                                body_fonts[fn] += 1
                            if c:
                                body_colors[c] += 1

        assets["title_font"] = title_fonts.most_common(1)[0][0] if title_fonts else "Times New Roman"
        assets["body_font"] = body_fonts.most_common(1)[0][0] if body_fonts else "Arial"
        assets["title_color"] = title_colors.most_common(1)[0][0] if title_colors else "FFB81C"
        assets["body_color"] = body_colors.most_common(1)[0][0] if body_colors else "FFFFFF"

        return assets

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
            # Check if template has a background image for this slide type
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
        """Find the template background image for this slide type."""
        assets = self._template_assets
        # Check slide-specific images first
        if slide_idx in assets["bg_images"]:
            return assets["bg_images"][slide_idx]
        # Check by type
        type_map = {"TITLE": 0, "AGENDA": 1, "THANK_YOU": 8, "CLOSING": 9}
        if slide_type in type_map:
            tpl_idx = type_map[slide_type]
            if tpl_idx in assets["bg_images"]:
                return assets["bg_images"][tpl_idx]
        return None

    def _apply_image_background(self, prs, slide, img_data: bytes, mutations: list):
        """Add a full-slide background image behind all content."""
        try:
            img_stream = io.BytesIO(img_data)
            pic = slide.shapes.add_picture(
                img_stream, Inches(0), Inches(0),
                Inches(13.333), Inches(7.5)
            )
            # Move to back of z-order
            sp = pic._element
            spTree = sp.getparent()
            spTree.remove(sp)
            spTree.insert(2, sp)  # after nvGrpSpPr and grpSpPr
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
        """Apply solid brand background color."""
        bp = self.profile
        try:
            old = None
            try:
                if slide.background.fill.type == 1:
                    old = str(slide.background.fill.fore_color.rgb)
            except Exception:
                pass
            bg_color = RGBColor(*bp._hex_tuple(bp.dark_hex))
            slide.background.fill.solid()
            slide.background.fill.fore_color.rgb = bg_color
            mutations.append({
                "stage": "BRAND_BG", "property": "background_color",
                "before": old or "(inherit)", "after": str(bg_color),
            })
        except Exception:
            pass

    def _apply_brand_typography(self, slide, slide_idx: int, mutations: list):
        """Normalize fonts and colors on all text runs."""
        bp = self.profile
        assets = self._template_assets
        title_font = assets.get("title_font", bp.heading_font)
        body_font = assets.get("body_font", bp.body_font)
        title_color = assets.get("title_color", bp.gold_hex)
        body_color = assets.get("body_color", bp.white_hex)

        title_rgb = RGBColor(*bp._hex_tuple(title_color))
        body_rgb = RGBColor(*bp._hex_tuple(body_color))
        bg_rgb = RGBColor(*bp._hex_tuple(bp.dark_hex))

        for shape in self._all_shapes(slide):
            if not shape.has_text_frame:
                continue
            is_title = self._is_title_like(shape)

            target_font = title_font if is_title else body_font
            target_color = title_rgb if is_title else body_rgb

            # Contrast check
            contrast = _contrast_ratio(target_color, bg_rgb)
            if contrast < 2.0:
                target_color = body_rgb

            for p in shape.text_frame.paragraphs:
                try:
                    _force_paragraph_color(p, target_color)
                except Exception:
                    pass

                for r in p.runs:
                    old_font = r.font.name
                    old_color = "(inherited)"
                    try:
                        if r.font.color and r.font.color.type is not None and r.font.color.rgb:
                            old_color = str(r.font.color.rgb)
                    except Exception:
                        pass

                    try:
                        _force_run_font(r, target_font)
                    except Exception:
                        r.font.name = target_font

                    try:
                        _force_run_color(r, target_color)
                    except Exception:
                        r.font.color.rgb = target_color

                    if old_font != target_font:
                        mutations.append({
                            "stage": "TYPOGRAPHY", "property": "font.name",
                            "shape": shape.name, "before": old_font or "(inherited)",
                            "after": target_font,
                        })
                    if old_color != str(target_color):
                        mutations.append({
                            "stage": "TYPOGRAPHY", "property": "font.color",
                            "shape": shape.name, "before": old_color,
                            "after": str(target_color),
                        })

    def _apply_brand_fills(self, slide, slide_idx: int, mutations: list):
        """Normalize card/shape fills to brand colors."""
        bp = self.profile
        card_rgb = RGBColor(*bp._hex_tuple(bp.card_hex))

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
                    lum = _luminance(RGBColor(*bp._hex_tuple(old.lstrip("#")))) if old.startswith("#") or len(old) == 6 else 0.5
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


