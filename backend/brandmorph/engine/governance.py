"""CorporateGovernance: enforce strict corporate typography, contrast, and branding.

Corporate Typography Contract:
1. Slide Titles:
   - Font: Times New Roman (latin, cs, ea)
   - Size: 24pt - 32pt (clamped: >32 -> 30pt, <24 -> 26pt)
   - Weight: NOT Bold (bold=False, italic=False)
   - Color: Corporate Yellow (#FFB81C) on dark, or White (#FFFFFF)
2. Subheadings:
   - Font: Arial
   - Weight: Bold (bold=True, italic=False)
   - Size: 11pt - 16pt
   - Color: White (#FFFFFF) / Cyan (#00E5FF) on dark, Dark Navy (#030C1E) on bright
3. Body Paragraphs, Bullets, Tables & Footers:
   - Font: Arial
   - Weight: Regular (bold=False, italic=False)
   - Size: >= 8pt
   - Color: White (#FFFFFF) / Muted (#93A5C4) on dark (zero black text on dark),
            Dark Navy (#030C1E) / Black on bright (L > 0.35)
4. Slide Branding:
   - Deep Navy #030C1E background
   - Subtle bottom geometric accent framing (left=0, top=7.36", width=13.333", height=0.05", #FFB81C)
   - Top-right corporate brand stamp (left=11.5", top=0.32", width=1.45", height=0.42", BRANDMORPH)
"""

from __future__ import annotations

import math
from typing import Any, Tuple
from lxml import etree
import pptx
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE, MSO_SHAPE_TYPE, PP_PLACEHOLDER
from pptx.enum.text import MSO_ANCHOR

from ..brand.profile import BrandDNA
from ..report import ChangeEntry, MorphReport

_A = "http://schemas.openxmlformats.org/drawingml/2006/main"

# Primary corporate palette constants
RGB_DARK_NAVY = RGBColor(3, 12, 30)       # #030C1E
RGB_SURFACE_CARD = RGBColor(8, 22, 50)    # #081632
RGB_SURFACE_ALT = RGBColor(8, 30, 54)     # #081E36
RGB_NAVY_TEXT = RGBColor(0, 31, 51)       # #001F33
RGB_CORP_YELLOW = RGBColor(255, 184, 28)  # #FFB81C
RGB_CYAN = RGBColor(0, 229, 255)          # #00E5FF
RGB_WHITE = RGBColor(255, 255, 255)       # #FFFFFF
RGB_MUTED = RGBColor(147, 165, 196)       # #93A5C4
RGB_BLACK = RGBColor(0, 0, 0)             # #000000

HEX_DARK_NAVY = "030C1E"
HEX_SURFACE_ALT = "081E36"
HEX_NAVY_TEXT = "001F33"
HEX_CORP_YELLOW = "FFB81C"
HEX_CYAN = "00E5FF"
HEX_WHITE = "FFFFFF"
HEX_MUTED = "93A5C4"
HEX_BLACK = "000000"


def relative_luminance(r: int, g: int, b: int) -> float:
    """Compute relative luminance L per WCAG 2.1 specification."""
    def channel_lin(c: int) -> float:
        s = c / 255.0
        return s / 12.92 if s <= 0.04045 else math.pow((s + 0.055) / 1.055, 2.4)
    return 0.2126 * channel_lin(r) + 0.7152 * channel_lin(g) + 0.0722 * channel_lin(b)


def hex_to_rgb(hex_str: str) -> Tuple[int, int, int]:
    clean = hex_str.strip().lstrip("#")
    if len(clean) == 3:
        clean = "".join(c * 2 for c in clean)
    if len(clean) >= 6:
        try:
            return int(clean[0:2], 16), int(clean[2:4], 16), int(clean[4:6], 16)
        except ValueError:
            pass
    return 3, 12, 30


class CorporateGovernancePass:
    def __init__(self, dna: BrandDNA, report: MorphReport):
        self.dna = dna
        self.report = report

    def run(self, prs: pptx.Presentation) -> None:
        for idx, slide in enumerate(prs.slides):
            self._apply_slide_template(slide)
            self._govern_slide_shapes(slide, idx)

    def _apply_slide_template(self, slide) -> None:
        """Enforce deep navy canvas background, bottom accent line, and top-right stamp."""
        # 1. Slide Background
        try:
            slide.background.fill.solid()
            slide.background.fill.fore_color.rgb = RGB_DARK_NAVY
        except Exception:
            pass

        # Check existing custom shapes to avoid duplication
        has_bottom_frame = False
        has_stamp = False
        for s in slide.shapes:
            s_name = getattr(s, "name", "") or ""
            if "BrandMorphBottomFrame" in s_name or "BrandMorphAccentLine" in s_name:
                has_bottom_frame = True
            if "BrandMorph_Logo_Stamp" in s_name or "BrandMorphStamp" in s_name:
                has_stamp = True

        # 2. Subtle geometric bottom accent line
        if not has_bottom_frame:
            try:
                line = slide.shapes.add_shape(
                    MSO_SHAPE.RECTANGLE,
                    Inches(0.0), Inches(7.36), Inches(13.333), Inches(0.05)
                )
                line.name = "BrandMorphBottomFrame"
                line.fill.solid()
                line.fill.fore_color.rgb = RGB_CORP_YELLOW
                if hasattr(line, "line") and line.line:
                    line.line.fill.background()
            except Exception:
                pass

        # 3. Clean top-right brand wordmark/stamp (left=11.55", top=0.35", width=1.25", height=0.35")
        if not has_stamp:
            try:
                stamp = slide.shapes.add_textbox(
                    Inches(11.55), Inches(0.35), Inches(1.25), Inches(0.35)
                )
                stamp.name = "BrandMorph_Logo_Stamp"
                tf = stamp.text_frame
                tf.word_wrap = False
                tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
                p = tf.paragraphs[0]
                p.text = "BRANDMORPH"
                p.alignment = pptx.enum.text.PP_ALIGN.RIGHT
                p.font.name = "Arial"
                p.font.size = Pt(9.5)
                p.font.bold = True
                p.font.color.rgb = RGB_CORP_YELLOW
            except Exception:
                pass

    def _govern_slide_shapes(self, slide, slide_idx: int) -> None:
        """Recursively walk all shapes, tables, and groups to enforce typography & contrast."""
        for shape in list(slide.shapes):
            self._process_shape(shape, slide_idx, default_bg=HEX_DARK_NAVY)

    def _process_shape(self, shape, slide_idx: int, default_bg: str) -> None:
        # Avoid overriding our own brand stamp
        if getattr(shape, "name", "") in ("BrandMorph_Logo_Stamp", "BrandMorphStamp"):
            return

        # 1. Group shapes: recursively process children
        if shape.shape_type == MSO_SHAPE_TYPE.GROUP:
            for child in shape.shapes:
                self._process_shape(child, slide_idx, default_bg)
            return

        # 2. Table shapes: enforce corporate table styling and bounds
        if getattr(shape, "has_table", False) and shape.has_table:
            self._govern_table(shape)
            return

    def _govern_table(self, shape) -> None:
        """Enforce clean corporate Table styling per task specifications."""
        try:
            shape.left = Inches(0.80)
            shape.top = Inches(1.65)
            shape.width = Inches(11.73)
            current_h = shape.height.inches if shape.height else 4.0
            shape.height = Inches(min(4.8, max(2.5, current_h)))
        except Exception:
            pass

        table = shape.table
        for r_idx, row in enumerate(table.rows):
            is_header = (r_idx == 0)
            row_fill_rgb = RGB_CORP_YELLOW if is_header else (RGB_SURFACE_ALT if (r_idx % 2 == 1) else RGB_DARK_NAVY)
            row_fill_hex = HEX_CORP_YELLOW if is_header else (HEX_SURFACE_ALT if (r_idx % 2 == 1) else HEX_DARK_NAVY)

            for c_idx, cell in enumerate(row.cells):
                try:
                    cell.vertical_anchor = MSO_ANCHOR.MIDDLE
                except Exception:
                    pass

                try:
                    cell.fill.solid()
                    cell.fill.fore_color.rgb = row_fill_rgb
                except Exception:
                    pass

                if not cell.text_frame:
                    continue

                if is_header:
                    for p in cell.text_frame.paragraphs:
                        for r in p.runs:
                            r.font.name = "Arial"
                            r.font.size = Pt(12)
                            r.font.bold = True
                            r.font.italic = False
                            r.font.color.rgb = RGB_NAVY_TEXT
                            self._inject_run_xml(r, "Arial", HEX_NAVY_TEXT)
                        self._inject_para_def_rpr(p, is_title=False, is_bright_bg=True)
                else:
                    is_first_col = (c_idx == 0)
                    target_color_rgb = RGB_CORP_YELLOW if is_first_col else RGB_WHITE
                    target_color_hex = HEX_CORP_YELLOW if is_first_col else HEX_WHITE
                    target_bold = True if is_first_col else False

                    for p in cell.text_frame.paragraphs:
                        for r in p.runs:
                            r.font.name = "Arial"
                            r.font.size = Pt(11)
                            r.font.bold = target_bold
                            r.font.italic = False
                            r.font.color.rgb = target_color_rgb
                            self._inject_run_xml(r, "Arial", target_color_hex)
                        self._inject_para_def_rpr(p, is_title=False, is_bright_bg=False)

        # 3. Text frames in AutoShapes, TextBoxes, Placeholders
        if shape.has_text_frame:
            shape_bg = self._get_shape_fill_hex(shape) or default_bg
            self._process_text_frame(
                shape.text_frame, shape, slide_idx, effective_bg=shape_bg, is_table=False
            )

    def _get_shape_fill_hex(self, shape) -> str | None:
        try:
            if shape.fill and shape.fill.type == 1:  # solid fill
                if hasattr(shape.fill, "fore_color") and hasattr(shape.fill.fore_color, "rgb"):
                    return f"{shape.fill.fore_color.rgb}".upper()
        except Exception:
            pass
        return None

    def _is_slide_title(self, shape, para, is_table: bool) -> bool:
        if is_table:
            return False

        # Placeholder checks
        if getattr(shape, "is_placeholder", False):
            try:
                p_type = shape.placeholder_format.type
                if p_type in (PP_PLACEHOLDER.TITLE, PP_PLACEHOLDER.CENTER_TITLE):
                    return True
            except Exception:
                pass

        # Name checks
        name = (getattr(shape, "name", "") or "").lower()
        if "title" in name and "subtitle" not in name:
            return True

        # Position / Size heuristic
        top_in = shape.top.inches if shape.top else 2.0
        width_in = shape.width.inches if shape.width else 0.0

        max_run_pt = 0.0
        for r in para.runs:
            if r.font and r.font.size and r.font.size.pt:
                max_run_pt = max(max_run_pt, r.font.size.pt)
        if para.font and para.font.size and para.font.size.pt:
            max_run_pt = max(max_run_pt, para.font.size.pt)

        # Primary title:
        # - Any top banner (top < 2.0" and font >= 18pt or wide banner)
        # - Centered cover slide title (top < 3.2" and font >= 22pt and width >= 5.0")
        if top_in < 2.0 and (max_run_pt >= 18.0 or (max_run_pt == 0.0 and width_in >= 4.0)):
            return True
        if top_in < 3.2 and max_run_pt >= 22.0 and width_in >= 4.5:
            return True

        return False

    def _is_subheading(self, shape, para, is_table: bool) -> bool:
        if is_table:
            return False

        if getattr(shape, "is_placeholder", False):
            try:
                if shape.placeholder_format.type == PP_PLACEHOLDER.SUBTITLE:
                    return True
            except Exception:
                pass

        name = (getattr(shape, "name", "") or "").lower()
        if "subtitle" in name or "subheading" in name or "card_title" in name:
            return True

        pt_size = para.font.size.pt if para.font and para.font.size else 12.0
        txt = para.text.strip()
        if 13.0 <= pt_size <= 22.0 and 0 < len(txt) <= 60:
            return True

        return False

    def _process_text_frame(
        self, text_frame, shape, slide_idx: int, effective_bg: str, is_table: bool
    ) -> None:
        bg_rgb = hex_to_rgb(effective_bg)
        bg_lum = relative_luminance(*bg_rgb)
        is_bright_bg = bg_lum > 0.35  # e.g. Cyan #00FFFF, Yellow #FFB81C, White #FFFFFF

        for p_idx, para in enumerate(text_frame.paragraphs):
            txt = para.text.strip()
            if not txt:
                continue

            # Ensure runs exist
            if len(para.runs) == 0:
                para.add_run().text = txt

            is_title = self._is_slide_title(shape, para, is_table)
            is_sub = not is_title and self._is_subheading(shape, para, is_table)

            for run in para.runs:
                # -------------------------------------------------------------
                # 1. TYPOGRAPHY: Font Family, Size, Weight
                # -------------------------------------------------------------
                if is_title:
                    # Title: Times New Roman, 24pt-32pt, NOT bold, NOT italic
                    target_font = "Times New Roman"
                    current_pt = run.font.size.pt if run.font and run.font.size else 28.0
                    if current_pt > 32.0:
                        target_pt = 30.0
                    elif current_pt < 24.0:
                        target_pt = 26.0
                    else:
                        target_pt = current_pt
                    target_bold = False
                    target_italic = False
                elif is_sub:
                    # Subheading: Arial, 11pt-16pt, can be bold, NOT italic
                    target_font = "Arial"
                    current_pt = run.font.size.pt if run.font and run.font.size else 14.0
                    target_pt = max(11.0, min(16.0, current_pt))
                    target_bold = True
                    target_italic = False
                else:
                    # Body, Bullets, Tables, Footers: Arial, >= 8pt, NO bold, NO italic
                    target_font = "Arial"
                    current_pt = run.font.size.pt if run.font and run.font.size else 12.0
                    target_pt = max(8.0, current_pt)
                    target_bold = False
                    target_italic = False

                run.font.name = target_font
                run.font.size = Pt(target_pt)
                run.font.bold = target_bold
                run.font.italic = target_italic

                # -------------------------------------------------------------
                # 2. CONTRAST RESOLVER: Background-Aware Color Selection
                # -------------------------------------------------------------
                cur_hex = None
                if run.font.color and run.font.color.type == 1:
                    try:
                        cur_hex = str(run.font.color.rgb).upper()
                    except Exception:
                        pass

                if is_bright_bg:
                    # Bright background (Cyan, Yellow, Light surface) -> Dark Navy
                    target_color_rgb = RGB_DARK_NAVY
                    target_color_hex = HEX_DARK_NAVY
                else:
                    # Dark background (Dark Navy canvas #030C1E, Card #081632)
                    if is_title:
                        # Corporate Yellow (#FFB81C) or White (#FFFFFF)
                        if cur_hex in ("FFFFFF", "F2F6FC"):
                            target_color_rgb = RGB_WHITE
                            target_color_hex = HEX_WHITE
                        else:
                            target_color_rgb = RGB_CORP_YELLOW
                            target_color_hex = HEX_CORP_YELLOW
                    elif is_sub:
                        if cur_hex and cur_hex in (HEX_CORP_YELLOW, HEX_CYAN, "FFFFFF", "F2F6FC"):
                            target_color_rgb = run.font.color.rgb
                            target_color_hex = cur_hex
                        else:
                            target_color_rgb = RGB_WHITE
                            target_color_hex = HEX_WHITE
                    else:
                        # Body / Table / Bullets / Footers:
                        # If run already has an intentional, readable color (L > 0.15) like muted #93A5C4, danger #E5484D, white #FFFFFF:
                        is_readable = False
                        if cur_hex:
                            try:
                                r_lum = relative_luminance(*hex_to_rgb(cur_hex))
                                if r_lum >= 0.10:
                                    is_readable = True
                            except Exception:
                                pass

                        if is_readable:
                            target_color_rgb = run.font.color.rgb
                            target_color_hex = cur_hex
                        else:
                            # Black (#000000), inherited None, or unreadable dark ink -> FORCE WHITE
                            target_color_rgb = RGB_WHITE
                            target_color_hex = HEX_WHITE

                run.font.color.rgb = target_color_rgb

                # -------------------------------------------------------------
                # 3. XML SOLIDFILL & SCRIPT FACES INJECTION
                # -------------------------------------------------------------
                self._inject_run_xml(run, target_font, target_color_hex)

            # Also set default run properties on paragraph
            self._inject_para_def_rpr(para, is_title, is_bright_bg)

    def _inject_run_xml(self, run, font_family: str, color_hex: str) -> None:
        """Explicitly inject drawingML <a:solidFill> and typeface tags into run's XML in schema-compliant order."""
        try:
            clean_hex = color_hex.lstrip("#")
            if len(clean_hex) == 6:
                r_val = int(clean_hex[0:2], 16)
                g_val = int(clean_hex[2:4], 16)
                b_val = int(clean_hex[4:6], 16)
                run.font.color.rgb = RGBColor(r_val, g_val, b_val)
            run.font.name = font_family

            rPr = run._r.get_or_add_rPr()

            # 1. Clear conflicting fills (schemeClr, noFill, sysClr)
            for child in list(rPr):
                tag = etree.QName(child).localname
                if tag in ("solidFill", "schemeClr", "noFill", "sysClr", "gradFill", "blipFill"):
                    rPr.remove(child)

            # 2. Add explicit solidFill srgbClr BEFORE typeface tags
            solidFill = etree.Element(f"{{{_A}}}solidFill")
            srgb = etree.SubElement(solidFill, f"{{{_A}}}srgbClr")
            srgb.set("val", clean_hex)

            first_typeface = None
            for child in list(rPr):
                tag = etree.QName(child).localname
                if tag in ("latin", "ea", "cs", "sym", "hlinkClick", "hlinkMouseOver", "rtl", "extLst"):
                    first_typeface = child
                    break

            if first_typeface is not None:
                first_typeface.addprevious(solidFill)
            else:
                rPr.append(solidFill)

            # 3. Ensure typeface tags
            for tag in ("latin", "cs", "ea"):
                el = rPr.find(f"{{{_A}}}{tag}")
                if el is None:
                    el = etree.SubElement(rPr, f"{{{_A}}}{tag}")
                el.set("typeface", font_family)
        except Exception:
            pass

    def _inject_para_def_rpr(self, para, is_title: bool, is_bright_bg: bool) -> None:
        try:
            pPr = para._p.get_or_add_pPr()
            defRPr = pPr.find(f"{{{_A}}}defRPr")
            if defRPr is None:
                defRPr = etree.SubElement(pPr, f"{{{_A}}}defRPr")

            for child in list(defRPr):
                tag = etree.QName(child).localname
                if tag in ("solidFill", "schemeClr", "noFill", "sysClr"):
                    defRPr.remove(child)

            solidFill = etree.Element(f"{{{_A}}}solidFill")
            srgb = etree.SubElement(solidFill, f"{{{_A}}}srgbClr")
            color_hex = HEX_DARK_NAVY if is_bright_bg else (HEX_CORP_YELLOW if is_title else HEX_WHITE)
            srgb.set("val", color_hex)

            first_typeface = None
            for child in list(defRPr):
                tag = etree.QName(child).localname
                if tag in ("latin", "ea", "cs", "sym", "hlinkClick", "hlinkMouseOver", "rtl", "extLst"):
                    first_typeface = child
                    break

            if first_typeface is not None:
                first_typeface.addprevious(solidFill)
            else:
                defRPr.append(solidFill)

            family = "Times New Roman" if is_title else "Arial"
            for tag in ("latin", "cs", "ea"):
                el = defRPr.find(f"{{{_A}}}{tag}")
                if el is None:
                    el = etree.SubElement(defRPr, f"{{{_A}}}{tag}")
                el.set("typeface", family)
        except Exception:
            pass

