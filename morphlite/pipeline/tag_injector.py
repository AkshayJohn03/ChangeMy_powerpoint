"""Programmatic tag injector for Brand_guideline_Akkodis.pptx.

Creates `data/brand_template/Brand_guideline_Akkodis_tagged.pptx` by:
1. Purging helper guidance text frames ("Font Guidance", "Do not change the template").
2. Injecting docxtemplater-style tags ({title}, {subtitle}, {bullets_text}, {agenda_1}..{agenda_4}, {card_1}..{card_4})
   into the exact vector shapes while preserving all font styling, sizes, colors, and master layers.
"""
from __future__ import annotations

import os
from pathlib import Path
import pptx

SOURCE_TEMPLATE = Path("data/brand_template/Brand_guideline_Akkodis.pptx")
TARGET_TAGGED = Path("data/brand_template/Brand_guideline_Akkodis_tagged.pptx")

def is_guidance_text(text: str) -> bool:
    t = text.lower()
    return "font guidance" in t or "do not change the template" in t or "do not change the font" in t

def clean_and_tag_template(source_path: Path = SOURCE_TEMPLATE, target_path: Path = TARGET_TAGGED) -> Path:
    prs = pptx.Presentation(str(source_path))
    
    for slide_idx, slide in enumerate(prs.slides):
        shapes_to_delete = []
        
        # 1. Identify guidance shapes to remove
        for shape in slide.shapes:
            if shape.has_text_frame:
                txt = shape.text_frame.text.strip()
                if is_guidance_text(txt):
                    shapes_to_delete.append(shape)

        for s in shapes_to_delete:
            sp = s._element
            sp.getparent().remove(sp)

        # 2. Tag specific shapes per slide layout
        # Slide 0: Deck Title
        if slide_idx == 0:
            for s in slide.shapes:
                if s.has_text_frame:
                    txt = s.text_frame.text.strip()
                    if "Global Tech Powerhouse" in txt:
                        # Find paragraph with runs and replace
                        for p in s.text_frame.paragraphs:
                            if "Global Tech Powerhouse" in p.text:
                                if p.runs:
                                    p.runs[0].text = "{title}"
                                    for r in p.runs[1:]:
                                        r.text = ""
                                else:
                                    p.text = "{title}"

        # Slide 1: Agenda Slide
        elif slide_idx == 1:
            agenda_counter = 1
            for s in slide.shapes:
                if s.has_text_frame:
                    txt = s.text_frame.text.strip()
                    if "Agenda" in txt:
                        p = s.text_frame.paragraphs[0]
                        if p.runs:
                            p.runs[0].text = "{title}"
                    elif txt in ("Corporate Overview", "Akkodis – Microsoft Partnership", "Service offering", "Case studies") or (len(txt) > 3 and not txt.isdigit()):
                        p = s.text_frame.paragraphs[0]
                        if p.runs:
                            p.runs[0].text = f"{{agenda_{agenda_counter}}}"
                            for r in p.runs[1:]:
                                r.text = ""
                            agenda_counter += 1

        # Slide 2: Who We Are / Corporate Profile
        elif slide_idx == 2:
            card_idx = 1
            for s in slide.shapes:
                if s.has_text_frame:
                    txt = s.text_frame.text.strip()
                    if "Who We Are" in txt:
                        p = s.text_frame.paragraphs[0]
                        if p.runs:
                            p.runs[0].text = "{title}"
                    elif len(txt) > 2 and not txt.isdigit():
                        p = s.text_frame.paragraphs[0]
                        if p.runs:
                            p.runs[0].text = f"{{card_{card_idx}}}"
                            for r in p.runs[1:]:
                                r.text = ""
                            card_idx += 1

        # Generic / Other Slides: Tag Title + Body / Bullets
        else:
            tagged_title = False
            for s in slide.shapes:
                if s.has_text_frame:
                    txt = s.text_frame.text.strip()
                    if not tagged_title and s.top < pptx.util.Inches(2.0) and len(txt) > 0:
                        p = s.text_frame.paragraphs[0]
                        if p.runs:
                            p.runs[0].text = "{title}"
                            for r in p.runs[1:]:
                                r.text = ""
                        tagged_title = True
                    elif len(txt) > 0 and "{title}" not in txt:
                        p = s.text_frame.paragraphs[0]
                        if p.runs:
                            p.runs[0].text = "{bullets_text}"
                            for r in p.runs[1:]:
                                r.text = ""

    target_path.parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(target_path))
    print(f"Successfully created tagged template at: {target_path} ({target_path.stat().st_size} bytes)")
    return target_path

if __name__ == "__main__":
    clean_and_tag_template()
