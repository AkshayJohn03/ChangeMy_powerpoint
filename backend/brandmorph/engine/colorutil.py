"""Color math for brand mapping: sRGB <-> CIE Lab and Delta-E 76.

Hand-rolled (no color-science dependency) so the engine runs anywhere
python-pptx runs. Lab is used because Euclidean distance in Lab (dE76)
approximates perceived color difference far better than RGB distance —
e.g. dark navy (#030C1E) and black (#000000) are RGB-far but perceptually
close, which is exactly the confusion RGB matching would make in
role-preserving brand mapping.
"""

from __future__ import annotations

import colorsys
import math


def normalize_hex(value: str) -> str:
    """Normalize any common hex spelling to uppercase 6-digit form."""
    v = value.strip().lstrip("#")
    if len(v) == 3:
        v = "".join(c * 2 for c in v)
    if len(v) != 6:
        raise ValueError(f"not a 6-digit hex color: {value!r}")
    int(v, 16)  # validates
    return v.upper()


def hex_to_rgb(value: str) -> tuple[int, int, int]:
    v = normalize_hex(value)
    return int(v[0:2], 16), int(v[2:4], 16), int(v[4:6], 16)


def rgb_to_hex(r: int, g: int, b: int) -> str:
    return f"{max(0, min(255, r)):02X}{max(0, min(255, g)):02X}{max(0, min(255, b)):02X}"


def rgb_to_hls(r: int, g: int, b: int) -> tuple[float, float, float]:
    """HLS in 0..1 (colorsys convention: hue, lightness, saturation)."""
    return colorsys.rgb_to_hls(r / 255, g / 255, b / 255)


def relative_luminance(r: int, g: int, b: int) -> float:
    """WCAG relative luminance, 0..1."""

    def lin(c: float) -> float:
        c /= 255
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

    return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)


def _srgb_to_linear(c: float) -> float:
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def rgb_to_lab(r: int, g: int, b: int) -> tuple[float, float, float]:
    """sRGB (0-255) -> CIE Lab (D65, 2 deg)."""
    rl, gl, bl = (_srgb_to_linear(c / 255) for c in (r, g, b))
    x = (0.4124564 * rl + 0.3575761 * gl + 0.1804375 * bl) / 0.95047
    y = (0.2126729 * rl + 0.7151522 * gl + 0.0721750 * bl) / 1.0
    z = (0.0193339 * rl + 0.1191920 * gl + 0.9503041 * bl) / 1.08883

    def f(t: float) -> float:
        return t ** (1 / 3) if t > 0.008856 else (7.787 * t) + 16 / 116

    fx, fy, fz = f(x), f(y), f(z)
    return 116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz)


def hex_to_lab(value: str) -> tuple[float, float, float]:
    return rgb_to_lab(*hex_to_rgb(value))


def delta_e76(lab1: tuple[float, float, float], lab2: tuple[float, float, float]) -> float:
    """CIE76 color difference. <2 imperceptible, <8 'same role/color' band."""
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(lab1, lab2)))


def hex_delta(h1: str, h2: str) -> float:
    return delta_e76(hex_to_lab(h1), hex_to_lab(h2))


def shade(hex_color: str, lightness_delta: float) -> str:
    """Return a hue-true shade: shift Lab L by delta, clamp chroma drift.

    Used to build accent3-6 theme slots from one brand accent without
    inventing new hues (design rule: prefer tints/shades over new colors).
    """
    L, a, b = hex_to_lab(hex_color)
    L2 = max(0.0, min(100.0, L + lightness_delta))
    # keep chroma proportional as lightness approaches the extremes
    scale = 1.0 - 0.4 * abs(L2 - 50) / 50
    return lab_to_hex(L2, a * scale, b * scale)


def lab_to_hex(L: float, a: float, b: float) -> str:
    fy = (L + 16) / 116
    fx = fy + a / 500
    fz = fy - b / 200

    def finv(t: float) -> float:
        t3 = t ** 3
        return t3 if t3 > 0.008856 else (t - 16 / 116) / 7.787

    x = 0.95047 * finv(fx)
    y = 1.0 * finv(fy)
    z = 1.08883 * finv(fz)

    def to_srgb(c: float) -> int:
        c = 12.92 * c if c <= 0.0031308 else 1.055 * (c ** (1 / 2.4)) - 0.055
        return round(max(0.0, min(1.0, c)) * 255)

    r = to_srgb(3.2404542 * x - 1.5371385 * y - 0.4985314 * z)
    g = to_srgb(-0.9692660 * x + 1.8760108 * y + 0.0415560 * z)
    bl = to_srgb(0.0556434 * x - 0.2040259 * y + 1.0572252 * z)
    return rgb_to_hex(r, g, bl)
