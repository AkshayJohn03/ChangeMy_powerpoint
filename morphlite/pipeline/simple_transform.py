"""BrandMorph v0.3 — Simple, direct brand transformation.

Opens the RAW deck. Applies brand styling. Saves. No template filling.
No presentation merging. Just direct, visible, reliable changes.

    pipeline = SimpleBrandTransform(template_path)
    result = pipeline.process("input.pptx", "output.pptx")
"""
from __future__ import annotations

import hashlib
import os
import sys
import uuid
from collections import Counter
from pathlib import Path

import pptx
from pptx.util import Pt, Inches
from pptx.dml.color import RGBColor
from pptx.oxml.ns import qn

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from .brand_profile import DEFAULT_PROFILE, BrandProfile


def _luminance(rgb):
    r, g, b = rgb[0] / 255, rgb[1] / 255, rgb[2] / 255
    return 0.299 * r + 0.587 * g + 0.114 * b


def _contrast_ratio(fg, bg):
    l1, l2 = _luminance(fg), _luminance(bg)
    return (max(l1, l2) + 0.05) / (min(l1, l2) + 0.05)


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


class SimpleBrandTransform:
    def __init__(self, template_path: str, profile: BrandProfile | None = None):
        self.profile = profile or DEFAULT_PROFILE
        self.template_assets = self._extract_template_assets(template_path)

    def _extract_template_assets(self, template_path: str) -> dict:
        """Extract brand colors and fonts from the template."""
        try:
            tpl = pptx.Presentation(template_path)
        except Exception:
            return self._default_assets()

        title_fonts, body_fonts = {}, {}
        title_colors, body_colors = {}, {}
        bg_colors = {}

        for slide in tpl.slides:
            try:
                bg = slide.background.fill
                if bg.type == 1:
                    bg_colors[str(bg.fore_color.rgb)] = bg_colors.get(str(bg.fore_color.rgb), 0) + 1
            except Exception:
                pass

            for shape in _all_shapes(slide):
                if not shape.has_text_frame:
                    continue
                for p in shape.text_frame.paragraphs:
                    for r in p.runs:
                        if not r.font.size:
                            continue
                        sz = r.font.size.pt
                        fn = r.font.name
                        try:
                            c = str(r.font.color.rgb) if r.font.color and r.font.color.rgb else None
                        except Exception:
                            c = None

                        if sz >= 20:
                            if fn:
                                title_fonts[fn] = title_fonts.get(fn, 0) + 1
                            if c:
                                title_colors[c] = title_colors.get(c, 0) + 1
                        elif sz >= 8:
                            if fn:
                                body_fonts[fn] = body_fonts.get(fn, 0) + 1
                            if c:
                                body_colors[c] = body_colors.get(c, 0) + 1

        return {
            "title_font": max(title_fonts, key=title_fonts.get) if title_fonts else "Times New Roman",
            "body_font": max(body_fonts, key=body_fonts.get) if body_fonts else "Arial",
            "title_color": "FFB81C",  # Gold Text 2 per brand guidelines
            "body_color": "FFFFFF",
            "background": max(bg_colors, key=bg_colors.get) if bg_colors else "030C1E",
        }

    def _default_assets(self):
        return {
            "title_font": "Times New Roman",
            "body_font": "Arial",
            "title_color": "FFB81C",
            "body_color": "FFFFFF",
            "background": "030C1E",
        }

    def process(self, raw_deck_path: str, output_path: str | None = None) -> dict:
        input_hash = hashlib.sha256(Path(raw_deck_path).read_bytes()).hexdigest()
        prs = pptx.Presentation(raw_deck_path)

        assets = self.template_assets
        bg_rgb = RGBColor.from_string(assets["background"])
        title_rgb = RGBColor.from_string(assets["title_color"])
        body_rgb = RGBColor.from_string(assets["body_color"])
        title_font = assets["title_font"]
        body_font = assets["body_font"]
        card_rgb = RGBColor.from_string("081632")
        aqua_rgb = RGBColor(0, 255, 255)
        gold_rgb = title_rgb

        # Load Akkodis logo if available
        logo_path = None
        logo_path = None
        try:
            repo_root = Path(__file__).resolve().parent.parent.parent
            logo_dir = str(repo_root / "data" / "brand_template" / "images")
            if os.path.isdir(logo_dir):
                for f in os.listdir(logo_dir):
                    if "logo" in f.lower() and f.endswith(".png"):
                        logo_path = os.path.join(logo_dir, f)
                        break
        except Exception:
            pass
        for f in os.listdir(logo_dir):
            if "logo" in f.lower() and f.endswith(".png"):
                logo_path = os.path.join(logo_dir, f)
                break

        mutations = []
        n_slides = len(prs.slides)

        for si, slide in enumerate(prs.slides):
            is_first = si == 0

            # 1. BACKGROUND
            try:
                old_bg = None
                try:
                    if slide.background.fill.type == 1:
                        old_bg = str(slide.background.fill.fore_color.rgb)
                except Exception:
                    pass
                slide.background.fill.solid()
                slide.background.fill.fore_color.rgb = bg_rgb
                mutations.append({
                    "slide": si + 1, "type": "BACKGROUND",
                    "shape": "(slide)", "before": old_bg or "(inherit)",
                    "after": str(bg_rgb),
                })
            except Exception:
                pass

            # 2. ADD LOGO to every slide (top-right corner)
            if logo_path and os.path.exists(logo_path):
                try:
                    logo = slide.shapes.add_picture(
                        logo_path, Inches(11.4), Inches(0.3), Inches(1.6), Inches(0.2)
                    )
                    mutations.append({
                        "slide": si + 1, "type": "LOGO_ADDED",
                        "shape": "(logo)", "before": "(none)", "after": "Akkodis logo",
                    })
                except Exception:
                    pass

            # 3. SHAPE-LEVEL STYLING (fill, border, text)
            for shape in _all_shapes(slide):
                shape_name = shape.name or "?"

                # --- LINE/CONNECTOR COLOR: gold ---
                try:
                    from pptx.enum.shapes import MSO_SHAPE_TYPE as MST
                    if shape.shape_type == MST.LINE:
                        try:
                            old_lc = str(shape.line.color.rgb) if shape.line.color else "(none)"
                        except Exception:
                            old_lc = "(none)"
                        shape.line.color.rgb = gold_rgb
                        shape.line.width = Pt(1.5)
                        mutations.append({
                            "slide": si + 1, "type": "LINE_COLOR",
                            "shape": shape_name, "before": old_lc, "after": "FFB81C",
                        })
                        continue
                except Exception:
                    pass

                # --- SHAPE FILL: fix light fills that make text invisible ---
                has_text = shape.has_text_frame and shape.text_frame.text.strip()
                old_fill = None
                fill_is_light = False

                try:
                    if shape.fill.type == 1:
                        old_fill = str(shape.fill.fore_color.rgb)
                        fill_lum = _luminance(shape.fill.fore_color.rgb)
                        fill_is_light = fill_lum > 0.5
                except Exception:
                    pass

                # If shape has a light fill and we're setting text to white,
                # change the fill to brand card color for contrast
                if has_text and fill_is_light:
                    try:
                        shape.fill.fore_color.rgb = card_rgb
                        mutations.append({
                            "slide": si + 1, "type": "FILL_CONTRAST_FIX",
                            "shape": shape_name,
                            "before": old_fill, "after": "081632",
                        })
                        fill_is_light = False  # now dark
                    except Exception:
                        pass

                # Also apply fill to AUTO_SHAPEs without text (card styling)
                if not has_text:
                    try:
                        st = str(shape.shape_type)
                        if "AUTO_SHAPE" in st or "FREEFORM" in st:
                            if shape.fill.type == 1 and fill_is_light:
                                shape.fill.fore_color.rgb = card_rgb
                                mutations.append({
                                    "slide": si + 1, "type": "FILL_NORMALIZE",
                                    "shape": shape_name,
                                    "before": old_fill, "after": "081632",
                                })
                    except Exception:
                        pass

                # --- TEXT: font + color with contrast against effective bg ---
                if not shape.has_text_frame:
                    continue
                text = shape.text_frame.text.strip()
                if not text:
                    continue

                lower = text.lower()
                if "font guidance" in lower or "do not change" in lower or "do not move" in lower:
                    continue

                is_title = _is_title_like(shape)
                target_font = title_font if is_title else body_font

                # Text color: contrast against the shape's fill if it has one,
                # otherwise against the slide background
                effective_bg = card_rgb if (old_fill and not fill_is_light) else bg_rgb
                target_color = title_rgb if is_title else body_rgb

                cr = _contrast_ratio(target_color, effective_bg)
                if cr < 2.0:
                    # If white text won't be visible on light fill, use dark text
                    if fill_is_light or (old_fill and _luminance(RGBColor.from_string(old_fill.lstrip("#"))) > 0.5):
                        target_color = RGBColor(0x0F, 0x17, 0x2A)  # dark text on light bg
                    else:
                        target_color = body_rgb  # fallback white
                    cr = _contrast_ratio(target_color, effective_bg)

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
                                "slide": si + 1, "type": "FONT_NAME",
                                "shape": shape_name, "before": old_font or "(inh)",
                                "after": target_font,
                            })
                        if old_color != str(target_color):
                            mutations.append({
                                "slide": si + 1, "type": "FONT_COLOR",
                                "shape": shape_name, "before": old_color,
                                "after": str(target_color),
                            })

        # Save
        output_hash = ""
        if output_path:
            prs.save(output_path)
            output_hash = hashlib.sha256(Path(output_path).read_bytes()).hexdigest()

        binary_changed = input_hash != output_hash if output_hash else False

        return {
            "deck_id": str(uuid.uuid4())[:8],
            "input_path": raw_deck_path,
            "output_path": output_path,
            "n_slides": n_slides,
            "input_sha256": input_hash,
            "output_sha256": output_hash,
            "binary_changed": binary_changed,
            "mutations": mutations,
            "mutation_count": len(mutations),
            "mutation_summary": {
                "total": len(mutations),
                "by_type": dict(Counter(m["type"] for m in mutations)),
            },
            "brand_assets": assets,
        }


from collections import Counter
