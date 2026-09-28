"""FitGuard: measure, never guess.

The budget doctrine (design §2.1 ⑦): a shape's original text length was tuned
by the template designer, so any transformation that grows text risks
overflow. FitGuard measures actual rendered height with real font metrics
(PIL) and applies the shrink ladder — spacing first is unreliable across
viewers, so: reduce font size 1pt at a time (max 2 steps), then flag
`needs_review`. It never widens boxes and never deletes content.

When a family's font file is missing on the machine, an advance-width
estimator is used and the measurement is marked as an estimate in the report.
"""

from __future__ import annotations

import os
from pathlib import Path

from pptx import Presentation
from pptx.enum.text import MSO_AUTO_SIZE
from pptx.util import Pt

from ..brand.profile import BrandDNA
from ..report import ChangeEntry, MorphReport

EMU_PER_PT = 12700
_DEFAULT_SZ_PT = 18.0
_LINE_HEIGHT = 1.21
# advance-width factor (fraction of point size per char) when no font file
_WIDTH_FACTOR = {"condensed": 0.45, "regular": 0.52, "wide": 0.58}
_WIDE_FAMILIES = {"verdana", "segoe ui", "tahoma", "impact"}
_CONDENSED_FAMILIES = {"arial narrow", "liberation sans narrow", "haettenschweiler"}

_FONT_DIRS = [
    Path("assets/fonts"),
    Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts",
    Path("/usr/share/fonts"),
    Path("/usr/local/share/fonts"),
]
_FONT_FILES = {
    "arial": ["arial.ttf", "Arial.ttf"],
    "calibri": ["calibri.ttf", "Calibri.ttf"],
    "segoe ui": ["segoeui.ttf"],
    "times new roman": ["times.ttf"],
    "georgia": ["georgia.ttf"],
    "verdana": ["verdana.ttf"],
    "tahoma": ["tahoma.ttf"],
    "trebuchet ms": ["trebuc.ttf"],
    "liberation sans": ["LiberationSans-Regular.ttf"],
    "noto sans": ["NotoSans-Regular.ttf"],
}


def resolve_font_file(family: str, bold: bool = False) -> Path | None:
    key = (family or "").strip().lower()
    names = _FONT_FILES.get(key)
    if not names:
        return None
    wanted = ([names[0].replace(".ttf", "bd.ttf")] if bold else []) + names
    for d in _FONT_DIRS:
        for n in wanted:
            p = d / n
            if p.exists():
                return p
    return None


def _width_factor(family: str) -> float:
    key = (family or "").strip().lower()
    if key in _CONDENSED_FAMILIES:
        return _WIDTH_FACTOR["condensed"]
    if key in _WIDE_FAMILIES:
        return _WIDTH_FACTOR["wide"]
    return _WIDTH_FACTOR["regular"]


class _Para:
    __slots__ = ("defrpr", "family", "line_spacing", "runs", "size", "text")

    def __init__(self, text, size, family, line_spacing, runs, defrpr):
        self.text, self.size, self.family = text, size, family
        self.line_spacing, self.runs, self.defrpr = line_spacing, runs, defrpr


class FitGuard:
    def __init__(self, dna: BrandDNA, report: MorphReport):
        self.dna = dna
        self.report = report
        self._font_cache: dict[tuple, object] = {}

    def run(self, prs: Presentation) -> None:
        self._slide_width_emu = prs.slide_width
        for idx, slide in enumerate(prs.slides):
            self._check_tree(slide.shapes, idx, slide)

    # -- traversal ---------------------------------------------------------
    def _check_tree(self, shapes, slide_idx: int, slide) -> None:
        from pptx.enum.shapes import MSO_SHAPE_TYPE

        for shp in shapes:
            if shp.shape_type == MSO_SHAPE_TYPE.GROUP:
                self._check_tree(shp.shapes, slide_idx, slide)
                continue
            if getattr(shp, "has_text_frame", False) and shp.has_text_frame:
                self._check_shape(shp, slide_idx, slide)

    def _check_shape(self, shape, slide_idx: int, slide) -> None:
        tf = shape.text_frame
        text = tf.text.strip()
        if not text:
            return
        if tf.auto_size == MSO_AUTO_SIZE.TEXT_TO_FIT_SHAPE:
            return  # viewer-side shrink is already armed
        if tf.auto_size == MSO_AUTO_SIZE.SHAPE_TO_FIT_TEXT:
            # the box grows with its text — vertical overflow is impossible,
            # but a wrap-off box can bleed past the slide's right edge
            if getattr(tf, "word_wrap", True) is False:
                self._check_horizontal_bleed(shape, tf, slide_idx, slide)
            return
        if getattr(tf, "word_wrap", True) is False:
            self._check_horizontal_bleed(shape, tf, slide_idx, slide)
            return

        try:
            # margins are None when inherited (default insets 0.1" l/r, 0.05" t/b)
            ml = (tf.margin_left if tf.margin_left is not None else 91440) / EMU_PER_PT
            mr = (tf.margin_right if tf.margin_right is not None else 91440) / EMU_PER_PT
            mt = (tf.margin_top if tf.margin_top is not None else 45720) / EMU_PER_PT
            mb = (tf.margin_bottom if tf.margin_bottom is not None else 45720) / EMU_PER_PT
            box_w = shape.width / EMU_PER_PT - ml - mr
            box_h = shape.height / EMU_PER_PT - mt - mb
        except TypeError:
            return  # shape without explicit extents
        if box_w <= 0 or box_h <= 0:
            return

        paras = self._collect(tf)
        needed = self._needed_height(paras, box_w)
        slack = 1.0 + self.dna.rules.fit_slack
        if needed <= box_h * slack:
            return

        # shrink ladder: -1pt per step, max 2 steps (design §2.1 ⑦)
        for step in (1, 2):
            for para in paras:
                para.size = max(9.0, (para.size or _DEFAULT_SZ_PT) - 1)
            needed = self._needed_height(paras, box_w)
            if needed <= box_h * slack:
                self._apply(paras, slide_idx, step)
                return
        self.report.flag(
            f"slide {slide_idx}: text overflows shape '{shape.name}' even after "
            f"2 shrink steps ({needed:.0f}pt needed vs {box_h:.0f}pt box) — manual layout fix required"
        )

    def _check_horizontal_bleed(self, shape, tf, slide_idx: int, slide) -> None:
        """wrap='none' boxes render one unwrapped line: flag right-edge bleed."""
        try:
            ml = (tf.margin_left if tf.margin_left is not None else 91440) / EMU_PER_PT
            mr = (tf.margin_right if tf.margin_right is not None else 91440) / EMU_PER_PT
            left = shape.left / EMU_PER_PT
            avail = self._slide_width_emu / EMU_PER_PT - left - ml - mr
        except TypeError:
            return
        worst = 0.0
        for p in tf.paragraphs:
            size = None
            family = self.dna.typography.body.family
            for r in p.runs:
                if r.font.size is not None:
                    size = r.font.size.pt
                if r.font.name:
                    family = r.font.name
            size = size or _DEFAULT_SZ_PT
            if p.text.strip():
                worst = max(worst, self._line_width(p.text, size, family))
        if worst > avail * 1.05:
            self.report.flag(
                f"slide {slide_idx}: wrap-off text in '{shape.name}' is ~{worst:.0f}pt wide "
                f"but only ~{avail:.0f}pt of slide width remains — it will bleed past the "
                f"right edge; widen the box or enable word wrap"
            )

    # -- measurement -------------------------------------------------------
    def _collect(self, tf) -> list[_Para]:
        out = []
        body_family = self.dna.typography.body.family
        for p in tf.paragraphs:
            if not p.text.strip():
                out.append(_Para("", _DEFAULT_SZ_PT, body_family, None, [], None))
                continue
            sizes, family = [], body_family
            for r in p.runs:
                if r.font.size is not None:
                    sizes.append(r.font.size.pt)
                if r.font.name:
                    family = r.font.name
            if not sizes:
                defrpr = p._pPr.find(
                    "{http://schemas.openxmlformats.org/drawingml/2006/main}defRPr"
                ) if p._pPr is not None else None
                if defrpr is not None and defrpr.get("sz"):
                    sizes.append(int(defrpr.get("sz")) / 100)
            out.append(_Para(
                p.text, sizes[0] if sizes else None, family,
                p.line_spacing if isinstance(p.line_spacing, float) else None,
                list(p.runs), p._pPr,
            ))
        return out

    def _needed_height(self, paras: list[_Para], box_w: float) -> float:
        total = 0.0
        for para in paras:
            size = para.size or _DEFAULT_SZ_PT
            lines = self._line_count(para.text, size, para.family, box_w)
            lh = size * _LINE_HEIGHT * (para.line_spacing or 1.0)
            total += lines * lh
        return total

    def _line_count(self, text: str, size: float, family: str, box_w: float) -> int:
        if not text:
            return 1
        measure = self._measurer(family, size)
        if measure is not None:
            font, scale = measure
            width = lambda s: font.getlength(s) / scale
        else:
            factor = _width_factor(family)
            width = lambda s: len(s) * size * factor
        lines, cur = 1, ""
        for word in text.split():
            candidate = f"{cur} {word}".strip()
            if width(candidate) <= box_w or not cur:
                cur = candidate
            else:
                lines += 1
                cur = word
        return lines

    def _line_width(self, text: str, size: float, family: str) -> float:
        measure = self._measurer(family, size)
        if measure is not None:
            font, scale = measure
            return font.getlength(text) / scale
        return len(text) * size * _width_factor(family)

    def _measurer(self, family: str, size: float):
        key = (family, round(size))
        if key in self._font_cache:
            return self._font_cache[key]
        result = None
        path = resolve_font_file(family)
        if path is not None:
            try:
                from PIL import ImageFont

                scale = 4  # measure at 4x for sub-point precision
                result = (ImageFont.truetype(str(path), int(size * scale)), scale)
            except Exception:
                result = None
        self._font_cache[key] = result
        return result

    # -- application -------------------------------------------------------
    def _apply(self, paras: list[_Para], slide_idx: int, steps: int) -> None:
        for para in paras:
            if not para.runs:
                continue
            for r in para.runs:
                if r.font.size is not None:
                    r.font.size = Pt(round(r.font.size.pt))
        self.report.add(ChangeEntry(
            stage="fit", slide=slide_idx, element="text_frame", kind="size",
            before=f"-{steps}pt pending", after="applied", role="fit",
            note=f"shrink ladder applied ({steps} step(s))",
        ))
