import base64
import io
import pptx
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN
from pptx.oxml.ns import qn

def hex_to_rgb(hex_str: str) -> RGBColor:
    s = hex_str.lstrip("#")
    if len(s) == 6:
        return RGBColor(int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16))
    return RGBColor(255, 255, 255)

def rgb_luminance(rgb: RGBColor) -> float:
    r, g, b = rgb[0] / 255.0, rgb[1] / 255.0, rgb[2] / 255.0
    return 0.299 * r + 0.587 * g + 0.114 * b

def force_run_xml_color(run, rgb: RGBColor):
    """Explicitly write <a:solidFill><a:srgbClr val="..."/></a:solidFill> to ensure zero black text inheritance."""
    rPr = run._r.get_or_add_rPr()
    for tag in ("a:solidFill", "a:gradFill", "a:pattFill", "a:blipFill", "a:noFill", "a:grpFill"):
        for el in rPr.findall(qn(tag)):
            rPr.remove(el)
    solid_fill = rPr.makeelement(qn("a:solidFill"), {})
    srgb = solid_fill.makeelement(qn("a:srgbClr"), {"val": str(rgb)})
    solid_fill.append(srgb)
    rPr.insert(0, solid_fill)

class BrandTokens:
    BG_DARK = RGBColor(0, 31, 51)          # #001F33 Deep Navy
    BG_LEGACY = RGBColor(3, 12, 30)        # #030C1E
    CARD_BG = RGBColor(8, 30, 54)          # #081E36 Card Surface Slate
    CARD_ALT = RGBColor(10, 42, 74)        # #0A2A4A Card Surface Alt
    CYAN = RGBColor(0, 255, 255)           # #00FFFF Aqua / Cyan telemetry
    CYAN_ALT = RGBColor(7, 255, 255)       # #07FFFF
    GOLD = RGBColor(255, 184, 28)          # #FFB81C Corporate Gold
    TEXT_WHITE = RGBColor(255, 255, 255)   # #FFFFFF
    TEXT_DARK = RGBColor(0, 31, 51)        # #001F33 Text for bright badge containers

    FONT_TITLE = "Times New Roman"
    FONT_BODY = "Arial"
    FONT_HEADING = "Roboto"

class NativePPTXBuilder:
    def __init__(self):
        self.prs = pptx.Presentation()
        self.prs.slide_width = Inches(13.333)
        self.prs.slide_height = Inches(7.5)

    def _resolve_contrast_color(self, container_fill_rgb: RGBColor | None, is_title: bool, is_subheading: bool) -> RGBColor:
        """Background-Aware Contrast Resolver (Issues #7, #8, #9)."""
        if container_fill_rgb is not None:
            lum = rgb_luminance(container_fill_rgb)
            # High-luminance background (Gold, Cyan, bright yellow)
            if lum >= 0.55:
                return BrandTokens.TEXT_DARK
            # Dark background
            return BrandTokens.GOLD if is_title else BrandTokens.TEXT_WHITE

        # Default dark slide background (#001F33)
        if is_title:
            return BrandTokens.GOLD
        if is_subheading:
            return BrandTokens.TEXT_WHITE
        return BrandTokens.TEXT_WHITE

    def add_top_right_logo_stamp(self, slide):
        """Top-Right Akkodis Corporate Logo Stamp (Issue #4)."""
        left = Inches(11.4)
        top = Inches(0.35)
        width = Inches(1.5)
        height = Inches(0.45)

        stamp_box = slide.shapes.add_textbox(left, top, width, height)
        tf = stamp_box.text_frame
        tf.word_wrap = False
        tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
        p = tf.paragraphs[0]
        p.alignment = PP_ALIGN.RIGHT
        run = p.add_run()
        run.text = "AKKODIS"
        run.font.name = "Arial"
        run.font.size = Pt(13)
        run.font.bold = True
        run.font.color.rgb = BrandTokens.GOLD
        force_run_xml_color(run, BrandTokens.GOLD)

    def build_slide(self, slide_ast: dict) -> pptx.slide.Slide:
        blank_slide_layout = self.prs.slide_layouts[6]
        slide = self.prs.slides.add_slide(blank_slide_layout)

        # 1. Apply Structured Dark Corporate Background (#001F33)
        background = slide.background
        fill = background.fill
        fill.solid()
        fill.fore_color.rgb = BrandTokens.BG_DARK

        # Optional accent framing line across top
        accent_bar = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE,
            Inches(0), Inches(0), Inches(13.333), Inches(0.04)
        )
        accent_bar.fill.solid()
        accent_bar.fill.fore_color.rgb = BrandTokens.GOLD
        accent_bar.line.fill.background()

        # 2. Add Top-Right Logo Stamp
        self.add_top_right_logo_stamp(slide)

        # 3. Render Nodes at exact Spatial Coordinates
        nodes = slide_ast.get("nodes", [])

        # Render Images / Pictures first (z-order: beneath text elements)
        for node in nodes:
            node_type = node.get("type")
            bbox = node.get("bbox", {"left": 1.0, "top": 1.0, "width": 4.0, "height": 2.0})

            if node_type in ("PICTURE", "IMAGE"):
                data_uri = node.get("image_data_uri") or node.get("image_data")
                if data_uri and "base64," in data_uri:
                    try:
                        raw_b64 = data_uri.split("base64,")[1]
                        img_bytes = base64.b64decode(raw_b64)
                        slide.shapes.add_picture(
                            io.BytesIO(img_bytes),
                            Inches(bbox["left"]), Inches(bbox["top"]),
                            Inches(bbox["width"]), Inches(bbox["height"])
                        )
                    except Exception:
                        pass

        # Render Shape Containers (Cards, Ovals, Arrows)
        for node in nodes:
            node_type = node.get("type")
            bbox = node.get("bbox", {"left": 1.0, "top": 1.0, "width": 4.0, "height": 2.0})

            if node_type in ("RECTANGLE_SHAPE", "CONTAINER_SHAPE"):
                card = slide.shapes.add_shape(
                    MSO_SHAPE.ROUNDED_RECTANGLE,
                    Inches(bbox["left"]), Inches(bbox["top"]),
                    Inches(bbox["width"]), Inches(bbox["height"])
                )
                card.fill.solid()
                card.fill.fore_color.rgb = BrandTokens.CARD_BG
                card.line.color.rgb = BrandTokens.CYAN
                card.line.width = Pt(1.5)
                if hasattr(card, 'adjustments') and len(card.adjustments) > 0:
                    card.adjustments[0] = 0.04

            elif node_type == "OVAL_SHAPE":
                oval = slide.shapes.add_shape(
                    MSO_SHAPE.OVAL,
                    Inches(bbox["left"]), Inches(bbox["top"]),
                    Inches(bbox["width"]), Inches(bbox["height"])
                )
                oval.fill.solid()
                oval.fill.fore_color.rgb = BrandTokens.CARD_BG
                oval.line.color.rgb = BrandTokens.CYAN

            elif node_type == "ARROW_SHAPE":
                arrow = slide.shapes.add_shape(
                    MSO_SHAPE.RIGHT_ARROW,
                    Inches(bbox["left"]), Inches(bbox["top"]),
                    Inches(bbox["width"]), Inches(bbox["height"])
                )
                arrow.fill.solid()
                arrow.fill.fore_color.rgb = BrandTokens.GOLD
                arrow.line.color.rgb = BrandTokens.GOLD

        # Render Text Containers (Typography & Contrast Resolution)
        for node in nodes:
            node_type = node.get("type")
            if node_type != "TEXT_CONTAINER":
                continue

            bbox = node.get("bbox", {"left": 1.0, "top": 1.0, "width": 4.0, "height": 2.0})
            txBox = slide.shapes.add_textbox(
                Inches(bbox["left"]), Inches(bbox["top"]),
                Inches(bbox["width"]), Inches(bbox["height"])
            )
            tf = txBox.text_frame
            tf.word_wrap = True

            container_fill = None
            if node.get("fill_hex"):
                container_fill = hex_to_rgb(node["fill_hex"])

            is_title_candidate = node.get("is_title", False) or (bbox["top"] < 1.6 and bbox["height"] < 1.6)

            paragraphs = node.get("paragraphs", [])
            for i, para_data in enumerate(paragraphs):
                txt = para_data.get("text", "").strip()
                if not txt:
                    continue

                p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
                p.text = txt
                p.level = para_data.get("level", 0)

                align_str = para_data.get("align", "LEFT")
                if align_str == "CENTER":
                    p.alignment = PP_ALIGN.CENTER
                elif align_str == "RIGHT":
                    p.alignment = PP_ALIGN.RIGHT
                elif align_str == "JUSTIFY":
                    p.alignment = PP_ALIGN.JUSTIFY
                else:
                    p.alignment = PP_ALIGN.LEFT

                # Classify role
                raw_size = para_data.get("font_size") or 12
                is_title = is_title_candidate and (i == 0 or raw_size >= 20)
                is_subheading = not is_title and (para_data.get("bold") or (14 <= raw_size < 20))

                resolved_color = self._resolve_contrast_color(container_fill, is_title, is_subheading)

                if is_title:
                    # Title Rules: Times New Roman, 24pt-32pt clamp, NOT Bold, NOT Italic, Gold or White
                    p.font.name = BrandTokens.FONT_TITLE
                    clamped_size = 30.0 if raw_size > 32 else (24.0 if raw_size < 24 else raw_size)
                    p.font.size = Pt(clamped_size)
                    p.font.bold = False
                    p.font.italic = False
                    p.font.color.rgb = resolved_color
                elif is_subheading:
                    # Subheading Rules: Roboto/Arial, 11pt-16pt, Can be Bold, NO Italic
                    p.font.name = BrandTokens.FONT_HEADING
                    clamped_sub = max(11.0, min(16.0, float(raw_size)))
                    p.font.size = Pt(clamped_sub)
                    p.font.bold = True
                    p.font.italic = False
                    p.font.color.rgb = resolved_color
                else:
                    # Body Rules: Roboto/Arial, >= 8pt, NO Bold, NO Italic
                    p.font.name = BrandTokens.FONT_BODY
                    clamped_body = max(8.0, float(raw_size))
                    p.font.size = Pt(clamped_body)
                    p.font.bold = False
                    p.font.italic = False
                    p.font.color.rgb = resolved_color

                # Apply XML run level color and font to eradicate master black text
                for r in p.runs:
                    r.font.name = p.font.name
                    r.font.size = p.font.size
                    r.font.bold = p.font.bold
                    r.font.italic = p.font.italic
                    r.font.color.rgb = resolved_color
                    force_run_xml_color(r, resolved_color)

        return slide

    def save(self, output_path: str):
        self.prs.save(output_path)
