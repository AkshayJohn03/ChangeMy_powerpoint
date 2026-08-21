"""Persistent ID generation for decks, slides and nodes."""
from __future__ import annotations

import re


def slugify(name: str) -> str:
    s = name.lower()
    s = re.sub(r"[^a-z0-9]+", "_", s).strip("_")
    return re.sub(r"_+", "_", s)


def deck_id(bucket: str, batch: str, filename: str) -> str:
    return f"{slugify(bucket)}__{slugify(batch)}__{slugify(filename)}"


def slide_id(deck: str, index: int) -> str:
    return f"{deck}__s{index:03d}"


def node_id(slide: str, index: int) -> str:
    return f"{slide}__n{index:03d}"
