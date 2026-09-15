"""SpecBuilder: ContentModel -> DeckSpec via LLM (or heuristic fallback)."""
from __future__ import annotations

import json
import logging
from typing import Optional

from ..models.content_model import DeckContent
from ..pipeline.brand_profile import DEFAULT_PROFILE as BP
from ..spec.slides_schema import DeckSpec, SlideSpec
from .provider import BaseLLM, get_provider

logger = logging.getLogger(__name__)

_BRAND_BRIEF = (
    f"Brand: Akkodis (dark blue corporate)\n"
    f"Colors: dark={BP.dark_hex} gold={BP.gold_hex} white={BP.white_hex} card={BP.card_hex}\n"
    f"Fonts: heading={BP.heading_font} body={BP.body_font}\n"
    f"Slide size: 13.333 x 7.5 in (widescreen 16:9)\n"
)

_ARCHETYPES = """Archetypes (pick one per slide):
- title: cover/hero title
- agenda: table of contents
- section_splitter: section divider
- content_columns: 2-column bullets
- card_grid: 3-4 info cards
- metrics_hero: large KPI callouts
- process_flow: horizontal steps
- comparison: side-by-side contrast
- quote: large quote + attribution
- table: tabular data
- timeline: chronological steps
- thank_you: closing
- generic: fallback
"""

_SCHEMA_HINT = """Output JSON with this shape (omit empty fields):
{
  "brand": "akkodis",
  "slides": [
    {
      "archetype": "<archetype>",
      "title": "<slide title>",
      "subtitle": "<optional>",
      "kicker": "<eyebrow 2-4 words>",
      "source_slide": <1-based raw index>,
      "elements": [{"title": "", "body": [""]}],
      "steps": [{"label": "", "detail": "", "index": 0}],
      "notes": ""
    }
  ]
}"""


class SpecBuilder:
    def __init__(self, llm: Optional[BaseLLM] = None, provider_name: str = "", extra_exemplars: list[str] | None = None):
        self._llm = llm or get_provider(provider_name)
        self._extra = extra_exemplars or []

    def build(self, deck: DeckContent, few_shot: list[str] | None = None) -> DeckSpec:
        system = _BRAND_BRIEF + "\n" + _ARCHETYPES + "\n" + _SCHEMA_HINT + "\nRespond ONLY with JSON."
        user = "Raw deck content (one block per slide, visual order):\n" + deck.to_prompt()
        exemplars = few_shot or self._extra
        if exemplars:
            user = "\n\n".join(exemplars) + "\n\n" + user
        messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
        try:
            raw = self._llm.complete_json(messages, schema_hint=_SCHEMA_HINT)
        except Exception as exc:
            logger.warning("LLM failed (%s) -> heuristic", exc)
            return _heuristic(deck)
        try:
            if isinstance(raw, list):
                raw = {"brand": "akkodis", "slides": raw}
            spec = _from_raw(raw)
            if spec.slides:
                return spec
            raise ValueError("empty slides")
        except Exception as exc:
            logger.warning("LLM output invalid (%s) -> heuristic", exc)
            return _heuristic(deck)


def _from_raw(data: dict) -> DeckSpec:
    slides = []
    for s in data.get("slides", []):
        slides.append(SlideSpec(
            archetype=s.get("archetype", "generic"),
            title=s.get("title", ""),
            subtitle=s.get("subtitle", ""),
            kicker=s.get("kicker", ""),
            source_slide=int(s.get("source_slide", 0) or 0),
            notes=s.get("notes", ""),
            elements=_coerce_elements(s.get("elements", [])),
            steps=_coerce_steps(s.get("steps", [])),
        ))
    return DeckSpec(brand=data.get("brand", "akkodis"), slides=slides)


def _coerce_elements(raw):
    from ..spec.slides_schema import CardElement
    out = []
    for e in raw or []:
        if isinstance(e, dict):
            out.append(CardElement(title=e.get("title",""), body=e.get("body",[]) or ([e.get("text","")] if e.get("text") else [])))
        elif isinstance(e, str):
            out.append(CardElement(title=e[:40], body=[e]))
    return out


def _coerce_steps(raw):
    from ..spec.slides_schema import StepElement
    out = []
    for i, e in enumerate(raw or []):
        if isinstance(e, dict):
            out.append(StepElement(label=e.get("label","") or e.get("title",""), detail=e.get("detail",""), index=int(e.get("index", i))))
        elif isinstance(e, str):
            out.append(StepElement(label=e[:32], index=i))
    return out


def _heuristic(deck: DeckContent) -> DeckSpec:
    slides: list[SlideSpec] = []
    for s in deck.slides:
        # filter page-number artefacts and noise
        raw_blocks = [b.text.strip() for b in s.text_blocks if b.text.strip()]
        tb = [t for t in raw_blocks if not (len(t) <= 2 and t.isdigit())]
        if not tb:
            tb = raw_blocks
        low = " ".join(tb).lower()
        arch = "generic"
        if s.slide_no == 1 and len(deck.slides) > 1:
            arch = "title"
        elif "agenda" in low or "contents" in low:
            arch = "agenda"
        elif low.strip().endswith("thank you") or low.strip() == "thank you" or ("thank you" in low and len(tb) <= 3):
            arch = "thank_you"
        elif "case stud" in low and len(tb) <= 6:
            arch = "content_columns"
        elif any(k in low for k in ("sense","understand","decide","respond")) and len(tb) >= 6:
            arch = "process_flow"
        elif tb and any(k in low for k in ("sensor","camera","radar")) and "how does" in low:
            arch = "process_flow"
        from ..spec.slides_schema import CardElement, StepElement
        cards: list[CardElement] = []
        steps: list[StepElement] = []
        if arch == "process_flow":
            # steps are the short caps words + their following detail
            for i, t in enumerate(tb[1:]):
                if t.isupper() or len(t.split()) <= 3:
                    steps.append(StepElement(label=t[:32], index=len(steps)))
                elif steps:
                    steps[-1].detail = t[:80]
            if not steps:
                for i, t in enumerate(tb[1:7]):
                    steps.append(StepElement(label=t[:32], index=i))
        else:
            for t in tb[1:]:
                cards.append(CardElement(title=t[:70], body=[t]))
        slides.append(SlideSpec(archetype=arch, title=tb[0] if tb else "", source_slide=s.slide_no, elements=cards, steps=steps))
    return DeckSpec(slides=slides)
