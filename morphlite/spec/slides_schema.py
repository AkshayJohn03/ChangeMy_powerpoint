"""Typed slide-spec schema: the LLM output that a deterministic renderer consumes.

The LLM never draws; it emits a *spec*. A spec is model-readable, diff-able,
validatable, and — crucially — can be produced deterministically from a golden
deck (so our dataset becomes spec labels we can evaluate against).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Optional

# MorphLite archetypes (superset of the original 7; aliases for readability).
Archetype = Literal[
    "title", "agenda", "section_splitter", "content_columns",
    "card_grid", "metrics_hero", "process_flow", "comparison",
    "quote", "table", "timeline", "thank_you", "generic",
]

# Per-text element role inside an archetype slot.
ElementRole = Literal[
    "title", "subtitle", "section_eyebrow", "card_title", "card_body",
    "bullet", "metric_value", "metric_label", "step", "step_body",
    "quote", "attribution", "kicker", "caption",
]


@dataclass
class TextElement:
    role: ElementRole = "bullet"
    text: str = ""
    # Optional emphasis. Renderers decide exact treatment from role + tokens,
    # but these carry intent the LLM derived from the source.
    bold: bool = False
    size_pt: Optional[float] = None

    def snake_name(self) -> str:
        return f"{self.role}:{self.text[:28]}"


@dataclass
class CardElement:
    title: str = ""
    body: list[str] = field(default_factory=list)
    metric_value: Optional[str] = None
    metric_label: Optional[str] = None
    # Preserve a source image (by source ref) when the lang chain decides it's
    # a meaningful content image, not chrome.
    image_ref: Optional[str] = None


@dataclass
class StepElement:
    label: str = ""
    detail: str = ""
    index: int = 0


@dataclass
class TableElement:
    headers: list[str] = field(default_factory=list)
    rows: list[list[str]] = field(default_factory=list)
    title: str = ""
    caption: str = ""


@dataclass
class ImageElement:
    ref: str = ""  # key into a DeckSpec.images map, or URL
    alt: str = ""
    full_bleed: bool = False


@dataclass
class SlideSpec:
    # LLM-only fields describing intent -------------------------------------
    archetype: Archetype = "generic"
    title: str = ""
    subtitle: str = ""
    kicker: str = ""  # small brand eyebrow, e.g. "AKKODIS • SERVICE MANAGEMENT"
    notes: str = ""

    speech_act: str = ""  # what this slide must communicate
    audience: str = ""  # who it is for

    elements: list[CardElement] = field(default_factory=list)
    steps: list[StepElement] = field(default_factory=list)
    table: Optional[TableElement] = None
    images: list[ImageElement] = field(default_factory=list)
    quote: str = ""
    attribution: str = ""

    # Review aid (LLM self-annotation, not structural)
    source_slide: int = 0


@dataclass
class DeckSpec:
    brand: str = "akkodis"
    layout: str = "16:9"
    title: str = ""
    author: str = ""
    slides: list[SlideSpec] = field(default_factory=list)
    notes: list[dict] = field(default_factory=list)  # free form, e.g. warnings
    images: dict[str, str] = field(default_factory=dict)  # ref -> source or url

    @property
    def n_slides(self) -> int:
        return len(self.slides)


# Aliases that map historical MorphLite archetypes onto the LLM ones.
ARTHETYPE_ALIASES: dict[str, str] = {
    "title_slide": "title",
    "two_column": "content_columns",
    "three_card": "card_grid",
    "four_grid": "card_grid",
    "metrics_hero": "metrics_hero",
    "process_flow": "process_flow",
    "unknown_freeform": "generic",
}


def normalize_archetype(raw: str) -> str:
    r = (raw or "").strip().lower()
    if not r:
        return "generic"
    r = r.replace(" ", "_").replace("-", "_")
    if r in ARTHETYPE_ALIASES:
        return ARTHETYPE_ALIASES[r]
    if r.endswith("_slide"):
        r = r[:-6]
    known = {
        "title", "agenda", "section", "section_splitter",
        "content", "content_columns", "card_grid", "cards", "grid",
        "metrics_hero", "metrics", "process_flow", "process",
        "comparison", "quote", "table", "timeline", "thank_you", "closing",
        "generic",
    }
    return r if r in known else "generic"


def to_dict(deck: DeckSpec) -> dict:
    import dataclasses
    return dataclasses.asdict(deck)


def from_dict(data: dict) -> DeckSpec:
    slides = [SlideSpec(**s) for s in data.get("slides", [])]
    return DeckSpec(
        brand=data.get("brand", "akkodis"),
        layout=data.get("layout", "16:9"),
        title=data.get("title", ""),
        author=data.get("author", ""),
        slides=slides,
        notes=data.get("notes", []),
        images=data.get("images", {}),
    )