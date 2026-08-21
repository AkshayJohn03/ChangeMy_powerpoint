"""Deterministic slide text fingerprinting and similarity scoring."""
from __future__ import annotations

import difflib
import re
from functools import lru_cache

_WORD_RE = re.compile(r"[a-z0-9]+")


@lru_cache(maxsize=8192)
def normalize_text(text: str) -> str:
    s = text.lower().replace("&", " and ")
    return " ".join(_WORD_RE.findall(s))


def tokens(text: str) -> set[str]:
    return set(normalize_text(text).split())


def similarity(a: str, b: str) -> float:
    na, nb = normalize_text(a), normalize_text(b)
    if not na or not nb:
        return 0.0
    if na == nb:
        return 1.0
    ta, tb = tokens(a), tokens(b)
    jac = len(ta & tb) / len(ta | tb) if ta | tb else 0.0
    ratio = difflib.SequenceMatcher(None, na, nb).ratio()
    return round(0.5 * jac + 0.5 * ratio, 4)


def containment(a: str, b: str) -> float:
    ta, tb = tokens(a), tokens(b)
    if not ta or not tb:
        return 0.0
    return round(len(ta & tb) / min(len(ta), len(tb)), 4)
