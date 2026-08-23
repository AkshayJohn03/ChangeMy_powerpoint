"""Brand profile: isolates all target-brand constants from the mutation layer.

v0.1 ships with the Akkodis default profile. Future versions will support
loading alternative profiles from JSON.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from pptx.dml.color import RGBColor


@dataclass(frozen=True)
class BrandProfile:
    name: str = "akkodis_default"

    body_font: str = "Arial"
    heading_font: str = "Times New Roman"

    gold_hex: str = "FFB81C"
    white_hex: str = "FFFFFF"
    dark_hex: str = "030C1E"
    card_hex: str = "081632"

    resize_map: dict = field(default_factory=lambda: {
        12.0: 10.0, 14.0: 12.0, 16.0: 12.0, 16.7: 12.0,
        20.0: 12.0, 32.0: 28.0, 36.0: 24.0,
    })

    legacy_gold_variants: tuple = (
        (0xFF, 0xC0, 0x00),
        (0xFF, 0xB2, 0x12),
        (0xEB, 0xAC, 0x00),
    )

    font_tiers: list = field(default_factory=lambda: [
        {"name": "heading", "min": 24, "target": 28},
        {"name": "body", "min": 12, "target": 14},
        {"name": "caption", "min": 0, "target": 10},
    ])

    @property
    def gold_rgb(self) -> RGBColor:
        return RGBColor(*self._hex_tuple(self.gold_hex))

    @property
    def white_rgb(self) -> RGBColor:
        return RGBColor(*self._hex_tuple(self.white_hex))

    @property
    def dark_rgb(self) -> RGBColor:
        return RGBColor(*self._hex_tuple(self.dark_hex))

    def legacy_color_target(self, rgb: RGBColor) -> RGBColor | None:
        for candidate in self.legacy_gold_variants:
            if rgb == RGBColor(*candidate):
                return self.gold_rgb
        return None

    @staticmethod
    def _hex_tuple(hex_str: str) -> tuple:
        hex_str = hex_str.lstrip("#")
        return tuple(int(hex_str[i:i + 2], 16) for i in (0, 2, 4))

    def to_json(self) -> dict:
        return {
            "name": self.name,
            "body_font": self.body_font,
            "heading_font": self.heading_font,
            "colors": {
                "gold": self.gold_hex, "white": self.white_hex,
                "dark": self.dark_hex, "card": self.card_hex,
            },
            "resize_map": {str(k): v for k, v in self.resize_map.items()},
            "legacy_gold_variants": [f"{r:02X}{g:02X}{b:02X}" for r, g, b in self.legacy_gold_variants],
        }

    @classmethod
    def from_json_file(cls, path: Path) -> "BrandProfile":
        data = json.loads(path.read_text(encoding="utf-8"))
        colors = data.get("colors", {})
        legacy = tuple(
            cls._hex_tuple(h) for h in data.get("legacy_gold_variants", [])
        )
        return cls(
            name=data.get("name", "custom"),
            body_font=data.get("body_font", "Arial"),
            heading_font=data.get("heading_font", "Times New Roman"),
            gold_hex=colors.get("gold", "FFB81C"),
            white_hex=colors.get("white", "FFFFFF"),
            dark_hex=colors.get("dark", "030C1E"),
            card_hex=colors.get("card", "081632"),
            resize_map={float(k): v for k, v in data.get("resize_map", {}).items()},
            legacy_gold_variants=legacy,
        )


DEFAULT_PROFILE = BrandProfile()
