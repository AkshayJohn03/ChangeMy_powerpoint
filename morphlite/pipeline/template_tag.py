"""Template-tag pipeline — docxtemplater-style for python-pptx.

Inspired by open-xml-templating/docxtemplater (3.6k★) + ppt-master's
edit-native-pptx contract: put tags directly in the brand template,
code just supplies JSON. Zero bbox math, 100% native fidelity.
"""
from __future__ import annotations

import copy
import hashlib
import os
import re
import uuid
from pathlib import Path

import pptx
from pptx.oxml.ns import qn
from pptx.util import Pt

TAG_RE = re.compile(r"\{([#\/$%~]?)([a-zA-Z0-9_\.]+)\}")

AGENDA_TITLE_KWS = ("agenda", "contents", "outline", "table of contents")
THANK_TITLE_KWS = ("thank", "questions", "q&a")
_CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")


def select_template_slide(slide_content, slide_idx: int, total_slides: int, template_len: int) -> int:
    """Archetype + capacity router: raw slide -> best template slide index.

    Order: cover -> agenda -> thank-you/closing -> case study -> section
    splitter -> KPI/card grid -> default content. The KPI grid only fires
    for genuinely label-dense slides (no sentence-length bodies) so mixed
    bullet+diagram slides stay on content layouts.
    """
    blocks = [b for b in slide_content.text_blocks if b.text.strip()]
    title = blocks[0].text.strip() if blocks else ""
    low_title = title.lower()
    all_low = " ".join(b.text.lower() for b in blocks[:14])
    max_font = max(((b.font_size or 0.0) for b in blocks), default=0.0)
    short_blocks = [b for b in blocks if len(b.text.strip()) <= 38]
    long_blocks = [b for b in blocks if len(b.text.strip()) > 30 and len(b.text.strip().split()) >= 5]

    if slide_idx == 0:
        return 0
    if any(k in low_title for k in AGENDA_TITLE_KWS):
        return 1 if template_len > 1 else 0
    last_slide_thank = slide_idx == total_slides - 1 and (
        len(blocks) <= 3 or any(k in b.text.lower() for k in THANK_TITLE_KWS for b in blocks)
    )
    if any(k in low_title for k in THANK_TITLE_KWS) or last_slide_thank:
        return min(9, template_len - 1)
    if "case stud" in all_low or ("challenge" in all_low and "solution" in all_low):
        return 6 if template_len > 6 else 3
    if len(blocks) <= 2 and max_font >= 24:
        return 5 if template_len > 5 else 3
    if len(short_blocks) >= 8 and len(long_blocks) <= 1:
        return 2 if template_len > 2 else 3
    return 3 if template_len > 3 else 0


def _clean_text(t: str) -> str:
    """Remove control chars (VT etc.) and OOXML _xHHHH_ escapes, collapse spaces."""
    t = _CONTROL_RE.sub(" ", t)
    t = re.sub(r"_x[0-9A-Fa-f]{4}_", " ", t)
    t = re.sub(r"[ \t]+", " ", t)
    return t

DEFAULT_TEMPLATE_PATH = "data/brand_template/Akkodis_Sanitized_Master_Lite.pptx"
if not os.path.exists(DEFAULT_TEMPLATE_PATH):
    DEFAULT_TEMPLATE_PATH = "data/brand_template/Brand_guideline_Akkodis_tagged.pptx"
if not os.path.exists(DEFAULT_TEMPLATE_PATH):
    DEFAULT_TEMPLATE_PATH = "data/brand_template/Brand_guideline_Akkodis.pptx"

def _find_tags(shape) -> list[str]:
    if not shape.has_text_frame:
        return []
    text = shape.text_frame.text
    return TAG_RE.findall(text)

def _replace_tag_in_shape(shape, tag: str, value: str):
    """Replace {tag} placeholder while preserving first-run style.

    Control chars (VT) and _xHHHH_ escapes are cleaned first so python-pptx
    cannot round-trip them into literal '_x000B_' junk in the output.
    """
    if not shape.has_text_frame:
        return False
    tf = shape.text_frame
    full = _clean_text(tf.text)
    if f"{{{tag}}}" not in full and f"{{{tag}" not in full:
        return False
    value = _clean_text(str(value))
    
    # preserve style from first run
    template_run = None
    for p in tf.paragraphs:
        if p.runs:
            template_run = p.runs[0]
            break
            
    # clear and rewrite (remove runs AND stray <a:br/> so no leading VT remains)
    for p in list(tf.paragraphs[1:]):
        p._p.getparent().remove(p._p)
    p0 = tf.paragraphs[0]
    for child in list(p0._p):
        if child.tag != qn("a:pPr"):
            p0._p.remove(child)
        
    r = p0.add_run()
    r.text = full.replace(f"{{{tag}}}", value).replace(f"{{#{tag}}}", value).replace(f"{{/{tag}}}", "").strip()
    if template_run:
        if template_run.font.name: r.font.name = template_run.font.name
        if template_run.font.size: r.font.size = template_run.font.size
        try:
            if template_run.font.color.rgb: r.font.color.rgb = template_run.font.color.rgb
        except: pass
        r.font.bold = template_run.font.bold
        r.font.italic = template_run.font.italic
    return True

def _purge_unreplaced_tags_in_shape(shape):
    """Clear any remaining {tag} placeholders so no raw template markers appear."""
    if not shape.has_text_frame:
        return
    tf = shape.text_frame
    for p in tf.paragraphs:
        for r in p.runs:
            cleaned = _clean_text(r.text)
            if cleaned != r.text:
                r.text = cleaned
            if "{" in r.text and "}" in r.text:
                r.text = re.sub(r"\{[#\/$%~]?[a-zA-Z0-9_\.]+\}", "", r.text).strip()
        # empty paragraph -> drop stray line-break elements (avoids leading VT junk)
        if not "".join(r.text for r in p.runs).strip():
            for br in p._p.findall(qn("a:br")):
                p._p.remove(br)

class TemplateTagPipeline:
    """Tag-based filler. Template slides contain {placeholders}."""

    def __init__(self, template_path: str = DEFAULT_TEMPLATE_PATH):
        if template_path == "data/brand_template/Brand_guideline_Akkodis.pptx":
            for preferred in (
                "data/brand_template/Akkodis_Sanitized_Master_Lite.pptx",
                "data/brand_template/Brand_guideline_Akkodis_tagged.pptx",
            ):
                if os.path.exists(preferred):
                    template_path = preferred
                    break
            
        self.template_path = template_path
        self.tpl = pptx.Presentation(template_path)
        # index tags per slide for diagnostics
        self.slide_tags = {}
        for i, slide in enumerate(self.tpl.slides):
            tags = []
            for shape in slide.shapes:
                tags.extend(_find_tags(shape))
            self.slide_tags[i] = tags

    def _select_template_slide(self, slide_content, slide_idx: int, total_slides: int, template_len: int) -> int:
        return select_template_slide(slide_content, slide_idx, total_slides, template_len)

    def process(self, raw_path: str, output_path: str | None = None, data: dict | None = None) -> dict:
        from ..models.content_model import extract_deck
        from .template_filler import _duplicate_slide, _remove_first_n_slides

        deck = extract_deck(raw_path)
        prs = pptx.Presentation(self.template_path)
        template_len = len(prs.slides)

        slide_payloads = self._deck_to_payloads(deck)

        # Archetype + capacity routing: raw slide -> best template slide
        chosen = [
            self._select_template_slide(s, si, len(deck.slides), template_len)
            for si, s in enumerate(deck.slides)
        ]

        # Duplicate chosen template slides (appended after originals -> raw order preserved)
        for tpl_idx in chosen:
            _duplicate_slide(prs, tpl_idx)

        # Drop the original template slides -> only the duplicated, routed slides remain
        _remove_first_n_slides(prs, template_len)

        # Fill each routed slide's tags with its raw-slide payload
        for si, payload in enumerate(slide_payloads):
            if si >= len(prs.slides):
                break
            slide = prs.slides[si]
            if chosen[si] == min(9, template_len - 1) and "thank" not in str(payload.get("title", "")).lower():
                payload["title"] = "Thank You"
            for shape in list(slide.shapes):
                if not shape.has_text_frame:
                    continue
                txt = shape.text_frame.text
                for m in TAG_RE.finditer(txt):
                    prefix, tag = m.groups()
                    if prefix in ("#", "/", "$", "%", "~"):
                        continue
                    if tag in payload:
                        _replace_tag_in_shape(shape, tag, str(payload[tag]))

        # Handle bullets expanding
        for si, payload in enumerate(slide_payloads):
            if si >= len(prs.slides):
                break
            if "bullets" in payload and isinstance(payload["bullets"], list):
                slide = prs.slides[si]
                bullets_text = "\n".join(f"• {b}" for b in payload["bullets"])
                for shape in slide.shapes:
                    if shape.has_text_frame:
                        if "{bullets}" in shape.text_frame.text:
                            _replace_tag_in_shape(shape, "bullets", bullets_text)
                        if "{bullets_text}" in shape.text_frame.text:
                            _replace_tag_in_shape(shape, "bullets_text", bullets_text)

        # Final pass: purge any remaining unreplaced {tag} placeholders
        for slide in prs.slides:
            for shape in slide.shapes:
                _purge_unreplaced_tags_in_shape(shape)

        out = output_path or f"_tag_out_{uuid.uuid4().hex[:6]}.pptx"
        prs.save(out)
        return {
            "n_slides": len(prs.slides),
            "n_raw": len(deck.slides),
            "output": out,
            "slide_tags": self.slide_tags,
            "routing": [{"raw_slide": i + 1, "template_slide": t} for i, t in enumerate(chosen)],
            "payload_sample": slide_payloads[0] if slide_payloads else {},
            "hash": hashlib.sha256(Path(out).read_bytes()).hexdigest()[:12],
        }

    def _deck_to_payloads(self, deck) -> list[dict]:
        payloads = []
        for s in deck.slides:
            tb = [b.text for b in s.text_blocks if b.text.strip() and not (len(b.text.strip()) <= 2 and b.text.strip().isdigit())]
            if not tb:
                tb = [b.text for b in s.text_blocks]
            title = tb[0] if tb else ""
            bullets = tb[1:] if len(tb) > 1 else []
            
            p_dict = {
                "title": title,
                "subtitle": bullets[0] if bullets else "",
                "kicker": "AKKODIS • BRANDED",
                "bullets": bullets,
                "bullets_text": "\n".join(bullets),
                "cards": [{"title": b[:40], "body": b} for b in bullets[:6]],
            }
            for idx, b in enumerate(bullets):
                p_dict[f"agenda_{idx + 1}"] = b
                p_dict[f"card_{idx + 1}"] = b

            payloads.append(p_dict)
        return payloads
