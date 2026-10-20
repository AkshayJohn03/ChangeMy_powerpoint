"""BrandDNA: the validated, structured form of a brand guideline.

The engine never hardcodes a company's look (v1's fatal flaw — five class
attributes in builder.py). Everything downstream reads this profile. Profiles
are authored as YAML so a brand manager can edit them without code; PDF
guideline ingestion is an optional LLM-assisted path (extract_draft).
"""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, Field, field_validator

from ..engine.colorutil import normalize_hex

_BRANDS_DIR = Path(__file__).resolve().parent.parent.parent / "brands"

# canonical palette roles (avoid instance-level pydantic model_fields access)
PALETTE_ROLES = (
    "background", "surface", "surface_alt", "text_primary", "text_muted",
    "accent_primary", "accent_secondary", "success", "warning", "danger", "link",
)


class BrandColor(BaseModel):
    hex: str
    usage: str = ""

    @field_validator("hex")
    @classmethod
    def _hex(cls, v: str) -> str:
        return normalize_hex(v)


class Palette(BaseModel):
    background: BrandColor
    surface: BrandColor
    surface_alt: BrandColor
    text_primary: BrandColor
    text_muted: BrandColor
    accent_primary: BrandColor
    accent_secondary: BrandColor
    success: BrandColor
    warning: BrandColor
    danger: BrandColor
    link: BrandColor


class FontSpec(BaseModel):
    family: str
    weight: str = "regular"  # regular | bold | semibold
    fallbacks: list[str] = Field(default_factory=list)


class Typography(BaseModel):
    heading: FontSpec
    body: FontSpec


class Tone(BaseModel):
    voice: str = ""
    formality: float = 0.5  # 0 casual .. 1 formal
    glossary: dict[str, str] = Field(default_factory=dict)
    banned_words: list[str] = Field(default_factory=list)


class Rules(BaseModel):
    min_contrast: float = 4.5
    fit_slack: float = 0.10  # tolerated overflow before FitGuard intervenes
    preserve_display_fonts: list[str] = Field(default_factory=list)
    rewrite_copy: bool = False  # opt-in LLM copy rewriting


class BrandDNA(BaseModel):
    name: str
    palette: Palette
    typography: Typography
    tone: Tone = Tone()
    rules: Rules = Rules()

    def accent_candidates(self) -> list[tuple[str, str]]:
        """(hex, role) candidates for accent-role colors, nearest-match order."""
        p = self.palette
        return [
            (p.accent_primary.hex, "accent_primary"),
            (p.accent_secondary.hex, "accent_secondary"),
            (p.success.hex, "success"),
            (p.warning.hex, "warning"),
            (p.danger.hex, "danger"),
            (p.link.hex, "link"),
        ]

    def surface_candidates(self) -> list[tuple[str, str]]:
        p = self.palette
        return [
            (p.surface.hex, "surface"),
            (p.surface_alt.hex, "surface_alt"),
            (p.background.hex, "background"),
        ]

    @classmethod
    def from_dict(cls, data: dict) -> BrandDNA:
        return cls.model_validate(data)

    @classmethod
    def from_yaml(cls, text: str) -> BrandDNA:
        return cls.from_dict(yaml.safe_load(text))

    @classmethod
    def load(cls, name_or_path: str) -> BrandDNA:
        """Load a bundled brand by name or any YAML/JSON file path."""
        p = Path(name_or_path)
        if not p.exists():
            p = _BRANDS_DIR / f"{name_or_path}.yaml"
        if not p.exists():
            raise FileNotFoundError(f"brand profile not found: {name_or_path}")
        return cls.from_dict(yaml.safe_load(p.read_text(encoding="utf-8")))


def _extract_pdf_text(pdf_bytes: bytes) -> str:
    import io

    try:
        import pdfplumber  # optional dependency, guarded
    except ImportError as e:
        raise RuntimeError("pdfplumber is required for PDF guideline extraction") from e
    chunks: list[str] = []
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages[:30]:
            chunks.append(page.extract_text() or "")
    return "\n".join(chunks)


_EXTRACTION_PROMPT = (
    "Extract a brand guideline as YAML matching this schema: "
    "name, palette{background,surface,surface_alt,text_primary,text_muted,"
    "accent_primary,accent_secondary,success,warning,danger,link} each {hex,usage}, "
    "typography{heading{family,weight},body{family,weight}}, tone{voice,formality}. "
    "Only include colors explicitly stated in the text. Output YAML only.\n\n"
)


async def extract_draft_async(pdf_bytes: bytes, llm) -> BrandDNA | None:
    """Async variant for FastAPI endpoints."""
    if llm is None:
        return None
    text = _extract_pdf_text(pdf_bytes)
    raw = await llm.complete(_EXTRACTION_PROMPT + text)
    return _parse_yaml_snippet(raw)


def extract_draft(pdf_bytes: bytes, llm) -> BrandDNA | None:
    """Draft a BrandDNA from a brand-guideline PDF via an LLMClient (CLI use).

    Optional path: returns None when no LLM is configured — the engine is
    fully functional with hand-edited YAML (see V2_DESIGN.md non-goals).
    """
    if llm is None:
        return None
    import asyncio

    return asyncio.run(extract_draft_async(pdf_bytes, llm))


def _parse_yaml_snippet(text: str) -> BrandDNA | None:
    """Parse an LLM-produced YAML snippet defensively (strip code fences)."""
    cleaned = "\n".join(
        ln for ln in text.splitlines() if not ln.strip().startswith("```")
    )
    try:
        data = yaml.safe_load(cleaned)
        if isinstance(data, dict) and "palette" in data:
            return BrandDNA.from_dict(data)
    except Exception:
        pass
    return None
