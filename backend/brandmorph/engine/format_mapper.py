"""DirectFormatMapper: role-aware remapping of explicitly-styled colors.

Decks rarely rely on the theme alone — authors hard-paint hexes everywhere.
v1 ignored this layer entirely; v2 remaps every explicit `a:srgbClr` while
preserving the *role* the color played (v1's builder painted everything with
one fixed set, diagnosis defect D2).

Mapping decision (design §2.1 ④):
  1. classify the color's context from its XML ancestors
     (text run / line / gradient stop / table cell / bullet / fill / effect)
  2. classify its *role*: background-ish, neutral surface, text ink or accent —
     derived from luminance/saturation relative to the slide's own background
  3. map to the BrandDNA color playing the same role, nearest-first in Lab
  4. colors already within dE<8 of ANY brand color are left alone (this makes
     the whole engine idempotent and lets partially-branded decks round-trip)

Picture fills (a:blipFill) are never touched — recoloring photos is a
non-goal (design §2.4).
"""

from __future__ import annotations

from lxml import etree
from pptx import Presentation

from ..brand.profile import PALETTE_ROLES, BrandDNA
from ..report import ChangeEntry, MorphReport
from .colorutil import hex_delta, hex_to_lab, hex_to_rgb, normalize_hex, rgb_to_hls

_A = "http://schemas.openxmlformats.org/drawingml/2006/main"
_SRGB = f"{{{_A}}}srgbClr"

_FILL_CONTEXTS = ("fill", "gradient", "effect", "table_fill")
_IDEMPOTENCE_BAND = 8.0
_BG_BAND = 12.0
_NEUTRAL_SAT = 0.10


def _local(el) -> str:
    return etree.QName(el).localname


def _context(srgb_el) -> str:
    """Classify the element a color styles by walking its XML ancestors."""
    for anc in srgb_el.iterancestors():
        name = _local(anc)
        if name == "blipFill":
            return "skip"          # image recoloring is out of scope
        if name == "ln":
            return "line"
        if name == "gs":
            return "gradient"
        if name == "buClr":
            return "bullet"
        if name == "tcPr":
            return "table_fill"
        if name in ("effectLst", "effectDag"):
            return "effect"
        if name in ("rPr", "defRPr", "endParaRPr"):
            return "text"
    return "fill"


def _nearest(val_hex: str, candidates: list[tuple[str, str]]) -> tuple[str, str, float]:
    best = min(candidates, key=lambda c: hex_delta(val_hex, c[0]))
    return best[0], best[1], hex_delta(val_hex, best[0])


def _is_brand_color(val_hex: str, dna: BrandDNA) -> bool:
    p = dna.palette
    for role in PALETTE_ROLES:
        if hex_delta(val_hex, getattr(p, role).hex) < _IDEMPOTENCE_BAND:
            return True
    return False


def _decide(
    val_hex: str, context: str, bg_hex: str, dna: BrandDNA
) -> tuple[str, str, float] | None:
    """Return (target_hex, role, confidence) or None when unmappable."""
    p = dna.palette
    src_L = hex_to_lab(val_hex)[0]
    h, _l, s = rgb_to_hls(*hex_to_rgb(val_hex))

    if context in _FILL_CONTEXTS:
        if hex_delta(val_hex, bg_hex) < _BG_BAND:
            return p.background.hex, "background", 0.90
        if s < _NEUTRAL_SAT:
            target, role, d = _nearest(val_hex, dna.surface_candidates())
            return target, role, 0.75
        target, role, d = _nearest(val_hex, dna.accent_candidates())
        return target, role, 0.70
    if context in ("line", "bullet"):
        target, role, d = _nearest(val_hex, dna.accent_candidates())
        return target, role, 0.70
    if context == "text":
        bg_L = hex_to_lab(bg_hex)[0]
        if s < _NEUTRAL_SAT:
            if abs(src_L - bg_L) >= 40:
                return p.text_primary.hex, "text_primary", 0.85
            return p.text_muted.hex, "text_muted", 0.70
        target, role, d = _nearest(val_hex, dna.accent_candidates())
        return target, role, 0.60
    return None


def _estimate_bg(root, fallback: str) -> str:
    """Most common explicitly-filled shape color on the part; fallback hex."""
    counts: dict[str, int] = {}
    for solid in root.iter(f"{{{_A}}}solidFill"):
        parent = solid.getparent()
        if parent is None or _local(parent) in ("rPr", "defRPr", "endParaRPr", "tcPr", "buClr"):
            continue
        for child in solid:
            if _local(child) == "srgbClr" and child.get("val"):
                counts[child.get("val").upper()] = counts.get(child.get("val").upper(), 0) + 1
    if not counts:
        return fallback
    return max(counts.items(), key=lambda kv: kv[1])[0]


def _theme_lt1(prs: Presentation) -> str:
    try:
        master = prs.slide_masters[0]
        theme = master.part.part_related_by(
            "http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme"
        )
        root = etree.fromstring(theme.blob)
        lt1 = root.find(".//a:clrScheme/a:lt1", {"a": _A})
        if lt1 is not None:
            cur = _current_hex_of(lt1)
            if cur:
                return cur
    except Exception:
        pass
    return "FFFFFF"


def _current_hex_of(slot_el) -> str | None:
    for child in slot_el:
        tag = _local(child)
        if tag == "srgbClr":
            return (child.get("val") or "").upper()
        if tag == "sysClr" and child.get("lastClr"):
            return child.get("lastClr").upper()
    return None


class DirectFormatMapper:
    def __init__(self, dna: BrandDNA, report: MorphReport):
        self.dna = dna
        self.report = report

    def run(self, prs: Presentation) -> None:
        fallback_bg = _theme_lt1(prs)
        for master in prs.slide_masters:
            self._sweep(master.element, f"master:{master.name or 'default'}", fallback_bg)
            for layout in master.slide_layouts:
                self._sweep(layout.element, f"layout:{layout.name}", fallback_bg)
        for idx, slide in enumerate(prs.slides):
            label_bg = _estimate_bg(slide.element, fallback_bg)
            self._sweep(slide.element, f"slide:{idx}", label_bg, slide_idx=idx)
            self._map_charts(slide, idx, label_bg)

    def _sweep(self, root, label: str, bg_hex: str, slide_idx: int | None = None) -> None:
        for srgb in list(root.iter(_SRGB)):
            raw = srgb.get("val")
            if not raw:
                continue
            try:
                val = normalize_hex(raw)
            except ValueError:
                continue
            if _is_brand_color(val, self.dna):
                continue
            context = _context(srgb)
            if context == "skip":
                continue
            decision = _decide(val, context, bg_hex, self.dna)
            if decision is None:
                continue
            target, role, confidence = decision
            if hex_delta(val, target) < _IDEMPOTENCE_BAND:
                continue
            srgb.set("val", target)
            self.report.add(ChangeEntry(
                stage="format", slide=slide_idx, element=label,
                kind="color", before=val, after=target, role=role,
                delta_e=hex_delta(val, target), confidence=confidence,
                note=f"context={context}",
            ))

    def _map_charts(self, slide, slide_idx: int, bg_hex: str) -> None:
        for shp in slide.shapes:
            if not (getattr(shp, "has_chart", False) and shp.has_chart):
                continue
            chart_space = getattr(shp.chart, "_chartSpace", None)
            if chart_space is None:
                continue
            self._sweep(chart_space, f"slide:{slide_idx}:chart", bg_hex, slide_idx=slide_idx)
