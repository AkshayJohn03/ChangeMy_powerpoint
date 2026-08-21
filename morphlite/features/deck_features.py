"""Deck-level features for intent classification (raw side only)."""
from __future__ import annotations

import math
import statistics

from ..ast import extractor

DECK_FEATURE_NAMES = [
    "n_slides",
    "n_distinct_layouts",
    "frac_slides_known_rebuild_source",
    "divider_frac",
    "titleish_frac",
    "avg_nodes_per_slide",
    "median_nodes_per_slide",
    "max_nodes_per_slide",
    "images_per_slide",
    "tables_per_slide",
    "charts_per_slide",
    "avg_text_len_per_slide",
    "text_len_std",
    "frac_slides_explicit_bg",
    "n_masters",
    "n_themes_pkg",
    "n_layouts_pkg",
    "style_ref_frac",
]


def extract_deck_features(deck: dict, chrome: dict, known_sources: set[str]) -> dict:
    slides = deck.get("slides", [])
    n = max(len(slides), 1)

    layouts = [s.get("layout") or "" for s in slides]
    distinct = {l for l in layouts if l}
    node_counts = []
    text_lens = []
    images = tables = charts = 0
    for s in slides:
        flat = extractor.flatten_nodes(s.get("nodes") or [])
        node_counts.append(len(flat))
        text_lens.append(sum(len(p) for nd in flat for p in [" ".join(pp["text"] for pp in nd.get("paragraphs") or [])]))
        images += sum(1 for nd in flat if nd["type"] == "IMAGE")
        tables += sum(1 for nd in flat if nd["type"] == "TABLE")
        charts += sum(1 for nd in flat if nd["type"] == "CHART")

    bg_slides = chrome.get("slides", [])
    explicit_bg = sum(
        1 for s in bg_slides if (s.get("background") or {}).get("type") in ("solid", "picture")
    )
    style_ref_slides = sum(1 for s in bg_slides if s.get("style_refs"))

    known_hits = sum(1 for l in layouts if l in known_sources)
    low = [l.lower() for l in layouts]

    return {
        "n_slides": len(slides),
        "n_distinct_layouts": len(distinct),
        "frac_slides_known_rebuild_source": round(known_hits / n, 4),
        "divider_frac": round(sum(1 for l in low if "divider" in l) / n, 4),
        "titleish_frac": round(sum(1 for l in low if "title" in l) / n, 4),
        "avg_nodes_per_slide": round(statistics.mean(node_counts) if node_counts else 0, 3),
        "median_nodes_per_slide": statistics.median(node_counts) if node_counts else 0,
        "max_nodes_per_slide": max(node_counts) if node_counts else 0,
        "images_per_slide": round(images / n, 3),
        "tables_per_slide": round(tables / n, 3),
        "charts_per_slide": round(charts / n, 3),
        "avg_text_len_per_slide": round(statistics.mean(text_lens) if text_lens else 0, 2),
        "text_len_std": round(statistics.pstdev(text_lens) if len(text_lens) > 1 else 0, 2),
        "frac_slides_explicit_bg": round(explicit_bg / n, 4),
        "n_masters": len(chrome.get("masters") or {}),
        "n_themes_pkg": len(chrome.get("themes") or {}),
        "n_layouts_pkg": len(chrome.get("layouts") or {}),
        "style_ref_frac": round(style_ref_slides / max(len(bg_slides), 1), 4),
    }
