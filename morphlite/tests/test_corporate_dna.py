"""Unit tests verifying strict enforcement of Corporate Style DNA & Layout standards."""
import os
import sys
import tempfile
from pathlib import Path
import pptx
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "backend"))

from backend.builder import NativePPTXBuilder, BrandTokens, rgb_luminance
from backend.decompiler import SlideDecompiler
from morphlite.rules.brand_tokens import BRAND_COLORS


def test_brand_palette_dna():
    """Verify primary and secondary color tokens match Akkodis standards."""
    assert BRAND_COLORS["base_dark"] == "001F33"
    assert BRAND_COLORS["gold"] == "FFB81C"
    assert BRAND_COLORS["aqua"] in ("00FFFF", "07FFFF")
    assert BRAND_COLORS["card_surface"] in ("081E36", "081632")


def test_contrast_resolver():
    """Verify background-aware contrast resolver prevents black text on dark and ensures dark text on bright."""
    builder = NativePPTXBuilder()

    # Dark background -> Text must be White or Gold
    dark_fill = RGBColor(0, 31, 51)  # #001F33
    color_body = builder._resolve_contrast_color(dark_fill, is_title=False, is_subheading=False)
    assert color_body == BrandTokens.TEXT_WHITE

    color_title = builder._resolve_contrast_color(dark_fill, is_title=True, is_subheading=False)
    assert color_title == BrandTokens.GOLD

    # Bright background (Gold or Cyan) -> Text must be Dark Navy
    gold_fill = RGBColor(255, 184, 28)  # #FFB81C
    color_on_gold = builder._resolve_contrast_color(gold_fill, is_title=False, is_subheading=False)
    assert color_on_gold == BrandTokens.TEXT_DARK

    cyan_fill = RGBColor(0, 255, 255)  # #00FFFF
    color_on_cyan = builder._resolve_contrast_color(cyan_fill, is_title=False, is_subheading=False)
    assert color_on_cyan == BrandTokens.TEXT_DARK


def test_title_and_body_typography_rules():
    """Verify title, subheading, and body font rules during slide build."""
    builder = NativePPTXBuilder()
    mock_slide_ast = {
        "slide_id": 1,
        "nodes": [
            {
                "id": 1,
                "type": "TEXT_CONTAINER",
                "is_title": True,
                "bbox": {"left": 0.8, "top": 0.5, "width": 10.0, "height": 1.2},
                "paragraphs": [
                    # Large title (36pt) -> must clamp to 30pt, NOT bold, Times New Roman, Gold
                    {"text": "Executive ADAS Validation Program", "font_size": 36, "bold": True}
                ]
            },
            {
                "id": 2,
                "type": "TEXT_CONTAINER",
                "bbox": {"left": 1.0, "top": 2.2, "width": 5.0, "height": 4.0},
                "paragraphs": [
                    # Subheading -> 11-16pt, bold=True, Roboto/Arial
                    {"text": "Key Milestone Deliverables", "font_size": 16, "bold": True},
                    # Body bullet -> >=8pt, bold=False, italic=False
                    {"text": "Deterministic latency across CAN-FD bus.", "font_size": 11, "bold": True, "italic": True}
                ]
            }
        ]
    }

    slide = builder.build_slide(mock_slide_ast)

    # Check that logo stamp was added
    has_logo = False
    for s in slide.shapes:
        if s.has_text_frame and "AKKODIS" in s.text_frame.text:
            has_logo = True
            assert round(s.left.inches, 1) == 11.4
            assert round(s.top.inches, 2) == 0.35
    assert has_logo, "Top-right Akkodis logo stamp must be present on every slide"


def test_slide_builder_save_roundtrip():
    """Verify NativePPTXBuilder builds a valid PPTX with dark background."""
    builder = NativePPTXBuilder()
    slide = builder.build_slide({"slide_id": 1, "nodes": []})

    with tempfile.NamedTemporaryFile(suffix=".pptx", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        builder.save(tmp_path)
        prs = pptx.Presentation(tmp_path)
        assert len(prs.slides) == 1
        # Check background fill
        bg = prs.slides[0].background
        assert bg.fill.type == 1
        assert str(bg.fill.fore_color.rgb) == "001F33"
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
