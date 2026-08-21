"""Akkodis brand tokens (PDR v1.2 section 4) plus canonical layout targets."""
from __future__ import annotations

CANONICAL_LAYOUTS = {
    "CONTENT": "12_Diseño personalizado",
    "TITLE": "3_Diseño personalizado",
    "DIVIDER_EMPTY": "Empty_Dark_Blue",
}

DEFAULT_BODY_FONT = "roboto"

BRAND_COLORS = {
    "base_dark": "030C1E",
    "card_surface": "081632",
    "gold": "FFB81C",
    "aqua": "00FFFF",
    "white": "FFFFFF",
    "title_light_bg": "0F172A",
    "body_light_bg": "334155",
}

LEGACY_GOLD_VARIANTS = {"FFC000", "FFB212", "EBAC00"}
LEGACY_AQUA_VARIANTS = {"1ED9F2"}

BRAND_FONT_SET = {"roboto", "arial", "times new roman"}

GUIDANCE_TEXT_MARKERS = ("font guidance", "do not change")

SAFE_AREA_IN = {"x": 0.5, "y": 0.4}
