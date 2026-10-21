"""Generate visually rich default 12-slide sample presentation.

Mirrors the authentic visual template structure:
  - Pastel layout decorative blocks in Raw mode
  - Circular image crop masks (<a:prstGeom prst="ellipse">) on:
      * Slide 4 (Section Splitter)
      * Slide 7 (4 Team Headshots)
      * Slide 11 (3 Summary Photos)
  - Data Table on Slide 5
  - Quote on Slide 6
  - Process Timeline on Slide 8
  - 3-Column and 2-Column Content on Slides 9 & 10
  - Closing Slide on Slide 12
  - "PRESENTATION TITLE" and slide number footers on Slides 2..12
"""

from __future__ import annotations

import copy
import io
from pathlib import Path
from PIL import Image, ImageDraw

import pptx
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE


def make_sample_image(width: int = 400, height: int = 400, color_a=(65, 117, 164), color_b=(240, 160, 120)) -> bytes:
    """Generate a clean visual gradient/pattern image as PNG bytes."""
    im = Image.new("RGB", (width, height), color=color_a)
    draw = ImageDraw.Draw(im)
    # Draw radial gradient or circles
    for r in range(min(width, height) // 2, 0, -12):
        ratio = r / (min(width, height) / 2)
        cr = int(color_a[0] * ratio + color_b[0] * (1 - ratio))
        cg = int(color_a[1] * ratio + color_b[1] * (1 - ratio))
        cb = int(color_a[2] * ratio + color_b[2] * (1 - ratio))
        draw.ellipse([width // 2 - r, height // 2 - r, width // 2 + r, height // 2 + r], fill=(cr, cg, cb))
    buf = io.BytesIO()
    im.save(buf, format="PNG")
    return buf.getvalue()


def set_shape_ellipse_mask(shape) -> None:
    """Set OpenXML prstGeom to ellipse on a picture or shape."""
    if hasattr(shape, "_element"):
        for elem in shape._element.xpath('.//*[local-name()="prstGeom"]'):
            elem.set("prst", "ellipse")


def add_footer_and_slidenum(slide, slide_num: int) -> None:
    """Add standard corporate footer and slide number."""
    # Footer text
    ft = slide.shapes.add_textbox(Inches(0.8), Inches(7.0), Inches(4.5), Inches(0.35))
    p = ft.text_frame.paragraphs[0]
    p.text = "PRESENTATION TITLE"
    p.font.size = Pt(8.5)
    p.font.name = "Calibri"
    p.font.color.rgb = RGBColor(140, 150, 160)

    # Slide number
    sn = slide.shapes.add_textbox(Inches(12.0), Inches(7.0), Inches(0.6), Inches(0.35))
    p2 = sn.text_frame.paragraphs[0]
    p2.text = str(slide_num)
    p2.font.size = Pt(8.5)
    p2.font.name = "Calibri"
    p2.font.color.rgb = RGBColor(140, 150, 160)


def build_rich_sample_deck(output_path: Path) -> Path:
    prs = pptx.Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    layout = prs.slide_layouts[6]  # Blank layout

    # Add a pastel background block to the layout so raw mode detects layout background shape
    temp_slide = prs.slides.add_slide(layout)
    dummy_bg = temp_slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(3.6), Inches(7.5))
    dummy_bg.fill.solid()
    dummy_bg.fill.fore_color.rgb = RGBColor(246, 243, 237)  # Warm soft cream
    dummy_bg.line.fill.background()
    layout_sp = copy.deepcopy(dummy_bg._element)
    layout.shapes._spTree.append(layout_sp)

    # Remove temporary slide
    rId = prs.slides._sldIdLst[0].rId
    prs.part.drop_rel(rId)
    del prs.slides._sldIdLst[0]

    # Sample images
    img_avatar1 = make_sample_image(400, 400, (40, 80, 140), (255, 200, 120))
    img_avatar2 = make_sample_image(400, 400, (50, 130, 120), (240, 160, 160))
    img_avatar3 = make_sample_image(400, 400, (120, 70, 150), (255, 220, 150))
    img_avatar4 = make_sample_image(400, 400, (180, 90, 70), (230, 200, 140))
    img_hero = make_sample_image(500, 500, (30, 60, 120), (255, 184, 28))

    # =========================================================================
    # SLIDE 1: COVER_SLIDE (Title, Subtitle, Date)
    # =========================================================================
    s1 = prs.slides.add_slide(layout)
    # Pastel decorative banner
    banner1 = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(1.8), Inches(11.7), Inches(0.08))
    banner1.fill.solid()
    banner1.fill.fore_color.rgb = RGBColor(255, 184, 28)
    banner1.line.fill.background()

    t1 = s1.shapes.add_textbox(Inches(0.8), Inches(2.3), Inches(10.5), Inches(1.6))
    p1 = t1.text_frame.paragraphs[0]
    p1.text = "Strategic Corporate Overview"
    p1.font.size = Pt(36)
    p1.font.name = "Times New Roman"
    p1.font.bold = False
    p1.font.color.rgb = RGBColor(24, 24, 27)

    sub1 = s1.shapes.add_textbox(Inches(0.8), Inches(4.2), Inches(8.5), Inches(0.8))
    p_sub1 = sub1.text_frame.paragraphs[0]
    p_sub1.text = "Prepared for Executive Leadership & Board of Directors"
    p_sub1.font.size = Pt(16)
    p_sub1.font.name = "Calibri"
    p_sub1.font.color.rgb = RGBColor(100, 116, 139)

    # =========================================================================
    # SLIDE 2: AGENDA_SLIDE (Table of Contents + 2 Side Photos)
    # =========================================================================
    s2 = prs.slides.add_slide(layout)
    t2 = s2.shapes.add_textbox(Inches(0.8), Inches(0.6), Inches(7.0), Inches(0.8))
    t2.text_frame.paragraphs[0].text = "Executive Agenda"
    t2.text_frame.paragraphs[0].font.size = Pt(28)
    t2.text_frame.paragraphs[0].font.name = "Times New Roman"

    agenda_items = [
        "01. Corporate Mission & Strategic Horizon",
        "02. Operational Architecture & Cloud Scale",
        "03. Global Financial & Unit Economics",
        "04. Risk Governance & Execution Roadmap",
    ]
    for i, item in enumerate(agenda_items):
        box = s2.shapes.add_textbox(Inches(0.8), Inches(1.8 + i * 1.15), Inches(5.8), Inches(0.8))
        p = box.text_frame.paragraphs[0]
        p.text = item
        p.font.size = Pt(14)
        p.font.bold = True
        p.font.name = "Calibri"

    s2.shapes.add_picture(io.BytesIO(img_avatar1), Inches(7.2), Inches(1.8), Inches(4.8), Inches(2.2))
    s2.shapes.add_picture(io.BytesIO(img_avatar2), Inches(7.2), Inches(4.3), Inches(4.8), Inches(2.2))
    add_footer_and_slidenum(s2, 2)

    # =========================================================================
    # SLIDE 3: MULTI_CARD_CONTENT (3 Subtitle + Body Pillars + Photo)
    # =========================================================================
    s3 = prs.slides.add_slide(layout)
    t3 = s3.shapes.add_textbox(Inches(0.8), Inches(0.6), Inches(7.5), Inches(0.8))
    t3.text_frame.paragraphs[0].text = "Market Growth Opportunities"
    t3.text_frame.paragraphs[0].font.size = Pt(28)

    pillars = [
        ("Pillar 01: Intelligent Pipeline", "Automated slide governance guaranteeing brand consistency across all global teams."),
        ("Pillar 02: Neural Alignment", "Real-time layout classification with sub-millisecond inference and spatial consensus."),
        ("Pillar 03: Scalable Operations", "Enterprise-grade OpenXML decompilation with full fidelity asset preservation."),
    ]
    for i, (head, body) in enumerate(pillars):
        box = s3.shapes.add_textbox(Inches(0.8), Inches(1.8 + i * 1.6), Inches(5.8), Inches(1.3))
        p_head = box.text_frame.paragraphs[0]
        p_head.text = head
        p_head.font.size = Pt(13)
        p_head.font.bold = True
        p_body = box.text_frame.add_paragraph()
        p_body.text = body
        p_body.font.size = Pt(11)

    s3.shapes.add_picture(io.BytesIO(img_avatar3), Inches(7.2), Inches(1.8), Inches(4.8), Inches(4.6))
    add_footer_and_slidenum(s3, 3)

    # =========================================================================
    # SLIDE 4: SECTION_SPLITTER (Circular Photo prst="ellipse")
    # =========================================================================
    s4 = prs.slides.add_slide(layout)
    t4 = s4.shapes.add_textbox(Inches(0.8), Inches(2.3), Inches(5.8), Inches(1.2))
    p4 = t4.text_frame.paragraphs[0]
    p4.text = "Topic One"
    p4.font.size = Pt(36)
    p4.font.name = "Times New Roman"

    sub4 = s4.shapes.add_textbox(Inches(0.8), Inches(3.6), Inches(5.8), Inches(1.2))
    p_sub4 = sub4.text_frame.paragraphs[0]
    p_sub4.text = "Engineering Architecture & Scalable Infrastructure"
    p_sub4.font.size = Pt(16)
    p_sub4.font.color.rgb = RGBColor(100, 116, 139)

    pic4 = s4.shapes.add_picture(io.BytesIO(img_hero), Inches(7.2), Inches(1.6), Inches(4.6), Inches(4.6))
    set_shape_ellipse_mask(pic4)
    add_footer_and_slidenum(s4, 4)

    # =========================================================================
    # SLIDE 5: DATA_TABLE_SLIDE (Financial Performance Metrics Table)
    # =========================================================================
    s5 = prs.slides.add_slide(layout)
    t5 = s5.shapes.add_textbox(Inches(0.8), Inches(0.6), Inches(8.0), Inches(0.8))
    t5.text_frame.paragraphs[0].text = "Financial Performance Metrics"
    t5.text_frame.paragraphs[0].font.size = Pt(28)

    table_shape = s5.shapes.add_table(4, 3, Inches(0.8), Inches(1.8), Inches(11.2), Inches(4.4))
    headers = ["Metric", "FY24 Actual", "FY25 Plan"]
    for c_idx, h in enumerate(headers):
        cell = table_shape.table.cell(0, c_idx)
        cell.text = h
        cell.fill.solid()
        cell.fill.fore_color.rgb = RGBColor(255, 184, 28)
        p = cell.text_frame.paragraphs[0]
        p.font.bold = True
        p.font.color.rgb = RGBColor(0, 31, 51)
        p.font.size = Pt(12)

    rows_data = [
        ["Total Revenue ($M)", "$124.5", "$168.0"],
        ["Gross Margin (%)", "74.2%", "78.5%"],
        ["Customer Retention (%)", "96.5%", "98.5%"],
    ]
    for r_idx, r_data in enumerate(rows_data):
        for c_idx, val in enumerate(r_data):
            cell = table_shape.table.cell(r_idx + 1, c_idx)
            cell.text = val
            p = cell.text_frame.paragraphs[0]
            p.font.size = Pt(11)
            p.font.color.rgb = RGBColor(24, 24, 27)

    add_footer_and_slidenum(s5, 5)

    # =========================================================================
    # SLIDE 6: QUOTE_SLIDE (Client Testimonial + Author Attribution)
    # =========================================================================
    s6 = prs.slides.add_slide(layout)
    q6 = s6.shapes.add_textbox(Inches(1.5), Inches(2.5), Inches(10.0), Inches(1.8))
    pq6 = q6.text_frame.paragraphs[0]
    pq6.text = '"BrandMorph transformed our enterprise presentation workflow into an automated, brand-governed content supply chain."'
    pq6.font.size = Pt(22)
    pq6.font.name = "Times New Roman"
    pq6.font.italic = True
    pq6.font.color.rgb = RGBColor(24, 24, 27)

    sub6 = s6.shapes.add_textbox(Inches(1.5), Inches(4.5), Inches(10.0), Inches(0.8))
    psub6 = sub6.text_frame.paragraphs[0]
    psub6.text = "— Chief Technology Officer, Fortune 500 Enterprise"
    psub6.font.size = Pt(14)
    psub6.font.bold = True
    psub6.font.color.rgb = RGBColor(100, 116, 139)

    add_footer_and_slidenum(s6, 6)

    # =========================================================================
    # SLIDE 7: TEAM_OR_GALLERY_GRID (4 Circular Headshots prst="ellipse")
    # =========================================================================
    s7 = prs.slides.add_slide(layout)
    t7 = s7.shapes.add_textbox(Inches(0.8), Inches(0.6), Inches(8.0), Inches(0.8))
    t7.text_frame.paragraphs[0].text = "Executive Leadership Team"
    t7.text_frame.paragraphs[0].font.size = Pt(28)

    team_members = [
        ("Alex Rivera", "Chief Executive Officer", img_avatar1),
        ("Sarah Chen", "VP Engineering", img_avatar2),
        ("Marcus Vance", "Chief Product Officer", img_avatar3),
        ("Elena Rostova", "Head of Design", img_avatar4),
    ]
    for i, (name, role, img_bytes) in enumerate(team_members):
        x = 0.8 + i * 2.95
        pic = s7.shapes.add_picture(io.BytesIO(img_bytes), Inches(x), Inches(1.8), Inches(2.4), Inches(2.4))
        set_shape_ellipse_mask(pic)

        n_box = s7.shapes.add_textbox(Inches(x), Inches(4.4), Inches(2.4), Inches(0.4))
        pn = n_box.text_frame.paragraphs[0]
        pn.text = name
        pn.font.size = Pt(13)
        pn.font.bold = True

        r_box = s7.shapes.add_textbox(Inches(x), Inches(4.8), Inches(2.4), Inches(0.4))
        pr = r_box.text_frame.paragraphs[0]
        pr.text = role
        pr.font.size = Pt(10)
        pr.font.color.rgb = RGBColor(100, 116, 139)

    add_footer_and_slidenum(s7, 7)

    # =========================================================================
    # SLIDE 8: PROCESS_TIMELINE (4 Horizontal Milestone Cards)
    # =========================================================================
    s8 = prs.slides.add_slide(layout)
    t8 = s8.shapes.add_textbox(Inches(0.8), Inches(0.6), Inches(8.0), Inches(0.8))
    t8.text_frame.paragraphs[0].text = "Product Delivery Timeline"
    t8.text_frame.paragraphs[0].font.size = Pt(28)

    quarters = [
        ("Q1: Discovery", "Decompile existing slide library, extract AST graph, normalize tokens."),
        ("Q2: Architecture", "Deploy SlideGNN neural model and WCAG 2.1 color contrast solver."),
        ("Q3: Deployment", "Ship high-craft React & Tauri client with before/after visual inspection."),
        ("Q4: Scale", "Full enterprise automated deck migration across Fortune 500 tenants."),
    ]
    for i, (q_title, q_desc) in enumerate(quarters):
        x = 0.8 + i * 2.95
        card = s8.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(2.0), Inches(2.7), Inches(4.2))
        card.fill.solid()
        card.fill.fore_color.rgb = RGBColor(241, 245, 249) if i != 1 else RGBColor(254, 243, 199)
        card.line.color.rgb = RGBColor(226, 232, 240)

        p = card.text_frame.paragraphs[0]
        p.text = q_title
        p.font.size = Pt(13)
        p.font.bold = True
        p.font.color.rgb = RGBColor(24, 24, 27)

        p2 = card.text_frame.add_paragraph()
        p2.text = q_desc
        p2.font.size = Pt(10)
        p2.font.color.rgb = RGBColor(71, 85, 105)

    add_footer_and_slidenum(s8, 8)

    # =========================================================================
    # SLIDE 9: MULTI_CARD_CONTENT (3 Columns Subtitle + Body)
    # =========================================================================
    s9 = prs.slides.add_slide(layout)
    t9 = s9.shapes.add_textbox(Inches(0.8), Inches(0.6), Inches(8.0), Inches(0.8))
    t9.text_frame.paragraphs[0].text = "Key Transformation Pillars"
    t9.text_frame.paragraphs[0].font.size = Pt(28)

    cards9 = [
        ("Automated Compliance", "Continuous auditing of brand guidelines, font normalization, and OpenXML coordinate hygiene."),
        ("Deterministic Layout", "Top-left snapping, clean whitespace preservation, and zero destructive coordinate overwrites."),
        ("Universal Export", "One-click PPTX builder producing pristine binary presentations ready for executive boardroom display."),
    ]
    for i, (title, desc) in enumerate(cards9):
        x = 0.8 + i * 3.95
        box = s9.shapes.add_textbox(Inches(x), Inches(2.0), Inches(3.6), Inches(4.2))
        p = box.text_frame.paragraphs[0]
        p.text = title
        p.font.size = Pt(14)
        p.font.bold = True
        p2 = box.text_frame.add_paragraph()
        p2.text = desc
        p2.font.size = Pt(11)

    add_footer_and_slidenum(s9, 9)

    # =========================================================================
    # SLIDE 10: MULTI_CARD_CONTENT (2 Wide Columns Subtitle + Body)
    # =========================================================================
    s10 = prs.slides.add_slide(layout)
    t10 = s10.shapes.add_textbox(Inches(0.8), Inches(0.6), Inches(8.0), Inches(0.8))
    t10.text_frame.paragraphs[0].text = "Global Infrastructure & Scale"
    t10.text_frame.paragraphs[0].font.size = Pt(28)

    cards10 = [
        ("North America & EMEA Region", "Multi-region edge deployment with sub-10ms response times and automated load balancing."),
        ("Asia-Pacific & LATAM Region", "Strict localized compliance, multi-lingual font fallback resolution, and isolated tenant storage."),
    ]
    for i, (title, desc) in enumerate(cards10):
        x = 0.8 + i * 5.95
        box = s10.shapes.add_textbox(Inches(x), Inches(2.0), Inches(5.5), Inches(4.2))
        p = box.text_frame.paragraphs[0]
        p.text = title
        p.font.size = Pt(15)
        p.font.bold = True
        p2 = box.text_frame.add_paragraph()
        p2.text = desc
        p2.font.size = Pt(11.5)

    add_footer_and_slidenum(s10, 10)

    # =========================================================================
    # SLIDE 11: MULTI_CARD_CONTENT / GALLERY (3 Circular Summary Photos)
    # =========================================================================
    s11 = prs.slides.add_slide(layout)
    t11 = s11.shapes.add_textbox(Inches(0.8), Inches(0.6), Inches(8.0), Inches(0.8))
    t11.text_frame.paragraphs[0].text = "Executive Summary & Milestones"
    t11.text_frame.paragraphs[0].font.size = Pt(28)

    gallery_items = [
        ("Phase 1: Ingestion", img_avatar1),
        ("Phase 2: Alignment", img_avatar2),
        ("Phase 3: Generation", img_avatar3),
    ]
    for i, (cap, img_bytes) in enumerate(gallery_items):
        x = 0.8 + i * 3.95
        pic = s11.shapes.add_picture(io.BytesIO(img_bytes), Inches(x + 0.6), Inches(2.0), Inches(2.5), Inches(2.5))
        set_shape_ellipse_mask(pic)

        tb = s11.shapes.add_textbox(Inches(x), Inches(4.8), Inches(3.7), Inches(1.5))
        p = tb.text_frame.paragraphs[0]
        p.text = cap
        p.font.size = Pt(13)
        p.font.bold = True
        p.alignment = pptx.enum.text.PP_ALIGN.CENTER

    add_footer_and_slidenum(s11, 11)

    # =========================================================================
    # SLIDE 12: CLOSING_SLIDE (Thank You, Contact Details)
    # =========================================================================
    s12 = prs.slides.add_slide(layout)
    t12 = s12.shapes.add_textbox(Inches(0.8), Inches(2.2), Inches(6.0), Inches(1.2))
    p12 = t12.text_frame.paragraphs[0]
    p12.text = "Thank You"
    p12.font.size = Pt(36)
    p12.font.name = "Times New Roman"

    c12 = s12.shapes.add_textbox(Inches(0.8), Inches(3.6), Inches(6.0), Inches(1.5))
    p_c12 = c12.text_frame.paragraphs[0]
    p_c12.text = "Website: https://brandmorph-tau.vercel.app\nInquiries: team@brandmorph.com\nHeadquarters: San Francisco, CA"
    p_c12.font.size = Pt(13)
    p_c12.font.color.rgb = RGBColor(100, 116, 139)

    pic12 = s12.shapes.add_picture(io.BytesIO(img_avatar4), Inches(7.5), Inches(1.8), Inches(4.8), Inches(4.2))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(output_path))
    return output_path


if __name__ == "__main__":
    out = Path("backend/samples/sample_12slide_archetypes.pptx")
    build_rich_sample_deck(out)
    print(f"Generated rich 12-slide sample presentation at: {out}")
