"""Invariant template fingerprints.

Name-free deck signature built from:
    - layout placeholder topology (type + quantized geometry multiset)
    - master structure (count, bg types, txStyles size ladders)
    - theme palette histogram (hue x value bins) + font families
    - slide-level effective font-size ladder

Fixed-dim hashed vectors -> cosine similarity; exact-hash for duplicates.
"""
from __future__ import annotations

import hashlib
import json
import colorsys
import zipfile
from collections import Counter
from pathlib import Path

from .. import config

CHROME_ROOT = config.EXTRACTED_DIR / "chrome"
FP_DIM = 128

HUE_BINS = 12
VAL_BINS = 4


def _h64(s: str) -> int:
    return int(hashlib.md5(s.encode("utf-8")).hexdigest()[:16], 16)


def _bump(vec: list[float], token: str, w: float = 1.0):
    vec[_h64(token) % FP_DIM] += w


def _cosine(a: list[float], b: list[float]) -> float:
    na = sum(x * x for x in a) ** 0.5
    nb = sum(x * x for x in b) ** 0.5
    if not na or not nb:
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    return round(dot / (na * nb), 6)


def _hex_hv(hexval: str) -> tuple[int, int] | None:
    try:
        r = int(hexval[0:2], 16) / 255
        g = int(hexval[2:4], 16) / 255
        b = int(hexval[4:6], 16) / 255
    except Exception:
        return None
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    return int(h * HUE_BINS) % HUE_BINS, min(int(v * VAL_BINS), VAL_BINS - 1)


def fingerprint_deck(deck_id: str, ast_v2: dict | None = None) -> dict:
    chrome = json.loads((CHROME_ROOT / f"{deck_id}.json").read_text(encoding="utf-8"))

    topo_vec = [0.0] * FP_DIM
    master_vec = [0.0] * FP_DIM
    theme_vec = [0.0] * FP_DIM

    masters = chrome.get("masters") or {}
    themes = chrome.get("themes") or {}
    _bump(master_vec, f"nmasters:{len(masters)}", 3.0)
    theme_palette_bins = Counter()
    theme_fonts = set()
    for tname, tdata in themes.items():
        pal = tdata.get("palette") or {}
        for role, hexval in sorted(pal.items()):
            hv = _hex_hv(hexval or "")
            if hv:
                theme_palette_bins[hv] += 1
                _bump(theme_vec, f"pal:{hv[0]}x{hv[1]}", 1.5)
            else:
                _bump(theme_vec, f"palraw:{role}", 0.5)
        fonts = tdata.get("fonts") or {}
        for fk in ("majorFont", "minorFont"):
            fam = (fonts.get(fk) or "").strip().lower()
            if fam:
                theme_fonts.add(fam)
                _bump(theme_vec, f"font:{fam}:{fk}", 2.0)

    used_layouts = Counter()
    bg_types = Counter()
    style_ref_slides = 0
    slides = chrome.get("slides") or []
    for s in slides:
        if s.get("layout"):
            used_layouts[s["layout"]] += 1
        bg_types[(s.get("background") or {}).get("type") or "absent"] += 1
        if s.get("style_refs"):
            style_ref_slides += 1
    used_parts: Counter = Counter()
    name_to_part = {}
    for part, meta in (chrome.get("layouts") or {}).items():
        nm = meta.get("name") or part
        name_to_part.setdefault(nm, part)
        name_to_part.setdefault(part, part)
    for s in slides:
        lp = name_to_part.get(s.get("layout") or "", "")
        if lp:
            used_parts[lp] += 1
    layout_sigs_used = []
    for part, cnt in used_parts.items():
        meta = (chrome.get("layouts") or {}).get(part) or {}
        rows = tuple(meta.get("ph_topology") or [])
        counts = meta.get("shape_counts") or {}
        sig = ";".join(rows) + "#" + ",".join(f"{k}:{v}" for k, v in sorted(counts.items()))
        sig = sig or f"empty@{part}"
        layout_sigs_used.append(sig[:200])
        _bump(topo_vec, "ltopo:" + sig[:160], float(cnt))
        _bump(topo_vec, f"nph:{len(rows)}", 0.5 * cnt)
    for bt, cnt in bg_types.items():
        _bump(master_vec, f"bg:{bt}", float(cnt))
    _bump(master_vec, f"stylerefs:{style_ref_slides >= len(slides) / 2}", 1.0)
    for mpart, ladder in (chrome.get("master_ladders") or {}).items():
        for style, sizes in ladder.items():
            if sizes:
                _bump(master_vec, f"ladder:{style}:{','.join(str(x) for x in sizes)}", 1.0)

    eff_sizes: Counter = Counter()
    if ast_v2:
        from ..ast import extractor as ex

        for slide in ast_v2.get("slides", []):
            for node in ex.flatten_nodes(slide.get("nodes") or []):
                e = ((node.get("effective") or {}).get("font_size_pt") or {}).get("value")
                if isinstance(e, (int, float)):
                    eff_sizes[round(float(e))] += 1
    ladder_vec = [0.0] * FP_DIM
    ladder_sizes = sorted(eff_sizes)
    for s, cnt in eff_sizes.items():
        _bump(ladder_vec, f"sz:{s}", float(cnt))

    fp = {
        "topology": topo_vec,
        "master": master_vec,
        "theme": theme_vec,
        "ladder": ladder_vec,
    }
    canonical = {
        "used_layout_structures": sorted(layout_sigs_used),
        "bg_types": dict(bg_types),
        "n_masters": len(masters),
        "palette_bins": {str(k): v for k, v in sorted(theme_palette_bins.items())},
        "theme_fonts": sorted(theme_fonts),
        "size_ladder": ladder_sizes,
    }
    exact_hash = hashlib.md5(json.dumps(canonical, sort_keys=True).encode()).hexdigest()

    return {
        "deck_id": deck_id,
        "vectors": fp,
        "canonical": canonical,
        "exact_hash": exact_hash,
    }


def meta_master(chrome: dict, layout_name: str) -> str:
    for name, meta in (chrome.get("layouts") or {}).items():
        if (meta.get("name") or "") == layout_name or name == layout_name:
            return str(meta.get("master"))
    return "?"


BLOCK_WEIGHTS = {"topology": 2.0, "master": 1.0, "theme": 1.5, "ladder": 1.0}


def similarity(a: dict, b: dict) -> dict:
    out = {}
    for block, w in BLOCK_WEIGHTS.items():
        out[block] = _cosine(a["vectors"][block], b["vectors"][block]) * w
    out["weighted"] = round(sum(out.values()) / sum(BLOCK_WEIGHTS.values()), 6)
    out["exact_match"] = a["exact_hash"] == b["exact_hash"]
    return out


def build_all(deck_ids: list[str], ast_v2_index: dict[str, str] | None = None) -> dict[str, dict]:
    out = {}
    for did in deck_ids:
        ast_v2 = None
        if ast_v2_index and did in ast_v2_index:
            p = Path(ast_v2_index[did])
            if p.exists():
                ast_v2 = json.loads(p.read_text(encoding="utf-8"))
        out[did] = fingerprint_deck(did, ast_v2)
    return out


if __name__ == "__main__":
    print("module; use morphlite.training.fingerprint_stats")
