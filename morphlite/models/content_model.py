"""ContentModel + PPTX -> ContentModel extraction.

The content model is the *model-readable* intermediate: a raw deck reduced to
its content (text blocks in visual order, tables, images, notes) with the
geometry that matters for semantics (visual order, font size, level) but none
of the brand chrome that a renderer will re-add. An LLM reads this, then emits
a typed slides spec (the reverse direction lives in morphlite/spec/slides_schema.py).
"""
from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
from typing import Any, Iterator

import pptx
from pptx.enum.shapes import MSO_SHAPE_TYPE


@dataclass
class BBox:
    left: float = 0.0
    top: float = 0.0
    width: float = 0.0
    height: float = 0.0

    @classmethod
    def from_shape(cls, shape) -> "BBox":
        left = shape.left / 914400.0 if shape.left is not None else 0.0
        top = shape.top / 914400.0 if shape.top is not None else 0.0
        width = shape.width / 914400.0 if shape.width is not None else 0.0
        height = shape.height / 914400.0 if shape.height is not None else 0.0
        return cls(round(left, 3), round(top, 3), round(width, 3), round(height, 3))


@dataclass
class TextBlock:
    idx: int
    text: str
    bbox: BBox = field(default_factory=BBox)
    level: int = 0
    font_size: float = 12.0
    bold: bool = False
    italic: bool = False
    align: str = "LEFT"

    def to_line(self) -> str:
        prefix = "  " * self.level
        s = f"{self.font_size:.0f}pt"
        if self.bold:
            s += "/b"
        return f"{prefix}[{s}] {self.text}"


@dataclass
class TableBlock:
    idx: int
    title_hint: str | None
    headers: list[str]
    rows: list[list[str]]
    bbox: BBox = field(default_factory=BBox)

    def to_line(self) -> str:
        head = " | ".join(self.headers)
        body = "; ".join(" | ".join(r) for r in self.rows[:6])
        return f"TABLE headers=[{head}] rows=[{body}]"


@dataclass
class ImageBlock:
    idx: int
    bbox: BBox = field(default_factory=BBox)
    content_type: str = "picture"
    extent: str = ""

    def to_line(self) -> str:
        return (
            f"IMAGE {self.extent or self.content_type} "
            f"({self.bbox.width:.1f}x{self.bbox.height:.1f}in @"
            f"{self.bbox.left:.1f},{self.bbox.top:.1f})"
        )


@dataclass
class SlideContent:
    slide_no: int
    blocks: list[Any] = field(default_factory=list)
    notes: str = ""
    has_splash_image: bool = False

    @property
    def text_blocks(self) -> list[TextBlock]:
        return [b for b in self.blocks if isinstance(b, TextBlock)]

    def to_text(self, include_notes: bool = False) -> str:
        lines = [f"--- slide {self.slide_no} ---"]
        for b in self.blocks:
            lines.append(b.to_line())
        if self.has_splash_image:
            lines.append("(full-bleed image / splash)")
        if include_notes and self.notes:
            lines.append(f"NOTES: {self.notes}")
        return "\n".join(lines)


@dataclass
class DeckContent:
    source_path: str = ""
    slide_w: float = 13.333
    slide_h: float = 7.5
    slides: list[SlideContent] = field(default_factory=list)

    def to_prompt(self, include_notes: bool = False) -> str:
        return "\n\n".join(s.to_text(include_notes) for s in self.slides)

    def to_compact(self) -> list[list[str]]:
        """Per-slide list of (kind, text) pairs, cheap to dump as JSON for evals."""
        out = []
        for s in self.slides:
            out.append([b.to_line() for b in s.blocks])
        return out

    @property
    def n_slides(self) -> int:
        return len(self.slides)


_NOISE_MARKERS = (
    "Font Guidance",
    "Do not change the template",
    "Placeholder",
    "Insert text",
)


def _is_noise(text: str) -> bool:
    t = text.strip()
    if not t:
        return True
    return any(m.lower() in t.lower() for m in _NOISE_MARKERS)


def extract_deck(path: str, include_notes: bool = True) -> DeckContent:
    """Read a .pptx/.ppt into a DeckContent intermediate.

    Text is read in *visual order* (top-to-bottom, then left-to-right) using each
    block's bounding box, so the LLM gets reliable reading order without relying
    on Python's often-random shape iteration order.
    """
    prs = pptx.Presentation(path)
    emu = 914400.0
    deck = DeckContent(
        source_path=path,
        slide_w=prs.slide_width / emu if prs.slide_width else 13.333,
        slide_h=prs.slide_height / emu if prs.slide_height else 7.5,
    )

    for si, slide in enumerate(prs.slides):
        sc = SlideContent(slide_no=si + 1)
        counter = _IdCounter()

        def walk(shape, level: int = 0) -> None:
            if shape.shape_type == MSO_SHAPE_TYPE.GROUP and hasattr(shape, "shapes"):
                for child in shape.shapes:
                    walk(child, level)
                return
            # Connectors / lines: structural chrome, not content — skip without error
            # python-pptx reports connectors as LINE (9) with tag cxnSp; handle both
            try:
                if shape.shape_type == MSO_SHAPE_TYPE.LINE:
                    return
                if shape._element.tag.endswith("}cxnSp"):
                    return
            except Exception:
                pass
            # Legacy CONNECTOR enum guard (does not exist in current python-pptx)
            try:
                if hasattr(MSO_SHAPE_TYPE, "CONNECTOR") and shape.shape_type == getattr(MSO_SHAPE_TYPE, "CONNECTOR"):
                    return
            except Exception:
                pass
            try:
                bbox = BBox.from_shape(shape)
            except Exception:
                bbox = BBox()
            # Full-bleed background image: treat as splash, not content image.
            if shape.shape_type == MSO_SHAPE_TYPE.PICTURE:
                w, h = bbox.width, bbox.height
                if w >= deck.slide_w - 1.0 and h >= deck.slide_h - 1.0:
                    sc.has_splash_image = True
                else:
                    sc.blocks.append(ImageBlock(counter.next(), bbox, "picture"))
                return

            if shape.has_table:
                tbl = shape.table
                headers = [c.text.strip() for c in tbl.rows[0].cells]
                rows = [[c.text.strip() for c in row.cells] for row in tbl.rows[1:]]
                sc.blocks.append(TableBlock(counter.next(), None, headers, rows, bbox))
                return

            if shape.has_text_frame and shape.text_frame.text.strip():
                tf = shape.text_frame
                for p in tf.paragraphs:
                    txt = p.text.strip()
                    if not txt or _is_noise(txt):
                        continue
                    r = p.runs[0] if p.runs else None
                    sc.blocks.append(
                        TextBlock(
                            idx=counter.next(),
                            text=txt,
                            bbox=bbox,
                            level=p.level,
                            font_size=round(r.font.size.pt, 1) if (r and r.font.size) else 12.0,
                            bold=bool(r and r.font.bold),
                            italic=bool(r and r.font.italic),
                            align=("LEFT" if not p.alignment else str(p.alignment)),
                        )
                    )

        for shape in slide.shapes:
            walk(shape)

        # Text always first (titles lead), then tables, then images; each group
        # in visual reading order.
        text_blocks = [
            b for b in sc.blocks
            if isinstance(b, TextBlock) or isinstance(b, TableBlock)
        ]
        image_blocks = [b for b in sc.blocks if isinstance(b, ImageBlock)]
        text_blocks.sort(key=lambda b: (b.bbox.top, b.bbox.left))
        image_blocks.sort(key=lambda b: (b.bbox.top, b.bbox.left))
        sc.blocks = text_blocks + image_blocks

        if include_notes:
            if slide.has_notes_slide:
                try:
                    notes_txt = slide.notes_slide.notes_text_frame.text.strip()
                    if notes_txt:
                        sc.notes = " ".join(notes_txt.split())
                except Exception:
                    pass

        deck.slides.append(sc)

    return deck


class _IdCounter:
    def __init__(self) -> None:
        self._n = 0

    def next(self) -> int:
        self._n += 1
        return self._n


def dump_json(deck: DeckContent, path: str) -> None:
    import json

    payload = {
        "source_path": deck.source_path,
        "slide_w": deck.slide_w,
        "slide_h": deck.slide_h,
        "slides": [dataclasses.asdict(s) for s in deck.slides],
    }
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)