"""Dynamic Slide-Graph & Archetype Engine.

Inspects every slide's 16D shape-graph features, dynamically classifies
into one of 8 corporate archetypes, and executes image-aware reflow,
top-left title snapping, contrast resolution, and brand stamping.
"""

from __future__ import annotations

import math
import os
import json
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from lxml import etree
import pptx
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE, MSO_SHAPE_TYPE, PP_PLACEHOLDER
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR

from ..brand.profile import BrandDNA
from ..report import MorphReport

_A = "http://schemas.openxmlformats.org/drawingml/2006/main"

# Primary corporate palette constants
RGB_DARK_NAVY = RGBColor(3, 12, 30)       # #030C1E
RGB_CANVAS_NAVY = RGBColor(3, 12, 30)     # #030C1E
RGB_SURFACE_CARD = RGBColor(8, 22, 50)    # #081632
RGB_SURFACE_ALT = RGBColor(8, 30, 54)     # #081E36
RGB_NAVY_TEXT = RGBColor(0, 31, 51)       # #001F33 Dark Navy
RGB_CORP_GOLD = RGBColor(255, 184, 28)    # #FFB81C
RGB_CYAN = RGBColor(0, 229, 255)          # #00E5FF
RGB_WHITE = RGBColor(255, 255, 255)       # #FFFFFF
RGB_MUTED = RGBColor(147, 165, 196)       # #93A5C4
RGB_BLACK = RGBColor(0, 0, 0)             # #000000

HEX_DARK_NAVY = "030C1E"
HEX_CANVAS_NAVY = "030C1E"
HEX_SURFACE_ALT = "081E36"
HEX_NAVY_TEXT = "001F33"
HEX_CORP_GOLD = "FFB81C"
HEX_CYAN = "00E5FF"
HEX_WHITE = "FFFFFF"
HEX_MUTED = "93A5C4"
HEX_BLACK = "000000"


class SlideArchetype(str, Enum):
    COVER_SLIDE = "Cover Slide"
    AGENDA_SLIDE = "Agenda + Photo Grid"
    SECTION_SPLITTER = "Section Splitter"
    DATA_TABLE_SLIDE = "Data Table"
    PROCESS_TIMELINE = "Process Timeline"
    TEAM_OR_GALLERY_GRID = "Team Gallery Grid"
    MULTI_CARD_CONTENT = "Multi-Card Content"
    CLOSING_SLIDE = "Closing Slide"


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


class SlideGraphClassifier:
    """Extracts 16D shape-graph features and classifies slide archetype."""

    @staticmethod
    def extract_16d_features(slide, slide_idx: int, total_slides: int) -> List[float]:
        """Extract a 16-dimensional geometric and semantic feature vector for a slide."""
        features = [0.0] * 16

        # f0: Normalized slide position in deck (0.0 = first, 1.0 = last)
        features[0] = float(slide_idx) / max(1.0, float(total_slides - 1))

        # Shape counts and semantic detection
        has_table = False
        table_cells = 0
        pictures = []
        text_shapes = []
        shapes_sorted_x = []

        all_text = []
        has_center_title = False
        has_title_placeholder = False

        for shape in slide.shapes:
            # Check placeholders
            if getattr(shape, "is_placeholder", False):
                try:
                    pt = shape.placeholder_format.type
                    if pt == PP_PLACEHOLDER.CENTER_TITLE:
                        has_center_title = True
                    elif pt == PP_PLACEHOLDER.TITLE:
                        has_title_placeholder = True
                except Exception:
                    pass

            # Table
            if getattr(shape, "has_table", False) and shape.has_table:
                has_table = True
                try:
                    table_cells += len(shape.table.rows) * len(shape.table.columns)
                except Exception:
                    table_cells += 10

            # Picture / Image
            is_pic = False
            try:
                if shape.shape_type == MSO_SHAPE_TYPE.PICTURE or hasattr(shape, "image"):
                    if getattr(shape, "image", None) is not None:
                        is_pic = True
            except Exception:
                pass
            if is_pic:
                pictures.append(shape)

            # Text frame
            if shape.has_text_frame:
                txt = shape.text_frame.text.strip()
                if txt and not getattr(shape, "name", "").startswith("BrandMorph"):
                    text_shapes.append(shape)
                    all_text.append(txt.lower())

            # Position for horizontal sequence check
            if hasattr(shape, "left") and shape.left is not None:
                shapes_sorted_x.append((shape.left.inches, shape.top.inches if shape.top else 0.0, shape))

        joined_text = " ".join(all_text)

        # f1: Has center title
        features[1] = 1.0 if has_center_title else 0.0
        # f2: Has title placeholder
        features[2] = 1.0 if has_title_placeholder else 0.0
        # f3: Has table
        features[3] = 1.0 if has_table else 0.0
        # f4: Normalized table cell count
        features[4] = min(1.0, float(table_cells) / 30.0)
        # f5: Picture count
        features[5] = float(len(pictures))

        # f6: Pictures aligned horizontally in a row (e.g. team or gallery)
        pic_row = False
        if len(pictures) >= 3:
            tops = [p.top.inches for p in pictures if hasattr(p, "top") and p.top is not None]
            if len(tops) >= 3 and (max(tops) - min(tops)) < 0.6:
                pic_row = True
        features[6] = 1.0 if pic_row else 0.0

        # f7: Timeline keywords
        timeline_kw = any(w in joined_text for w in ["timeline", "process", "roadmap", "milestone", "phases", "step 1", "q1", "q2", "q3", "q4"])
        features[7] = 1.0 if timeline_kw else 0.0

        # f8: Horizontal shape sequence (>=3 shapes ordered left to right with similar Y)
        h_seq_count = 0
        if len(shapes_sorted_x) >= 3:
            shapes_sorted_x.sort(key=lambda s: s[0])
            cur_seq = 1
            for i in range(1, len(shapes_sorted_x)):
                prev_x, prev_y, _ = shapes_sorted_x[i - 1]
                cur_x, cur_y, _ = shapes_sorted_x[i]
                if cur_x > prev_x and abs(cur_y - prev_y) < 1.0:
                    cur_seq += 1
                else:
                    cur_seq = 1
                h_seq_count = max(h_seq_count, cur_seq)
        features[8] = float(h_seq_count)

        # f9: Agenda keywords
        agenda_kw = any(w in joined_text for w in ["agenda", "contents", "table of contents", "overview", "topics"])
        features[9] = 1.0 if agenda_kw else 0.0

        # f10: Closing / Thank you keywords
        closing_kw = any(w in joined_text for w in ["thank you", "thanks", "q&a", "questions", "contact", "reach out", "get in touch"])
        features[10] = 1.0 if closing_kw else 0.0

        # f11: Is last slide
        features[11] = 1.0 if (slide_idx == total_slides - 1) else 0.0

        # f12: Text card count
        features[12] = float(len(text_shapes))

        # f13: Team keywords
        team_kw = any(w in joined_text for w in ["team", "leadership", "board", "executives", "speakers", "our team"])
        features[13] = 1.0 if team_kw else 0.0

        # f14: Team photo caption pairs (>=3 pictures with a text box directly underneath)
        caption_pairs = 0
        for pic in pictures:
            p_left = pic.left.inches if hasattr(pic, "left") and pic.left else 0.0
            p_top = pic.top.inches if hasattr(pic, "top") and pic.top else 0.0
            p_w = pic.width.inches if hasattr(pic, "width") and pic.width else 2.0
            p_h = pic.height.inches if hasattr(pic, "height") and pic.height else 2.0
            for ts in text_shapes:
                t_left = ts.left.inches if hasattr(ts, "left") and ts.left else 0.0
                t_top = ts.top.inches if hasattr(ts, "top") and ts.top else 0.0
                # Directly below picture (within 1.8" of picture bottom) and horizontally overlapping
                if (p_top + p_h - 0.2) <= t_top <= (p_top + p_h + 1.8) and abs(t_left - p_left) < 1.0:
                    caption_pairs += 1
                    break
        features[14] = float(caption_pairs)

        # f15: Quote / Short section splitter (few text shapes, short word count)
        total_words = sum(len(txt.split()) for txt in all_text)
        features[15] = 1.0 if (len(text_shapes) <= 2 and total_words <= 25 and not has_table) else 0.0

        return features

    @classmethod
    def classify(cls, slide, slide_idx: int, total_slides: int) -> SlideArchetype:
        """Classify slide using 16D graph features and golden_brain.json weights if present."""
        feats = cls.extract_16d_features(slide, slide_idx, total_slides)

        # -----------------------------------------------------------------
        # NEURO-SYMBOLIC CONSENSUS CHECK (Corporate DNA Golden Pair Guard)
        # 1. Slide index 0 is strictly COVER_SLIDE
        # 2. Any slide containing a Table is strictly DATA_TABLE_SLIDE
        # 3. >=3 timeline nodes or horizontal sequence is strictly PROCESS_TIMELINE
        # -----------------------------------------------------------------
        if slide_idx == 0:
            return SlideArchetype.COVER_SLIDE

        has_table_shape = feats[3] > 0.5 or any(getattr(s, "has_table", False) and s.has_table for s in slide.shapes)
        if has_table_shape:
            return SlideArchetype.DATA_TABLE_SLIDE

        h_seq = feats[8] >= 3.0
        timeline_kw = feats[7] > 0.5
        if h_seq or (timeline_kw and feats[12] >= 3):
            return SlideArchetype.PROCESS_TIMELINE

        # Check for external golden_brain.json weights
        weights_paths = [
            os.path.join(os.path.dirname(__file__), "golden_brain.json"),
            os.path.join(os.path.dirname(__file__), "..", "..", "brands", "golden_brain.json"),
        ]
        for wp in weights_paths:
            if os.path.exists(wp):
                try:
                    with open(wp, "r", encoding="utf-8") as f:
                        brain = json.load(f)
                    if "archetypes" in brain and "weights" in brain:
                        # Linear projection scoring if brain model is provided
                        scores = {}
                        for arch_name, w_vec in brain["weights"].items():
                            bias = brain.get("biases", {}).get(arch_name, 0.0)
                            scores[arch_name] = sum(f * w for f, w in zip(feats, w_vec)) + bias
                        best_arch = max(scores, key=scores.get)
                        for member in SlideArchetype:
                            if member.name == best_arch or member.value == best_arch:
                                return member
                except Exception:
                    pass

        # High-precision deterministic decision graph based on 16D features
        has_table = feats[3] > 0.5
        pic_count = feats[5]
        pic_row = feats[6] > 0.5
        timeline_kw = feats[7] > 0.5
        h_seq = feats[8] >= 3.0
        agenda_kw = feats[9] > 0.5
        closing_kw = feats[10] > 0.5
        is_last = feats[11] > 0.5
        text_count = feats[12]
        team_kw = feats[13] > 0.5
        caption_pairs = feats[14] >= 3.0
        is_splitter = feats[15] > 0.5

        # 1. Table slide
        if has_table:
            return SlideArchetype.DATA_TABLE_SLIDE

        # 2. Cover slide
        if slide_idx == 0 or (feats[1] > 0.5 and text_count <= 2 and not is_last):
            return SlideArchetype.COVER_SLIDE

        # 3. Closing slide
        if closing_kw or (is_last and text_count <= 3 and not h_seq):
            return SlideArchetype.CLOSING_SLIDE

        # 4. Team or gallery grid
        if caption_pairs or (pic_count >= 3 and (pic_row or team_kw)):
            return SlideArchetype.TEAM_OR_GALLERY_GRID

        # 5. Process timeline
        if timeline_kw or (h_seq and pic_count <= 1):
            return SlideArchetype.PROCESS_TIMELINE

        # 6. Agenda slide
        if agenda_kw or (slide_idx <= 1 and text_count >= 3 and not timeline_kw):
            return SlideArchetype.AGENDA_SLIDE

        # 7. Section splitter / Quote
        if is_splitter and slide_idx > 0:
            return SlideArchetype.SECTION_SPLITTER

        # 8. Multi-card content (standard content slide)
        return SlideArchetype.MULTI_CARD_CONTENT


class ArchetypeEngine:
    """Dynamic layout reflow, contrast resolver, and brand enforcement engine."""

    def __init__(self, dna: BrandDNA, report: MorphReport):
        self.dna = dna
        self.report = report

    def run(self, prs: pptx.Presentation) -> None:
        total_slides = len(prs.slides)
        for idx, slide in enumerate(prs.slides):
            archetype = SlideGraphClassifier.classify(slide, idx, total_slides)
            self._apply_slide_branding(slide)
            self._reflow_and_govern_slide(slide, idx, total_slides, archetype)

    def _apply_slide_branding(self, slide) -> None:
        """Enforce dark canvas background, bottom gold accent line, and single brand stamp."""
        # 1. Slide Background
        try:
            slide.background.fill.solid()
            slide.background.fill.fore_color.rgb = RGB_CANVAS_NAVY
        except Exception:
            pass

        # Check existing shapes to guarantee no duplication
        has_bottom_frame = False
        has_stamp = False
        for s in slide.shapes:
            s_name = getattr(s, "name", "") or ""
            if "BrandMorphBottomFrame" in s_name or "BrandMorphAccentLine" in s_name:
                has_bottom_frame = True
            if "BrandMorph_Logo_Stamp" in s_name or "BrandMorphStamp" in s_name:
                has_stamp = True

        # 2. Geometric bottom accent line: left=0, top=7.36", width=13.333", height=0.05", #FFB81C
        if not has_bottom_frame:
            try:
                line = slide.shapes.add_shape(
                    MSO_SHAPE.RECTANGLE,
                    Inches(0.0), Inches(7.36), Inches(13.333), Inches(0.05)
                )
                line.name = "BrandMorphBottomFrame"
                line.fill.solid()
                line.fill.fore_color.rgb = RGB_CORP_GOLD
                if hasattr(line, "line") and line.line:
                    line.line.fill.background()
            except Exception:
                pass

        # 3. Clean corporate wordmark stamp: left=11.55", top=0.35", width=1.25", height=0.35"
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
                p.alignment = PP_ALIGN.RIGHT
                p.font.name = "Arial"
                p.font.size = Pt(9.5)
                p.font.bold = True
                p.font.color.rgb = RGB_CORP_GOLD
                # Inject explicit solidFill XML
                self._inject_run_xml(p.runs[0], "Arial", HEX_CORP_GOLD)
            except Exception:
                pass

    def _find_slide_title_and_subtitle(self, slide) -> Tuple[Optional[Any], Optional[Any]]:
        """Identify the primary title shape and optional subtitle shape."""
        title_shape = None
        subtitle_shape = None

        # 1. Placeholders first
        for shape in slide.shapes:
            if getattr(shape, "is_placeholder", False):
                try:
                    pt = shape.placeholder_format.type
                    if pt in (PP_PLACEHOLDER.TITLE, PP_PLACEHOLDER.CENTER_TITLE):
                        title_shape = shape
                    elif pt == PP_PLACEHOLDER.SUBTITLE:
                        subtitle_shape = shape
                except Exception:
                    pass

        # 2. Heuristics if not found via placeholder
        if not title_shape:
            candidate_titles = []
            for shape in slide.shapes:
                if not shape.has_text_frame:
                    continue
                name = (getattr(shape, "name", "") or "").lower()
                if "brandmorph" in name:
                    continue
                top_in = shape.top.inches if shape.top else 99.0
                txt = shape.text_frame.text.strip()
                if not txt:
                    continue
                max_pt = 0.0
                for p in shape.text_frame.paragraphs:
                    for r in p.runs:
                        if r.font and r.font.size and r.font.size.pt:
                            max_pt = max(max_pt, r.font.size.pt)
                candidate_titles.append((top_in, -max_pt, shape))

            if candidate_titles:
                candidate_titles.sort(key=lambda item: (item[0], item[1]))
                title_shape = candidate_titles[0][2]
                if len(candidate_titles) > 1 and candidate_titles[1][0] < 4.0:
                    subtitle_shape = candidate_titles[1][2]

        return title_shape, subtitle_shape

    def _reflow_and_govern_slide(
        self, slide, slide_idx: int, total_slides: int, archetype: SlideArchetype
    ) -> None:
        """Execute archetype reflow rules and govern all shapes."""
        title_shape, subtitle_shape = self._find_slide_title_and_subtitle(slide)
        if archetype not in (SlideArchetype.COVER_SLIDE, SlideArchetype.SECTION_SPLITTER):
            subtitle_shape = None

        # ---------------------------------------------------------------------
        # RULE A: Title Detection & Top-Left Positioning
        # ---------------------------------------------------------------------
        if title_shape and title_shape.has_text_frame:
            tf = title_shape.text_frame
            if archetype == SlideArchetype.COVER_SLIDE:
                # Cover slide: Hero zone left=0.85", top=2.2", width=11.0", height=1.0"
                try:
                    title_shape.left = Inches(0.85)
                    title_shape.top = Inches(2.2)
                    title_shape.width = Inches(11.0)
                    title_shape.height = Inches(1.0)
                except Exception:
                    pass
                for p in tf.paragraphs:
                    p.alignment = PP_ALIGN.LEFT
                    for r in p.runs:
                        cur_hex = None
                        if r.font and r.font.color and r.font.color.type == 1:
                            try:
                                cur_hex = str(r.font.color.rgb).upper()
                            except Exception:
                                pass
                        t_hex = HEX_WHITE if cur_hex in ("FFFFFF", "F2F6FC") else HEX_CORP_GOLD
                        t_rgb = RGB_WHITE if t_hex == HEX_WHITE else RGB_CORP_GOLD

                        r.font.name = "Times New Roman"
                        r.font.size = Pt(32)
                        r.font.bold = False
                        r.font.italic = False
                        r.font.color.rgb = t_rgb
                        self._inject_run_xml(r, "Times New Roman", t_hex)
                    self._inject_para_def_rpr(p, is_title=True, is_bright_bg=False)

                # Subtitle directly below at left=0.85", top=3.2"
                if subtitle_shape and subtitle_shape != title_shape and subtitle_shape.has_text_frame:
                    try:
                        subtitle_shape.left = Inches(0.85)
                        subtitle_shape.top = Inches(3.2)
                        subtitle_shape.width = Inches(11.0)
                        subtitle_shape.height = Inches(0.75)
                    except Exception:
                        pass
                    for p in subtitle_shape.text_frame.paragraphs:
                        p.alignment = PP_ALIGN.LEFT
                        for r in p.runs:
                            r.font.name = "Arial"
                            r.font.size = Pt(16)
                            r.font.bold = False
                            r.font.italic = False
                            r.font.color.rgb = RGB_WHITE
                            self._inject_run_xml(r, "Arial", HEX_WHITE)
                        self._inject_para_def_rpr(p, is_title=False, is_bright_bg=False)

            elif archetype == SlideArchetype.SECTION_SPLITTER:
                # Section splitter: Hero title left=0.85", top=2.0", Times New Roman 32pt
                try:
                    title_shape.left = Inches(0.85)
                    title_shape.top = Inches(2.0)
                    title_shape.width = Inches(11.0)
                    title_shape.height = Inches(1.0)
                except Exception:
                    pass
                for p in tf.paragraphs:
                    p.alignment = PP_ALIGN.LEFT
                    for r in p.runs:
                        cur_hex = None
                        if r.font and r.font.color and r.font.color.type == 1:
                            try:
                                cur_hex = str(r.font.color.rgb).upper()
                            except Exception:
                                pass
                        t_hex = HEX_WHITE if cur_hex in ("FFFFFF", "F2F6FC") else HEX_CORP_GOLD
                        t_rgb = RGB_WHITE if t_hex == HEX_WHITE else RGB_CORP_GOLD

                        r.font.name = "Times New Roman"
                        r.font.size = Pt(32)
                        r.font.bold = False
                        r.font.italic = False
                        r.font.color.rgb = t_rgb
                        self._inject_run_xml(r, "Times New Roman", t_hex)
                    self._inject_para_def_rpr(p, is_title=True, is_bright_bg=False)

                if subtitle_shape and subtitle_shape != title_shape and subtitle_shape.has_text_frame:
                    try:
                        subtitle_shape.left = Inches(0.85)
                        subtitle_shape.top = Inches(3.1)
                        subtitle_shape.width = Inches(11.0)
                        subtitle_shape.height = Inches(0.75)
                    except Exception:
                        pass
                    for p in subtitle_shape.text_frame.paragraphs:
                        p.alignment = PP_ALIGN.LEFT
                        for r in p.runs:
                            r.font.name = "Arial"
                            r.font.size = Pt(16)
                            r.font.bold = False
                            r.font.italic = False
                            r.font.color.rgb = RGB_WHITE
                            self._inject_run_xml(r, "Arial", HEX_WHITE)
                        self._inject_para_def_rpr(p, is_title=False, is_bright_bg=False)

            elif archetype == SlideArchetype.CLOSING_SLIDE:
                try:
                    title_shape.left = Inches(0.85)
                    title_shape.top = Inches(2.5)
                    title_shape.width = Inches(11.0)
                    title_shape.height = Inches(1.0)
                except Exception:
                    pass
                for p in tf.paragraphs:
                    p.alignment = PP_ALIGN.LEFT
                    for r in p.runs:
                        cur_hex = None
                        if r.font and r.font.color and r.font.color.type == 1:
                            try:
                                cur_hex = str(r.font.color.rgb).upper()
                            except Exception:
                                pass
                        t_hex = HEX_WHITE if cur_hex in ("FFFFFF", "F2F6FC") else HEX_CORP_GOLD
                        t_rgb = RGB_WHITE if t_hex == HEX_WHITE else RGB_CORP_GOLD

                        r.font.name = "Times New Roman"
                        r.font.size = Pt(32)
                        r.font.bold = False
                        r.font.italic = False
                        r.font.color.rgb = t_rgb
                        self._inject_run_xml(r, "Times New Roman", t_hex)
                    self._inject_para_def_rpr(p, is_title=True, is_bright_bg=False)

            else:
                # Content slides: ALWAYS snap title to Top-Left anchor: left=0.65", top=0.38", width=10.4", height=0.75"
                try:
                    title_shape.left = Inches(0.65)
                    title_shape.top = Inches(0.38)
                    title_shape.width = Inches(10.4)
                    title_shape.height = Inches(0.75)
                except Exception:
                    pass
                for p in tf.paragraphs:
                    p.alignment = PP_ALIGN.LEFT
                    for r in p.runs:
                        cur_hex = None
                        if r.font and r.font.color and r.font.color.type == 1:
                            try:
                                cur_hex = str(r.font.color.rgb).upper()
                            except Exception:
                                pass
                        t_hex = HEX_WHITE if cur_hex in ("FFFFFF", "F2F6FC") else HEX_CORP_GOLD
                        t_rgb = RGB_WHITE if t_hex == HEX_WHITE else RGB_CORP_GOLD

                        r.font.name = "Times New Roman"
                        r.font.size = Pt(26)
                        r.font.bold = False
                        r.font.italic = False
                        r.font.color.rgb = t_rgb
                        self._inject_run_xml(r, "Times New Roman", t_hex)
                    self._inject_para_def_rpr(p, is_title=True, is_bright_bg=False)

        # ---------------------------------------------------------------------
        # RULE B: Image & Text Reflow (Never Overlap)
        # ---------------------------------------------------------------------
        pictures = []
        for s in slide.shapes:
            is_pic = False
            try:
                if s.shape_type == MSO_SHAPE_TYPE.PICTURE or hasattr(s, "image"):
                    if getattr(s, "image", None) is not None:
                        is_pic = True
            except Exception:
                pass
            if is_pic:
                pictures.append(s)

        content_text_shapes = [
            s for s in slide.shapes
            if s.has_text_frame
            and s != title_shape
            and s != subtitle_shape
            and not getattr(s, "name", "").startswith("BrandMorph")
        ]

        # Case B1: Team or Gallery Grid (Slide 7 archetype)
        if archetype == SlideArchetype.TEAM_OR_GALLERY_GRID and len(pictures) >= 3:
            num_pics = min(4, len(pictures))
            pictures.sort(key=lambda p: p.left.inches if hasattr(p, "left") and p.left else 0.0)
            col_width = 2.55
            gap = 0.50
            start_left = 0.85
            top_pos = 1.6

            for i in range(num_pics):
                pic = pictures[i]
                cur_left = start_left + i * (col_width + gap)
                try:
                    pic.left = Inches(cur_left)
                    pic.top = Inches(top_pos)
                    pic.width = Inches(col_width)
                    pic.height = Inches(col_width)
                except Exception:
                    pass

            # Align caption text boxes directly beneath corresponding photos
            content_text_shapes.sort(key=lambda s: s.left.inches if hasattr(s, "left") and s.left else 0.0)
            for i, ts in enumerate(content_text_shapes):
                col_idx = i % num_pics
                cur_left = start_left + col_idx * (col_width + gap)
                is_role = i >= num_pics
                t_top = 4.35 if not is_role else 4.75
                try:
                    ts.left = Inches(cur_left)
                    ts.top = Inches(t_top)
                    ts.width = Inches(col_width)
                    ts.height = Inches(0.35)
                except Exception:
                    pass

        # Case B2: Content slide with both text blocks AND 1-4 images (e.g. Slides 2, 3, 11)
        elif 1 <= len(pictures) <= 4 and content_text_shapes and archetype in (
            SlideArchetype.AGENDA_SLIDE,
            SlideArchetype.MULTI_CARD_CONTENT,
            SlideArchetype.SECTION_SPLITTER,
        ):
            # Arrange images into right-hand visual grid: left=7.1" to 12.68", top=1.35" to 6.65"
            grid_left = 7.1
            grid_top = 1.35
            grid_w = 5.5
            grid_h = 5.2

            num_pics = len(pictures)
            if num_pics == 1:
                try:
                    pictures[0].left = Inches(grid_left)
                    pictures[0].top = Inches(grid_top)
                    pictures[0].width = Inches(grid_w)
                    pictures[0].height = Inches(grid_h)
                except Exception:
                    pass
            elif num_pics == 2:
                half_h = 2.45
                gap_y = 0.3
                try:
                    pictures[0].left = Inches(grid_left)
                    pictures[0].top = Inches(grid_top)
                    pictures[0].width = Inches(grid_w)
                    pictures[0].height = Inches(half_h)

                    pictures[1].left = Inches(grid_left)
                    pictures[1].top = Inches(grid_top + half_h + gap_y)
                    pictures[1].width = Inches(grid_w)
                    pictures[1].height = Inches(half_h)
                except Exception:
                    pass
            else:
                half_w = 2.65
                half_h = 2.45
                gap = 0.2
                for p_idx, pic in enumerate(pictures[:4]):
                    row = p_idx // 2
                    col = p_idx % 2
                    try:
                        pic.left = Inches(grid_left + col * (half_w + gap))
                        pic.top = Inches(grid_top + row * (half_h + gap))
                        pic.width = Inches(half_w)
                        pic.height = Inches(half_h)
                    except Exception:
                        pass

            # Reflow text blocks into governed left-hand corporate cards: left=0.65" to 6.75"
            card_left = 0.65
            card_width = 6.1
            n_cards = len(content_text_shapes)
            avail_h = 5.2
            card_h = min(2.2, max(1.0, (avail_h - (n_cards - 1) * 0.25) / n_cards))

            for c_idx, ts in enumerate(content_text_shapes):
                c_top = grid_top + c_idx * (card_h + 0.25)
                try:
                    ts.left = Inches(card_left)
                    ts.top = Inches(c_top)
                    ts.width = Inches(card_width)
                    ts.height = Inches(card_h)
                except Exception:
                    pass

        # Case B3: Data Table Slide (or any slide containing a Table)
        table_shapes = [s for s in slide.shapes if getattr(s, "has_table", False) and s.has_table]
        for ts in table_shapes:
            try:
                # Table Bounding Box: Position cleanly below top-left title (left=0.80", top=1.65", width=11.73", height<=4.8" max)
                ts.left = Inches(0.80)
                ts.top = Inches(1.65)
                ts.width = Inches(11.73)
                current_h = ts.height.inches if ts.height else 4.0
                ts.height = Inches(min(4.8, max(2.5, current_h)))
            except Exception:
                pass
            self._style_table_corporate(ts.table)

        # Case B4: Multi-card content (zero pictures, 1-4 content cards)
        if archetype == SlideArchetype.MULTI_CARD_CONTENT and len(pictures) == 0 and 1 <= len(content_text_shapes) <= 4:
            k = len(content_text_shapes)
            # Golden Pair constants: 1 card = 11.73", 2 cards = 5.70" (gap 0.33"), 3 cards = 3.68" (gap 0.34"), 4 cards = 2.68" (gap 0.33")
            card_configs = {
                1: (11.73, 0.0),
                2: (5.70, 0.33),
                3: (3.68, 0.34),
                4: (2.68, 0.33),
            }
            card_w, gap = card_configs[k]
            start_left = 0.80
            top_pos = 1.65
            card_h = 4.80

            content_text_shapes.sort(key=lambda s: s.left.inches if hasattr(s, "left") and s.left else 0.0)
            for i, ts in enumerate(content_text_shapes):
                cur_left = start_left + i * (card_w + gap)
                try:
                    ts.left = Inches(cur_left)
                    ts.top = Inches(top_pos)
                    ts.width = Inches(card_w)
                    ts.height = Inches(card_h)
                    if hasattr(ts, "fill"):
                        ts.fill.solid()
                        ts.fill.fore_color.rgb = RGB_SURFACE_ALT
                except Exception:
                    pass

        # ---------------------------------------------------------------------
        # RULES C & D: Typography & Contrast Enforcement on All Shapes
        # ---------------------------------------------------------------------
        for shape in list(slide.shapes):
            if getattr(shape, "name", "") == "BrandMorph_Logo_Stamp":
                continue
            self._govern_shape_typography_and_contrast(
                shape, slide_idx, title_shape, subtitle_shape, archetype, default_bg=HEX_CANVAS_NAVY
            )

    def _style_table_corporate(self, table) -> None:
        """Enforce clean corporate Table styling per task specifications."""
        for r_idx, row in enumerate(table.rows):
            is_header = (r_idx == 0)
            row_fill_rgb = RGB_CORP_GOLD if is_header else (RGB_SURFACE_ALT if (r_idx % 2 == 1) else RGB_CANVAS_NAVY)
            row_fill_hex = HEX_CORP_GOLD if is_header else (HEX_SURFACE_ALT if (r_idx % 2 == 1) else HEX_CANVAS_NAVY)

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
                    # Header row: Arial 12pt Bold, Dark Navy #001F33
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
                    # Data row: First column is Bold Gold #FFB81C or White; other cells regular White 11pt
                    is_first_col = (c_idx == 0)
                    target_color_rgb = RGB_CORP_GOLD if is_first_col else RGB_WHITE
                    target_color_hex = HEX_CORP_GOLD if is_first_col else HEX_WHITE
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

    def _govern_shape_typography_and_contrast(
        self, shape, slide_idx: int, title_shape, subtitle_shape, archetype: SlideArchetype, default_bg: str
    ) -> None:
        """Walk shapes recursively, enforce Arial subheadings/body, and inject XML contrast."""
        if shape.shape_type == MSO_SHAPE_TYPE.GROUP:
            for child in shape.shapes:
                self._govern_shape_typography_and_contrast(
                    child, slide_idx, title_shape, subtitle_shape, archetype, default_bg
                )
            return

        if getattr(shape, "has_table", False) and shape.has_table:
            # Table cells are governed by _style_table_corporate; skip generic contrast loop to avoid overwriting header text
            return

        if shape.has_text_frame:
            shape_bg = self._get_shape_fill_hex(shape) or default_bg
            is_title = (shape == title_shape)
            is_sub = (shape == subtitle_shape)
            self._process_text_runs(
                shape.text_frame, shape, is_title=is_title, is_sub=is_sub, effective_bg=shape_bg
            )

    def _get_shape_fill_hex(self, shape) -> Optional[str]:
        try:
            if shape.fill and shape.fill.type == 1 and hasattr(shape.fill, "fore_color"):
                if hasattr(shape.fill.fore_color, "rgb"):
                    return f"{shape.fill.fore_color.rgb}".upper()
        except Exception:
            pass
        return None

    def _process_text_runs(
        self, text_frame, shape, is_title: bool, is_sub: bool, effective_bg: str
    ) -> None:
        bg_rgb = hex_to_rgb(effective_bg)
        bg_lum = relative_luminance(*bg_rgb)
        is_bright_bg = bg_lum > 0.35  # Cyan #00FFFF, Gold #FFB81C, White

        for p in text_frame.paragraphs:
            txt = p.text.strip()
            if not txt:
                continue

            if len(p.runs) == 0:
                p.add_run().text = txt

            # Determine subheading if not marked
            p_is_sub = is_sub
            if not is_title and not is_sub:
                pt_size = p.font.size.pt if p.font and p.font.size else 12.0
                if (13.0 <= pt_size <= 20.0 or (p.font and p.font.bold)) and len(txt) <= 75:
                    p_is_sub = True

            for run in p.runs:
                # -------------------------------------------------------------
                # 1. Typography
                # -------------------------------------------------------------
                if is_title:
                    target_font = "Times New Roman"
                    current_pt = run.font.size.pt if run.font and run.font.size else 26.0
                    target_pt = max(24.0, min(32.0, current_pt))
                    target_bold = False
                    target_italic = False
                elif p_is_sub:
                    target_font = "Arial"
                    current_pt = run.font.size.pt if run.font and run.font.size else 14.0
                    target_pt = max(12.0, min(16.0, current_pt))
                    target_bold = True
                    target_italic = False
                else:
                    target_font = "Arial"
                    current_pt = run.font.size.pt if run.font and run.font.size else 11.0
                    target_pt = max(8.0, current_pt)
                    target_bold = False
                    target_italic = False

                run.font.name = target_font
                run.font.size = Pt(target_pt)
                run.font.bold = target_bold
                run.font.italic = target_italic

                # -------------------------------------------------------------
                # 2. Contrast Resolver
                # -------------------------------------------------------------
                cur_hex = None
                if run.font.color and run.font.color.type == 1:
                    try:
                        cur_hex = str(run.font.color.rgb).upper()
                    except Exception:
                        pass

                if is_bright_bg:
                    # Bright shape background -> dark navy text
                    target_rgb = RGB_DARK_NAVY
                    target_hex = HEX_DARK_NAVY
                else:
                    # Dark background -> gold or white
                    if is_title:
                        if cur_hex in ("FFFFFF", "F2F6FC"):
                            target_rgb = RGB_WHITE
                            target_hex = HEX_WHITE
                        else:
                            target_rgb = RGB_CORP_GOLD
                            target_hex = HEX_CORP_GOLD
                    elif p_is_sub:
                        if cur_hex in (HEX_CORP_GOLD, HEX_CYAN, "FFFFFF"):
                            target_rgb = run.font.color.rgb
                            target_hex = cur_hex
                        else:
                            target_rgb = RGB_CORP_GOLD
                            target_hex = HEX_CORP_GOLD
                    else:
                        # Body text: white or readable muted
                        is_readable = False
                        if cur_hex:
                            try:
                                r_lum = relative_luminance(*hex_to_rgb(cur_hex))
                                if r_lum >= 0.15:
                                    is_readable = True
                            except Exception:
                                pass
                        if is_readable and cur_hex != "000000":
                            target_rgb = run.font.color.rgb
                            target_hex = cur_hex
                        else:
                            target_rgb = RGB_WHITE
                            target_hex = HEX_WHITE

                run.font.color.rgb = target_rgb
                self._inject_run_xml(run, target_font, target_hex)

            self._inject_para_def_rpr(p, is_title=is_title, is_bright_bg=is_bright_bg)

    def _inject_run_xml(self, run, font_family: str, color_hex: str) -> None:
        """Inject explicit DrawingML <a:solidFill> and typeface tags into run XML."""
        try:
            rPr = run._r.get_or_add_rPr()
            for child in list(rPr):
                tag = etree.QName(child).localname
                if tag in ("solidFill", "schemeClr", "noFill", "sysClr", "gradFill", "blipFill"):
                    rPr.remove(child)

            solidFill = etree.SubElement(rPr, f"{{{_A}}}solidFill")
            srgb = etree.SubElement(solidFill, f"{{{_A}}}srgbClr")
            srgb.set("val", color_hex)

            for tag in ("latin", "cs", "ea"):
                el = rPr.find(f"{{{_A}}}{tag}")
                if el is None:
                    el = etree.SubElement(rPr, f"{{{_A}}}{tag}")
                el.set("typeface", font_family)
        except Exception:
            pass

    def _inject_para_def_rpr(self, para, is_title: bool, is_bright_bg: bool) -> None:
        """Inject fallback paragraph default run properties."""
        try:
            pPr = para._p.get_or_add_pPr()
            defRPr = pPr.find(f"{{{_A}}}defRPr")
            if defRPr is None:
                defRPr = etree.SubElement(pPr, f"{{{_A}}}defRPr")

            for child in list(defRPr):
                tag = etree.QName(child).localname
                if tag in ("solidFill", "schemeClr", "noFill", "sysClr"):
                    defRPr.remove(child)

            solidFill = etree.SubElement(defRPr, f"{{{_A}}}solidFill")
            srgb = etree.SubElement(solidFill, f"{{{_A}}}srgbClr")
            color_hex = HEX_DARK_NAVY if is_bright_bg else (HEX_CORP_GOLD if is_title else HEX_WHITE)
            srgb.set("val", color_hex)

            family = "Times New Roman" if is_title else "Arial"
            for tag in ("latin", "cs", "ea"):
                el = defRPr.find(f"{{{_A}}}{tag}")
                if el is None:
                    el = etree.SubElement(defRPr, f"{{{_A}}}{tag}")
                el.set("typeface", family)
        except Exception:
            pass
