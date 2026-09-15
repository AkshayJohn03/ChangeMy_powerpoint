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
from pptx.util import Pt

TAG_RE = re.compile(r"\{([#\/$%~]?)([a-zA-Z0-9_\.]+)\}")

DEFAULT_TEMPLATE_PATH = "data/brand_template/Brand_guideline_Akkodis_tagged.pptx"
if not os.path.exists(DEFAULT_TEMPLATE_PATH):
    DEFAULT_TEMPLATE_PATH = "data/brand_template/Brand_guideline_Akkodis.pptx"

def _find_tags(shape) -> list[str]:
    if not shape.has_text_frame:
        return []
    text = shape.text_frame.text
    return TAG_RE.findall(text)

def _replace_tag_in_shape(shape, tag: str, value: str):
    """Replace {tag} placeholder while preserving first-run style."""
    if not shape.has_text_frame:
        return False
    tf = shape.text_frame
    full = tf.text
    if f"{{{tag}}}" not in full and f"{{{tag}" not in full:
        return False
    
    # preserve style from first run
    template_run = None
    for p in tf.paragraphs:
        if p.runs:
            template_run = p.runs[0]
            break
            
    # clear and rewrite
    for p in list(tf.paragraphs[1:]):
        p._p.getparent().remove(p._p)
    p0 = tf.paragraphs[0]
    for r in list(p0.runs):
        r._r.getparent().remove(r._r)
        
    r = p0.add_run()
    r.text = full.replace(f"{{{tag}}}", value).replace(f"{{#{tag}}}", value).replace(f"{{/{tag}}}", "")
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
            if "{" in r.text and "}" in r.text:
                r.text = re.sub(r"\{[#\/$%~]?[a-zA-Z0-9_\.]+\}", "", r.text).strip()

class TemplateTagPipeline:
    """Tag-based filler. Template slides contain {placeholders}."""

    def __init__(self, template_path: str = DEFAULT_TEMPLATE_PATH):
        if template_path == "data/brand_template/Brand_guideline_Akkodis.pptx" and os.path.exists("data/brand_template/Brand_guideline_Akkodis_tagged.pptx"):
            template_path = "data/brand_template/Brand_guideline_Akkodis_tagged.pptx"
            
        self.template_path = template_path
        self.tpl = pptx.Presentation(template_path)
        # index tags per slide for diagnostics
        self.slide_tags = {}
        for i, slide in enumerate(self.tpl.slides):
            tags = []
            for shape in slide.shapes:
                tags.extend(_find_tags(shape))
            self.slide_tags[i] = tags

    def process(self, raw_path: str, output_path: str | None = None, data: dict | None = None) -> dict:
        from ..models.content_model import extract_deck
        from .template_filler import _duplicate_slide

        deck = extract_deck(raw_path)
        prs = pptx.Presentation(self.template_path)
        template_len = len(prs.slides)

        # Ensure we have enough slides: duplicate generic_content (index 3) for overflow
        generic_idx = 3 if template_len > 3 else 0
        while len(prs.slides) < len(deck.slides):
            _duplicate_slide(prs, generic_idx)

        # Now fill each slide's tags with deck content
        slide_payloads = self._deck_to_payloads(deck)

        for si, payload in enumerate(slide_payloads):
            if si >= len(prs.slides):
                break
            slide = prs.slides[si]
            for shape in list(slide.shapes):
                if not shape.has_text_frame:
                    continue
                # replace each tag found
                txt = shape.text_frame.text
                for m in TAG_RE.finditer(txt):
                    prefix, tag = m.groups()
                    if prefix in ("#", "/", "$", "%", "~"):
                        continue
                    if tag in payload:
                        _replace_tag_in_shape(shape, tag, str(payload[tag]))

        # Handle bullets expanding
        for si, payload in enumerate(slide_payloads):
            if "bullets" in payload and isinstance(payload["bullets"], list):
                slide = prs.slides[si]
                bullets_text = "\n".join(f"• {b}" for b in payload["bullets"])
                for shape in slide.shapes:
                    if shape.has_text_frame:
                        if "{bullets}" in shape.text_frame.text:
                            _replace_tag_in_shape(shape, "bullets", bullets_text)
                        if "{bullets_text}" in shape.text_frame.text:
                            _replace_tag_in_shape(shape, "bullets_text", bullets_text)

        # Final pass: Purge any remaining unreplaced {tag} placeholders
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
