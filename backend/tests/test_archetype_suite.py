"""12-Slide Archetype Test Suite.

Verifies end-to-end all 8 slide archetypes:
1. Slide 1 (COVER_SLIDE) has Times New Roman, bold == False, 24-32pt.
2. Content slides have titles snapped to top-left (left == 0.65", top == 0.38").
3. Zero duplicate "BrandMorph" stamps exist.
4. All images appear in the JSON AST with image_data_uri and do not overlap repositioned text cards.
5. Every text run has an explicit RGB color with WCAG contrast >= 4.5:1 against its background.
"""

import base64
import io
import math
from pathlib import Path
import pytest
import pptx
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE, MSO_SHAPE_TYPE, PP_PLACEHOLDER
from pptx.enum.text import PP_ALIGN

from brandmorph.brand.profile import BrandDNA
from brandmorph.engine.archetype_engine import (
    ArchetypeEngine,
    SlideArchetype,
    SlideGraphClassifier,
    relative_luminance,
    hex_to_rgb,
)
from brandmorph.engine.pipeline import MorphPipeline, MorphOptions
from decompiler import SlideDecompiler


def _tiny_png_bytes() -> bytes:
    """1x1 transparent PNG bytes for testing."""
    return base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
    )


def generate_12_slide_presentation(path: Path) -> Path:
    """Generate a canonical 12-slide test deck covering all 8 corporate archetypes."""
    prs = pptx.Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]
    img_data = _tiny_png_bytes()

    # SLIDE 1: COVER_SLIDE (Index 0, large title + presenter subtitle)
    s1 = prs.slides.add_slide(blank_layout)
    t1 = s1.shapes.add_textbox(Inches(1.0), Inches(2.0), Inches(10.0), Inches(1.5))
    p1 = t1.text_frame.paragraphs[0]
    p1.text = "Strategic Corporate Overview"
    p1.font.size = Pt(36)
    p1.font.bold = True
    sub1 = s1.shapes.add_textbox(Inches(1.0), Inches(3.8), Inches(10.0), Inches(0.8))
    sub1.text_frame.paragraphs[0].text = "Prepared by Leadership Team"

    # SLIDE 2: AGENDA_SLIDE ("Agenda", 4 topic items + 2 side images)
    s2 = prs.slides.add_slide(blank_layout)
    t2 = s2.shapes.add_textbox(Inches(0.5), Inches(0.5), Inches(8.0), Inches(0.8))
    t2.text_frame.paragraphs[0].text = "Executive Agenda"
    for i in range(4):
        card = s2.shapes.add_textbox(Inches(1.0), Inches(1.5 + i * 1.2), Inches(5.0), Inches(0.8))
        card.text_frame.paragraphs[0].text = f"Agenda Item {i+1}: Global Strategy and Execution"
    s2.shapes.add_picture(io.BytesIO(img_data), Inches(7.5), Inches(1.5), Inches(4.5), Inches(2.0))
    s2.shapes.add_picture(io.BytesIO(img_data), Inches(7.5), Inches(4.0), Inches(4.5), Inches(2.0))

    # SLIDE 3: MULTI_CARD_CONTENT (3 subheading + body blocks + 1 image)
    s3 = prs.slides.add_slide(blank_layout)
    t3 = s3.shapes.add_textbox(Inches(0.8), Inches(0.6), Inches(7.0), Inches(0.8))
    t3.text_frame.paragraphs[0].text = "Market Growth Opportunities"
    for i in range(3):
        box = s3.shapes.add_textbox(Inches(0.8), Inches(1.6 + i * 1.6), Inches(5.5), Inches(1.2))
        p = box.text_frame.paragraphs[0]
        p.text = f"Pillar {i+1}: Accelerated Delivery"
        p.font.bold = True
        p2 = box.text_frame.add_paragraph()
        p2.text = "Expanding cloud adoption and cross-functional operations with measurable outcomes."
    s3.shapes.add_picture(io.BytesIO(img_data), Inches(7.2), Inches(1.6), Inches(5.2), Inches(4.5))

    # SLIDE 4: SECTION_SPLITTER ("Topic One", subtitle, hero photo)
    s4 = prs.slides.add_slide(blank_layout)
    t4 = s4.shapes.add_textbox(Inches(1.5), Inches(2.2), Inches(9.0), Inches(1.0))
    t4.text_frame.paragraphs[0].text = "Topic One"
    sub4 = s4.shapes.add_textbox(Inches(1.5), Inches(3.3), Inches(9.0), Inches(0.8))
    sub4.text_frame.paragraphs[0].text = "Operational Excellence and Engineering Delivery"
    s4.shapes.add_picture(io.BytesIO(img_data), Inches(8.0), Inches(1.5), Inches(4.5), Inches(4.5))

    # SLIDE 5: DATA_TABLE_SLIDE (Table shape with rows and columns)
    s5 = prs.slides.add_slide(blank_layout)
    t5 = s5.shapes.add_textbox(Inches(1.0), Inches(0.5), Inches(8.0), Inches(0.8))
    t5.text_frame.paragraphs[0].text = "Financial Performance Metrics"
    table_shape = s5.shapes.add_table(4, 3, Inches(1.0), Inches(1.8), Inches(11.0), Inches(4.5))
    headers = ["Metric", "FY24 Actual", "FY25 Plan"]
    for c_idx, h in enumerate(headers):
        table_shape.table.cell(0, c_idx).text = h
    rows = [
        ["Revenue ($M)", "$124.5", "$168.0"],
        ["Operating Margin", "22.4%", "26.8%"],
        ["Customer Retention", "96.5%", "98.5%"],
    ]
    for r_idx, r_data in enumerate(rows):
        for c_idx, val in enumerate(r_data):
            table_shape.table.cell(r_idx + 1, c_idx).text = val

    # SLIDE 6: SECTION_SPLITTER / QUOTE ("Client Testimonial", quote text)
    s6 = prs.slides.add_slide(blank_layout)
    t6 = s6.shapes.add_textbox(Inches(1.0), Inches(1.8), Inches(9.0), Inches(1.0))
    t6.text_frame.paragraphs[0].text = "Client Testimonial"
    q6 = s6.shapes.add_textbox(Inches(1.0), Inches(3.0), Inches(9.0), Inches(1.5))
    q6.text_frame.paragraphs[0].text = '"BrandMorph transformed our entire enterprise content supply chain in days."'

    # SLIDE 7: TEAM_OR_GALLERY_GRID (4 portrait photos + Name and Role underneath each)
    s7 = prs.slides.add_slide(blank_layout)
    t7 = s7.shapes.add_textbox(Inches(1.0), Inches(0.5), Inches(8.0), Inches(0.8))
    t7.text_frame.paragraphs[0].text = "Executive Leadership Team"
    names = ["Alex Rivera", "Sarah Chen", "Marcus Vance", "Elena Rostova"]
    roles = ["Chief Executive Officer", "VP Engineering", "Chief Product Officer", "Head of Design"]
    for i in range(4):
        x = 0.85 + i * 3.1
        s7.shapes.add_picture(io.BytesIO(img_data), Inches(x), Inches(1.6), Inches(2.5), Inches(2.5))
        n_box = s7.shapes.add_textbox(Inches(x), Inches(4.3), Inches(2.5), Inches(0.35))
        n_box.text_frame.paragraphs[0].text = names[i]
        r_box = s7.shapes.add_textbox(Inches(x), Inches(4.7), Inches(2.5), Inches(0.35))
        r_box.text_frame.paragraphs[0].text = roles[i]

    # SLIDE 8: PROCESS_TIMELINE (Contains "Timeline", horizontal sequence of 4 milestones)
    s8 = prs.slides.add_slide(blank_layout)
    t8 = s8.shapes.add_textbox(Inches(1.0), Inches(0.5), Inches(8.0), Inches(0.8))
    t8.text_frame.paragraphs[0].text = "Product Delivery Timeline"
    quarters = ["Q1: Discovery", "Q2: Architecture", "Q3: Deployment", "Q4: Scale"]
    for i, q in enumerate(quarters):
        x = 1.0 + i * 2.8
        card = s8.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(2.5), Inches(2.4), Inches(2.8))
        card.fill.solid()
        # Alternate cyan milestone for contrast check
        card.fill.fore_color.rgb = RGBColor(0, 255, 255) if i == 1 else RGBColor(8, 22, 50)
        p = card.text_frame.paragraphs[0]
        p.text = q
        p.font.size = Pt(13)

    # SLIDE 9: MULTI_CARD_CONTENT ("Key Transformation Pillars", 3 cards)
    s9 = prs.slides.add_slide(blank_layout)
    t9 = s9.shapes.add_textbox(Inches(0.8), Inches(0.5), Inches(8.0), Inches(0.8))
    t9.text_frame.paragraphs[0].text = "Key Transformation Pillars"
    for i in range(3):
        box = s9.shapes.add_textbox(Inches(0.8 + i * 4.0), Inches(2.0), Inches(3.6), Inches(3.8))
        p = box.text_frame.paragraphs[0]
        p.text = f"Pillar 0{i+1}"
        p.font.bold = True
        p2 = box.text_frame.add_paragraph()
        p2.text = "High-velocity pipeline automation enforcing compliance and typography."

    # SLIDE 10: MULTI_CARD_CONTENT ("Global Infrastructure & Scale", 2 wide cards)
    s10 = prs.slides.add_slide(blank_layout)
    t10 = s10.shapes.add_textbox(Inches(0.8), Inches(0.5), Inches(8.0), Inches(0.8))
    t10.text_frame.paragraphs[0].text = "Global Infrastructure & Scale"
    for i in range(2):
        box = s10.shapes.add_textbox(Inches(0.8 + i * 6.0), Inches(2.0), Inches(5.6), Inches(4.0))
        box.text_frame.paragraphs[0].text = f"Zone {i+1} Regional Datacenter Architecture"

    # SLIDE 11: MULTI_CARD_CONTENT ("Risk Governance Framework", 3 cards + side photo)
    s11 = prs.slides.add_slide(blank_layout)
    t11 = s11.shapes.add_textbox(Inches(0.8), Inches(0.5), Inches(7.0), Inches(0.8))
    t11.text_frame.paragraphs[0].text = "Risk Governance Framework"
    for i in range(3):
        box = s11.shapes.add_textbox(Inches(0.8), Inches(1.6 + i * 1.5), Inches(5.5), Inches(1.1))
        box.text_frame.paragraphs[0].text = f"Control Level {i+1}: Automated CI/CD Auditing"
    s11.shapes.add_picture(io.BytesIO(img_data), Inches(7.5), Inches(1.6), Inches(4.8), Inches(4.5))

    # SLIDE 12: CLOSING_SLIDE ("Thank You", contact details)
    s12 = prs.slides.add_slide(blank_layout)
    t12 = s12.shapes.add_textbox(Inches(1.5), Inches(2.5), Inches(9.0), Inches(1.2))
    t12.text_frame.paragraphs[0].text = "Thank You"
    c12 = s12.shapes.add_textbox(Inches(1.5), Inches(3.8), Inches(9.0), Inches(0.8))
    c12.text_frame.paragraphs[0].text = "Contact: team@brandmorph.com | https://brandmorph-tau.vercel.app"

    prs.save(str(path))
    return path


def test_12_slide_presentation_archetypes_and_rules(tmp_path):
    """Automated test verifying all 8 slide archetypes and the 5 critical rules."""
    src_deck = tmp_path / "test_12_slides.pptx"
    out_deck = tmp_path / "morphed_12_slides.pptx"

    generate_12_slide_presentation(src_deck)
    assert src_deck.exists()

    # Also save to backend/samples/sample_12slide_archetypes.pptx for reference
    samples_dir = Path("backend/samples")
    if samples_dir.exists():
        try:
            generate_12_slide_presentation(samples_dir / "sample_12slide_archetypes.pptx")
        except Exception:
            pass

    # Execute MorphPipeline
    dna = BrandDNA.load("enterprise_navy")
    report = MorphPipeline(dna, options=MorphOptions()).run(src_deck, out_deck)

    # 1. Parse both PPTX objects
    prs = pptx.Presentation(str(out_deck))
    assert len(prs.slides) == 12

    # Decompile to JSON AST
    decompiler = SlideDecompiler(str(out_deck))
    ast_slides = decompiler.parse_deck()
    assert len(ast_slides) == 12

    # -------------------------------------------------------------------------
    # VERIFICATION 1: All 8 Archetypes are Classified and Detected
    # -------------------------------------------------------------------------
    detected_archetypes = {s["archetype"] for s in ast_slides}
    expected_archetypes = {
        SlideArchetype.COVER_SLIDE.value,
        SlideArchetype.AGENDA_SLIDE.value,
        SlideArchetype.SECTION_SPLITTER.value,
        SlideArchetype.DATA_TABLE_SLIDE.value,
        SlideArchetype.PROCESS_TIMELINE.value,
        SlideArchetype.TEAM_OR_GALLERY_GRID.value,
        SlideArchetype.MULTI_CARD_CONTENT.value,
        SlideArchetype.CLOSING_SLIDE.value,
    }
    assert expected_archetypes.issubset(detected_archetypes), (
        f"Missing archetypes: {expected_archetypes - detected_archetypes}"
    )

    # -------------------------------------------------------------------------
    # CHECK 1: Slide 1 (COVER_SLIDE) has Times New Roman, bold == False, 24-32pt
    # -------------------------------------------------------------------------
    slide1 = prs.slides[0]
    slide1_title = [
        s for s in slide1.shapes
        if s.has_text_frame and "Strategic Corporate Overview" in s.text_frame.text
    ][0]
    p1 = slide1_title.text_frame.paragraphs[0]
    assert len(p1.runs) > 0
    r1 = p1.runs[0]
    assert r1.font.name == "Times New Roman", f"Slide 1 Title font is {r1.font.name}, expected Times New Roman"
    assert r1.font.bold is False, f"Slide 1 Title bold is {r1.font.bold}, expected False"
    assert 24.0 <= r1.font.size.pt <= 32.0, f"Slide 1 Title size {r1.font.size.pt} not in [24, 32]"

    # -------------------------------------------------------------------------
    # CHECK 2: Content slides have titles snapped to top-left (left == 0.80", top == 0.45")
    # -------------------------------------------------------------------------
    content_slide_indices = [1, 2, 4, 6, 7, 8, 9, 10]  # Agenda, Multi-Card, Table, Team, Timeline, Multi-Cards
    for idx in content_slide_indices:
        slide = prs.slides[idx]
        title_candidates = [
            s for s in slide.shapes
            if s.has_text_frame
            and not getattr(s, "name", "").startswith("BrandMorph")
            and (s.top and s.top.inches < 1.5)
        ]
        assert len(title_candidates) > 0, f"Slide {idx+1} missing top title"
        title = title_candidates[0]
        assert abs(title.left.inches - 0.80) < 0.05, (
            f"Slide {idx+1} title left is {title.left.inches:.2f}\", expected 0.80\""
        )
        assert abs(title.top.inches - 0.45) < 0.05, (
            f"Slide {idx+1} title top is {title.top.inches:.2f}\", expected 0.45\""
        )

    # -------------------------------------------------------------------------
    # CHECK 3: Zero duplicate "BrandMorph" stamps exist
    # -------------------------------------------------------------------------
    for idx, slide in enumerate(prs.slides):
        stamps = [
            s for s in slide.shapes
            if s.name in ("BrandMorph_Logo_Stamp", "BrandMorphStamp")
            or (s.has_text_frame and "BRANDMORPH" in s.text_frame.text.upper() and (s.top and s.top.inches < 1.0))
        ]
        assert len(stamps) == 1, (
            f"Slide {idx+1} has {len(stamps)} BrandMorph stamps, expected exactly 1 (zero duplicates)"
        )

    # -------------------------------------------------------------------------
    # CHECK 4: All images appear in JSON AST with image_data_uri and do not overlap
    # -------------------------------------------------------------------------
    # Slides with images: Slide 2 (2 pics), Slide 3 (1 pic), Slide 4 (1 pic), Slide 7 (4 pics), Slide 11 (1 pic)
    image_slide_indices = [1, 2, 3, 6, 10]
    for idx in image_slide_indices:
        slide_ast = ast_slides[idx]
        pic_nodes = [n for n in slide_ast["nodes"] if n["type"] == "PICTURE"]
        assert len(pic_nodes) >= 1, f"Slide {idx+1} AST missing PICTURE nodes"
        for p in pic_nodes:
            assert "image_data_uri" in p, f"Slide {idx+1} picture node missing image_data_uri"
            assert p["image_data_uri"].startswith("data:image/"), f"Slide {idx+1} invalid image_data_uri format"

        # On content slides with side images (Slides 2, 3, 11), verify no horizontal overlap between text cards and pictures
        if idx in (1, 2, 10):
            text_nodes = [
                n for n in slide_ast["nodes"]
                if n["type"] == "TEXT_CONTAINER"
                and not n.get("shape_name", "").startswith("BrandMorph")
                and (n["y"] or 0) > 1.0  # content cards below title
            ]
            for t in text_nodes:
                assert (t["x"] + t["w"]) <= 7.0, (
                    f"Slide {idx+1} text card right edge {t['x']+t['w']:.2f}\" overlaps picture zone (>=7.1\")"
                )
            for p in pic_nodes:
                assert p["x"] >= 7.0, (
                    f"Slide {idx+1} picture left edge {p['x']:.2f}\" overlaps left text zone (<=6.75\")"
                )

    # -------------------------------------------------------------------------
    # CHECK 5: Every text run has explicit RGB color with WCAG contrast >= 4.5:1
    # -------------------------------------------------------------------------
    for s_idx, slide in enumerate(prs.slides):
        for shape in slide.shapes:
            if not shape.has_text_frame:
                continue
            # Determine effective shape background color
            shape_bg = "030C1E"
            if shape.fill and shape.fill.type == 1 and hasattr(shape.fill, "fore_color"):
                if hasattr(shape.fill.fore_color, "rgb"):
                    shape_bg = f"{shape.fill.fore_color.rgb}".upper()

            bg_rgb = hex_to_rgb(shape_bg)
            bg_lum = relative_luminance(*bg_rgb)

            for p in shape.text_frame.paragraphs:
                for r in p.runs:
                    if not r.text.strip():
                        continue
                    # Must have explicit color
                    assert r.font.color and r.font.color.type == 1, (
                        f"Slide {s_idx+1} run '{r.text}' missing explicit font color"
                    )
                    r_hex = f"{r.font.color.rgb}".upper()
                    r_rgb = hex_to_rgb(r_hex)
                    r_lum = relative_luminance(*r_rgb)

                    # Compute WCAG contrast ratio
                    bright = max(bg_lum, r_lum)
                    dark = min(bg_lum, r_lum)
                    contrast = (bright + 0.05) / (dark + 0.05)

                    assert contrast >= 4.5, (
                        f"Slide {s_idx+1} text '{r.text}' color #{r_hex} has insufficient contrast {contrast:.2f}:1 "
                        f"against background #{shape_bg}"
                    )

    # -------------------------------------------------------------------------
    # CHECK 6: Clean Corporate Table Styling & table_data extraction (Slide 5)
    # -------------------------------------------------------------------------
    s5 = prs.slides[4]
    table_shapes = [s for s in s5.shapes if getattr(s, "has_table", False) and s.has_table]
    assert len(table_shapes) == 1, "Slide 5 must contain exactly 1 table"
    t_shape = table_shapes[0]
    assert abs(t_shape.left.inches - 0.80) < 0.05, f"Table left is {t_shape.left.inches:.2f}\", expected 0.80\""
    assert abs(t_shape.top.inches - 1.65) < 0.05, f"Table top is {t_shape.top.inches:.2f}\", expected 1.65\""
    assert abs(t_shape.width.inches - 11.73) < 0.05, f"Table width is {t_shape.width.inches:.2f}\", expected 11.73\""
    assert t_shape.height.inches <= 4.85, f"Table height is {t_shape.height.inches:.2f}\", expected <= 4.8\""

    t = t_shape.table
    # Header row
    h_cell = t.cell(0, 0)
    assert f"{h_cell.fill.fore_color.rgb}".upper() == "FFB81C", "Header fill must be Gold #FFB81C"
    h_run = h_cell.text_frame.paragraphs[0].runs[0]
    assert f"{h_run.font.color.rgb}".upper() == "001F33", "Header text must be Dark Navy #001F33"
    assert h_run.font.bold is True, "Header text must be bold"

    # Data row 1 alternating fill
    d1_cell = t.cell(1, 0)
    assert f"{d1_cell.fill.fore_color.rgb}".upper() == "081E36", "Row 1 fill must be #081E36"
    d1_run = d1_cell.text_frame.paragraphs[0].runs[0]
    assert f"{d1_run.font.color.rgb}".upper() in ("FFB81C", "FFFFFF"), "First col text must be Gold or White"
    assert d1_run.font.bold is True, "First col text must be bold"

    # AST check
    s5_ast = ast_slides[4]
    t_nodes = [n for n in s5_ast["nodes"] if n["type"] == "TABLE"]
    assert len(t_nodes) == 1, "Slide 5 AST must have TABLE node"
    assert "table_data" in t_nodes[0], "Slide 5 TABLE node must have table_data"
    assert len(t_nodes[0]["table_data"]["rows"]) == 4, "table_data must have 4 rows"
    assert len(t_nodes[0]["table_data"]["col_widths"]) == 3, "table_data must have 3 col_widths"


def test_canva_dimension_normalization_and_card_injection(tmp_path):
    """Test 10.0" x 5.625" Canva deck dimension scaling, title detection, and card injection."""
    deck_path = tmp_path / "canva_template.pptx"
    out_path = tmp_path / "canva_morphed.pptx"

    prs = pptx.Presentation()
    # 10.0 x 5.625 Canva widescreen
    prs.slide_width = Inches(10.0)
    prs.slide_height = Inches(5.625)

    # Slide 1: Cover slide
    s0 = prs.slides.add_slide(prs.slide_layouts[6])
    t0 = s0.shapes.add_textbox(Inches(1.0), Inches(1.5), Inches(8.0), Inches(1.0))
    t0.text_frame.text = "Company Presentation"

    # Slide 2: Content slide
    slide = prs.slides.add_slide(prs.slide_layouts[6])

    # Decorative number "01" (should NOT be classified as title)
    num_box = slide.shapes.add_textbox(Inches(0.5), Inches(0.2), Inches(0.8), Inches(0.4))
    num_box.text_frame.text = "01"

    # Freeform slide title
    title_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.5), Inches(6.0), Inches(0.8))
    p_t = title_box.text_frame.paragraphs[0]
    p_t.text = "Quarterly Business Operations"
    p_t.font.size = Pt(24)

    # Loose body content text block without a backing card
    body_box = slide.shapes.add_textbox(Inches(1.0), Inches(2.0), Inches(5.0), Inches(1.5))
    p_b = body_box.text_frame.paragraphs[0]
    p_b.text = "Our cloud migration expanded delivery capability across enterprise accounts."
    p_b.font.size = Pt(12)

    # Slide 3: Closing slide
    s2 = prs.slides.add_slide(prs.slide_layouts[6])
    t2 = s2.shapes.add_textbox(Inches(1.0), Inches(2.5), Inches(8.0), Inches(1.0))
    t2.text_frame.text = "Thank You"

    prs.save(str(deck_path))

    # Run MorphPipeline
    dna = BrandDNA.load("enterprise_navy")
    MorphPipeline(dna).run(deck_path, out_path)

    # Verify morphed presentation dimensions scaled to 13.333 x 7.5
    morphed_prs = pptx.Presentation(str(out_path))
    assert abs(morphed_prs.slide_width.inches - 13.333) < 0.05
    assert abs(morphed_prs.slide_height.inches - 7.5) < 0.05

    m_slide = morphed_prs.slides[1]

    # Verify title is "Quarterly Business Operations", snapped to top-left, Times New Roman, unbolded
    t_shape = None
    for s in m_slide.shapes:
        if s.has_text_frame and "Quarterly Business Operations" in s.text_frame.text:
            t_shape = s
            break
    assert t_shape is not None, "Title shape 'Quarterly Business Operations' not found"
    assert abs(t_shape.left.inches - 0.80) < 0.05
    assert abs(t_shape.top.inches - 0.45) < 0.05
    run = t_shape.text_frame.paragraphs[0].runs[0]
    assert run.font.name == "Times New Roman"
    assert run.font.bold is False

    # Verify dynamic card injection behind body text
    injected_cards = [s for s in m_slide.shapes if getattr(s, "name", "") == "BrandMorphInjectedCard"]
    assert len(injected_cards) >= 1, "Expected dynamic card shape injection behind loose body text"
    card = injected_cards[0]
    assert card.fill and f"{card.fill.fore_color.rgb}".upper() == "081E36"

    # Verify Z-order: card element sits before body text element in spTree
    body_shape = [s for s in m_slide.shapes if s.has_text_frame and "cloud migration" in s.text_frame.text][0]
    spTree_list = list(m_slide.shapes._spTree)
    assert spTree_list.index(card._element) < spTree_list.index(body_shape._element), "Card must sit behind text"


def test_raw_mode_vs_governed_mode_preservation(tmp_path):
    """Test raw_mode=True preserves original light background and dark text, while raw_mode=False is governed."""
    deck_path = tmp_path / "light_deck.pptx"
    out_path = tmp_path / "governed_deck.pptx"

    prs = pptx.Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    slide = prs.slides.add_slide(prs.slide_layouts[6])

    # Add light slide with dark charcoal text
    t_box = slide.shapes.add_textbox(Inches(1.0), Inches(1.0), Inches(8.0), Inches(1.0))
    p = t_box.text_frame.paragraphs[0]
    p.text = "Enterprise Transformation"
    r = p.runs[0]
    r.font.name = "Calibri"
    r.font.color.rgb = RGBColor(17, 24, 39)  # #111827

    prs.save(str(deck_path))

    # 1. Parse raw deck with raw_mode=True
    raw_dec = SlideDecompiler(str(deck_path), raw_mode=True)
    raw_ast = raw_dec.parse_deck()
    assert len(raw_ast) == 1
    assert raw_ast[0]["background_color"] == "#FFFFFF"
    raw_text_node = [n for n in raw_ast[0]["nodes"] if n["type"] == "TEXT_CONTAINER"][0]
    assert raw_text_node["paragraphs"][0]["font_color"] == "#111827"

    # 2. Morph deck
    dna = BrandDNA.load("enterprise_navy")
    MorphPipeline(dna).run(deck_path, out_path)

    # 3. Parse governed deck with raw_mode=False
    gov_dec = SlideDecompiler(str(out_path), raw_mode=False)
    gov_ast = gov_dec.parse_deck()
    assert len(gov_ast) == 1
    assert gov_ast[0]["background_color"] in ("#001F33", "#030C1E")

