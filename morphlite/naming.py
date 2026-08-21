"""Filename normalization and role detection for raw/branded PPTX pairing.

Convention observed in the dataset:
    "<name> raw.pptx"  <->  "<name>.pptx"          (explicit suffix, Category A)
    "Raw\\<name>.pptx" <->  "Updated\\<name> v1.pptx" (folder convention)
Version markers (v1, v1.1, v2) and stray trailing dots/spaces are ignored when
computing the canonical pairing key.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

_RAW_TOKEN = re.compile(r"^raw$", re.IGNORECASE)
_VERSION_TOKEN = re.compile(r"^v\d+(\.\d+)*$", re.IGNORECASE)

# Roles assigned to individual files before pairing.
ROLE_RAW = "raw"
ROLE_CLEAN = "clean"
ROLE_TEMPLATE = "template"


@dataclass(frozen=True)
class NameInfo:
    key: str                 # canonical pairing key
    had_raw_marker: bool     # filename contained a trailing "raw" marker
    had_version_token: bool  # filename carried an explicit version token (v1, v1.1, ...)
    stripped_tokens: list    # tokens removed from the tail


def _fold(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = text.replace("\ufffd", " ")           # mojibake replacement char
    text = re.sub(r"[\u2013\u2014]", "-", text)  # en/em dash variants
    return text.lower()


def normalize_name(stem: str) -> NameInfo:
    """Normalize a filename stem into a canonical pairing key."""
    folded = _fold(stem)
    tokens = [t for t in re.split(r"\s+", folded.strip()) if t]

    stripped: list[str] = []
    while tokens:
        last = tokens[-1].strip(".")
        if last == "":
            tokens.pop()
            stripped.append(".")
            continue
        if _RAW_TOKEN.match(last) or _VERSION_TOKEN.match(last):
            tokens.pop()
            stripped.append(last)
            continue
        break

    return NameInfo(
        key=" ".join(tokens),
        had_raw_marker=any(_RAW_TOKEN.match(t) for t in stripped),
        had_version_token=any(_VERSION_TOKEN.match(t) for t in stripped),
        stripped_tokens=list(reversed(stripped)),
    )


def detect_template(path: Path, template_hints, template_exact) -> bool:
    name = path.name.lower()
    stem_key = normalize_name(path.stem).key
    if path.name.lower() in {t.lower() for t in template_exact}:
        return True
    return any(hint in name or hint in stem_key for hint in template_hints)


def folder_role(path: Path, raw_folder_names, clean_folder_names) -> str | None:
    """Role implied by the immediate parent folder name, if any."""
    parent = path.parent.name.strip().lower()
    if parent in raw_folder_names:
        return ROLE_RAW
    if parent in clean_folder_names:
        return ROLE_CLEAN
    return None
