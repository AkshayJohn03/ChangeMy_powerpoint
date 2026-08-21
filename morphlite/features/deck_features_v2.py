"""Deck features v2: structural aggregates + invariant fingerprint similarity.

No raw layout names enter the feature vector.
"""
from __future__ import annotations

import statistics

from ..ast import extractor
from . import fingerprint as fp
from .deck_features import DECK_FEATURE_NAMES as V1_NAMES, extract_deck_features

DROPPED_V1 = {"frac_slides_known_rebuild_source", "divider_frac", "titleish_frac"}

DECK_BASE_NAMES = [f for f in V1_NAMES if f not in DROPPED_V1]

DECK_V2_EXTRA = [
    "n_used_layouts",
    "frac_eff_size_resolved",
    "sim_topo_max",
    "sim_theme_max",
    "sim_master_max",
    "sim_ladder_max",
    "sim_weighted_max",
    "sim_weighted_mean",
]

DECK_FEATURE_NAMES_V2 = DECK_BASE_NAMES + DECK_V2_EXTRA


def extract_deck_features_v2(deck: dict, chrome: dict, template_fps: dict[str, dict]) -> dict:
    base = extract_deck_features(deck, chrome, known_sources=set())
    feats = {k: v for k, v in base.items() if k not in DROPPED_V1}

    used = {s.get("layout") or "" for s in chrome.get("slides") or []}
    feats["n_used_layouts"] = len([u for u in used if u])

    text_total = eff_total = 0
    for slide in deck.get("slides") or []:
        for nd in extractor.flatten_nodes(slide.get("nodes") or []):
            if nd.get("paragraphs"):
                text_total += 1
                e = (nd.get("effective") or {}).get("font_size_pt") or {}
                if isinstance(e.get("value"), (int, float)):
                    eff_total += 1
    feats["frac_eff_size_resolved"] = round(eff_total / max(text_total, 1), 4)

    own = fp.fingerprint_deck(deck["deck_id"], deck)
    sims = [fp.similarity(own, tfp) for tfp in template_fps.values()] or []
    for block in ("topology", "theme", "master", "ladder", "weighted"):
        vals = [s[block] for s in sims]
        key = f"sim_{block}_max"
        if block == "weighted":
            feats[key] = round(max(vals), 4) if vals else 0.0
            feats["sim_weighted_mean"] = round(sum(vals) / len(vals), 4) if vals else 0.0
        else:
            feats[key] = round(max(vals), 4) if vals else 0.0

    return {k: feats.get(k, 0.0) for k in DECK_FEATURE_NAMES_V2}
