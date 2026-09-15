"""Deterministic renderer: DeckSpec -> native .pptx with Akkodis tokens."""
from __future__ import annotations
from pathlib import Path
import pptx
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN
from ..pipeline.brand_profile import DEFAULT_PROFILE as BP
from ..spec.slides_schema import DeckSpec, SlideSpec
from .fit import shrink_to_fit

def _rgb(h: str) -> RGBColor:
    h = h.lstrip("#")
    return RGBColor(int(h[0:2],16), int(h[2:4],16), int(h[4:6],16))

W, H = 13.333, 7.5
PAD, GAP = 0.35, 0.25

def _card_widths(n: int):
    avail = W - 2*PAD - (n-1)*GAP
    return avail/max(n,1), GAP

def _shape(slide, st, l, t, w, h, fill, line=None):
    shp = slide.shapes.add_shape(st, Inches(l), Inches(t), Inches(w), Inches(h))
    shp.fill.solid(); shp.fill.fore_color.rgb = _rgb(fill)
    if line: shp.line.color.rgb = _rgb(line)
    else: shp.line.fill.background()
    return shp

def _tbox(slide, l, t, w, h, text, font, size, color, bold=False, align=PP_ALIGN.LEFT):
    tb = slide.shapes.add_textbox(Inches(l), Inches(t), Inches(w), Inches(h))
    tf = tb.text_frame; tf.word_wrap = True
    p = tf.paragraphs[0]; p.alignment = align
    p.text = text; p.font.name = font
    p.font.size = Pt(int(shrink_to_fit(font, size, text, w, h)))
    p.font.color.rgb = color; p.font.bold = bold
    return tb

def _bullets(slide, l, t, w, h, items, font, size=11, color=None):
    color = color or _rgb(BP.white_hex)
    tb = slide.shapes.add_textbox(Inches(l), Inches(t), Inches(w), Inches(h))
    tf = tb.text_frame; tf.word_wrap = True
    for i, it in enumerate(items):
        p = tf.paragraphs[0] if i==0 else tf.add_paragraph()
        p.text = f"\u2022  {it}"; p.font.name = font
        p.font.size = Pt(int(shrink_to_fit(font, size, it, w, h/max(len(items),1))))
        p.font.color.rgb = color

def _title(slide, spec):
    bg = slide.background; bg.fill.solid(); bg.fill.fore_color.rgb = _rgb(BP.dark_hex)
    _tbox(slide, 1.0, 1.4, 11.3, 1.3, spec.title, BP.heading_font, 36, _rgb(BP.gold_hex), True)
    if spec.subtitle: _tbox(slide, 1.0, 2.9, 11.3, 0.7, spec.subtitle, BP.body_font, 16, _rgb(BP.white_hex))
    elif spec.elements: _tbox(slide, 1.0, 2.9, 11.3, 0.7, spec.elements[0].title, BP.body_font, 16, _rgb(BP.white_hex))
    if spec.kicker: _tbox(slide, 1.0, 1.0, 6.0, 0.3, spec.kicker, BP.body_font, 10, _rgb(BP.white_hex))
    # show remaining elements as small footer pills if title slide had extra content
    if len(spec.elements) > 1:
        extra = [e.title for e in spec.elements[1:7]]
        _bullets(slide, 1.0, 4.2, 11.3, 2.5, extra, BP.body_font, 11)

def _agenda(slide, spec):
    bg = slide.background; bg.fill.solid(); bg.fill.fore_color.rgb = _rgb(BP.dark_hex)
    _tbox(slide, 0.8, 0.4, 8.0, 0.8, spec.title or "Agenda", BP.heading_font, 28, _rgb(BP.gold_hex), True)
    items = [e.title for e in spec.elements if e.title] or [e.body[0] for e in spec.elements if e.body]
    _bullets(slide, 0.8, 1.6, 11.5, 5.5, items, BP.body_font, 14)

def _section(slide, spec):
    bg = slide.background; bg.fill.solid(); bg.fill.fore_color.rgb = _rgb(BP.dark_hex)
    _tbox(slide, 1.0, 2.5, 11.3, 1.5, spec.title, BP.heading_font, 36, _rgb(BP.gold_hex), True)
    if spec.subtitle: _tbox(slide, 1.0, 4.3, 11.3, 0.8, spec.subtitle, BP.body_font, 14, _rgb(BP.white_hex))
    s = _shape(slide, MSO_SHAPE.RECTANGLE, 1.0, 4.1, 3.0, 0.04, BP.gold_hex)

def _content_cols(slide, spec):
    bg = slide.background; bg.fill.solid(); bg.fill.fore_color.rgb = _rgb(BP.dark_hex)
    _tbox(slide, 0.8, 0.4, 10.0, 0.8, spec.title, BP.heading_font, 28, _rgb(BP.gold_hex), True)
    bullets = [e.body[0] if e.body else e.title for e in spec.elements]
    # split into two columns if many bullets, no truncation
    if len(bullets) > 8:
        mid = (len(bullets)+1)//2
        _bullets(slide, 0.8, 1.6, 5.6, 5.5, bullets[:mid], BP.body_font, 11)
        _bullets(slide, 6.9, 1.6, 5.6, 5.5, bullets[mid:], BP.body_font, 11)
    else:
        _bullets(slide, 0.8, 1.6, 11.7, 5.5, bullets, BP.body_font, 12)

def _card_grid(slide, spec):
    bg = slide.background; bg.fill.solid(); bg.fill.fore_color.rgb = _rgb(BP.dark_hex)
    _tbox(slide, 0.8, 0.4, 10.0, 0.8, spec.title, BP.heading_font, 28, _rgb(BP.gold_hex), True)
    cards = spec.elements[:5]; cw, gap = _card_widths(len(cards))
    for i, c in enumerate(cards):
        x = PAD + i*(cw+gap)
        _shape(slide, MSO_SHAPE.ROUNDED_RECTANGLE, x, 1.7, cw, 4.8, BP.card_hex, BP.gold_hex)
        _tbox(slide, x+0.25, 2.0, cw-0.5, 0.6, c.title, BP.heading_font, 16, _rgb(BP.gold_hex), True)
        body = "\n".join(c.body)
        if body: _tbox(slide, x+0.25, 2.7, cw-0.5, 3.5, body, BP.body_font, 11, _rgb(BP.white_hex))

def _metrics(slide, spec):
    bg = slide.background; bg.fill.solid(); bg.fill.fore_color.rgb = _rgb(BP.dark_hex)
    _tbox(slide, 0.8, 0.4, 10.0, 0.8, spec.title, BP.heading_font, 28, _rgb(BP.gold_hex), True)
    cards = spec.elements[:4]; cw, gap = _card_widths(len(cards))
    for i, c in enumerate(cards):
        x = PAD + i*(cw+gap)
        _shape(slide, MSO_SHAPE.ROUNDED_RECTANGLE, x, 1.7, cw, 4.8, BP.card_hex, BP.gold_hex)
        _tbox(slide, x+0.3, 2.3, cw-0.6, 1.2, c.title, BP.heading_font, 36, _rgb(BP.gold_hex), True)

def _process(slide, spec):
    bg = slide.background; bg.fill.solid(); bg.fill.fore_color.rgb = _rgb(BP.dark_hex)
    _tbox(slide, 0.8, 0.4, 10.0, 0.8, spec.title, BP.heading_font, 28, _rgb(BP.gold_hex), True)
    n = min(len(spec.steps),6); sw = (W-1.6)/max(n,1)-0.15
    for i, st in enumerate(spec.steps[:n]):
        x = 0.8 + i*(sw+0.15)
        shp = _shape(slide, MSO_SHAPE.CHEVRON, x, 2.0, sw, 4.0, BP.card_hex, BP.gold_hex)
        tf = shp.text_frame; tf.word_wrap=True
        p=tf.paragraphs[0]; p.alignment=PP_ALIGN.CENTER; p.text=st.label
        p.font.name=BP.body_font; p.font.size=Pt(12); p.font.color.rgb=_rgb(BP.white_hex)

def _generic(slide, spec):
    bg = slide.background; bg.fill.solid(); bg.fill.fore_color.rgb = _rgb(BP.dark_hex)
    _tbox(slide, 0.8, 0.4, 10.0, 0.8, spec.title, BP.heading_font, 28, _rgb(BP.gold_hex), True)
    bullets = [e.body[0] if e.body else e.title for e in spec.elements]
    if not bullets and spec.subtitle:
        bullets = [spec.subtitle]
    if len(bullets) > 9:
        mid = (len(bullets)+1)//2
        _bullets(slide, 0.8, 1.5, 5.7, 5.5, bullets[:mid], BP.body_font, 10)
        _bullets(slide, 6.8, 1.5, 5.7, 5.5, bullets[mid:], BP.body_font, 10)
    else:
        _bullets(slide, 0.8, 1.5, 11.7, 5.5, bullets, BP.body_font, 11)

_MAP = {"title":_title,"agenda":_agenda,"section_splitter":_section,"content_columns":_content_cols,"card_grid":_card_grid,"metrics_hero":_metrics,"process_flow":_process}

class BrandRenderer:
    def __init__(self, profile=None):
        self.prs = pptx.Presentation(); self.prs.slide_width=Inches(W); self.prs.slide_height=Inches(H)
    def render(self, spec: DeckSpec, output_path: str | None = None) -> str:
        for s in spec.slides:
            blank = self.prs.slide_layouts[6]
            slide = self.prs.slides.add_slide(blank)
            fn = _MAP.get(s.archetype, _generic)
            fn(slide, s)
        out = output_path or "_brandmorph_out.pptx"
        self.prs.save(out); return out
    def save(self, path: str): self.prs.save(path)
