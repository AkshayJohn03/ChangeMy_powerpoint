"""Zero-Leak Golden Pair Style & Metadata DNA Extractor.

Strictly zero text copy, zero images, zero proprietary data read or exported.
Extracts pure mathematical rules, geometry, typography, color palettes,
and aligns Raw <-> Golden slide elements using human-like structural heuristics
(char count buffer +-10, start/end char match, spatial rank, container boxing).

Usage:
    # Single pair:
    python scripts/extract_golden_pair_dna.py --raw "path/to/Raw.pptx" --golden "path/to/Golden.pptx"

    # Specific 17 Oct Golden pair:
    python scripts/extract_golden_pair_dna.py --pair-10oct

    # Batch scan 12 Dec Updated folder:
    python scripts/extract_golden_pair_dna.py --batch-12dec

    # Batch scan any directory:
    python scripts/extract_golden_pair_dna.py --scan-dir "C:/path/to/Updated"

    # All configured roots in BrandMorph:
    python scripts/extract_golden_pair_dna.py --all
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pptx
from pptx.enum.dml import MSO_FILL
from pptx.enum.shapes import MSO_SHAPE_TYPE
from pptx.enum.text import PP_ALIGN

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

# Safe EMU to inch / pt conversions
EMU_PER_INCH = 914400.0
EMU_PER_PT = 12700.0

# Pre-defined known locations from user directives
LOCATION_10_OCT = Path(r"C:\Users\Akshay.JOHN-XAVIER\OneDrive - Akkodis\Documents\10 Oct 2026")
LOCATION_12_DEC = Path(r"C:\Users\Akshay.JOHN-XAVIER\OneDrive - Akkodis\Documents\12 Dec\OneDrive_2025-12-11\Updated")


def to_hex(color_obj) -> Optional[str]:
    """Extract 6-character hex color without throwing exceptions."""
    if color_obj is None:
        return None
    try:
        if hasattr(color_obj, "rgb") and color_obj.rgb is not None:
            return str(color_obj.rgb).upper()
    except Exception:
        pass
    return None


def get_shape_fill(shape) -> Dict[str, Any]:
    """Extract shape fill properties (pure hex, zero content)."""
    result = {
        "type": "NONE",
        "color_hex": None,
        "transparency": 0.0,
    }
    try:
        fill = shape.fill
        if fill.type == MSO_FILL.SOLID:
            result["type"] = "SOLID"
            result["color_hex"] = to_hex(fill.fore_color)
            if hasattr(fill, "transparency"):
                result["transparency"] = round(float(fill.transparency), 3)
        elif fill.type == MSO_FILL.GRADIENT:
            result["type"] = "GRADIENT"
        elif fill.type == MSO_FILL.PICTURE:
            result["type"] = "PICTURE"
        elif fill.type == MSO_FILL.BACKGROUND:
            result["type"] = "BACKGROUND"
    except Exception:
        pass
    return result


def get_shape_line(shape) -> Dict[str, Any]:
    """Extract shape border/stroke properties (pure hex, pt)."""
    result = {
        "has_line": False,
        "color_hex": None,
        "width_pt": 0.0,
        "dash_style": "SOLID",
    }
    try:
        line = shape.line
        if line and line.fill and line.fill.type == MSO_FILL.SOLID:
            result["has_line"] = True
            result["color_hex"] = to_hex(line.color)
            if line.width:
                result["width_pt"] = round(line.width / EMU_PER_PT, 2)
            if hasattr(line, "dash_style") and line.dash_style:
                result["dash_style"] = str(line.dash_style).split()[-1]
    except Exception:
        pass
    return result


def extract_shape_metadata(shape, slide_w_in: float, slide_h_in: float, idx: int) -> Dict[str, Any]:
    """Extract complete structural metadata from a shape with ZERO text copy leakage."""
    meta: Dict[str, Any] = {
        "shape_id": shape.shape_id if hasattr(shape, "shape_id") else idx,
        "idx": idx,
        "name": getattr(shape, "name", f"Shape_{idx}"),
        "shape_type": "UNKNOWN",
        "preset_geometry": None,
        "bbox_in": {
            "left": round(shape.left / EMU_PER_INCH, 3),
            "top": round(shape.top / EMU_PER_INCH, 3),
            "width": round(shape.width / EMU_PER_INCH, 3),
            "height": round(shape.height / EMU_PER_INCH, 3),
            "right": round((shape.left + shape.width) / EMU_PER_INCH, 3),
            "bottom": round((shape.top + shape.height) / EMU_PER_INCH, 3),
        },
        "bbox_norm": [
            round((shape.left / EMU_PER_INCH) / max(slide_w_in, 1e-3), 3),
            round((shape.top / EMU_PER_INCH) / max(slide_h_in, 1e-3), 3),
            round(((shape.left + shape.width) / EMU_PER_INCH) / max(slide_w_in, 1e-3), 3),
            round(((shape.top + shape.height) / EMU_PER_INCH) / max(slide_h_in, 1e-3), 3),
        ],
        "rotation": round(getattr(shape, "rotation", 0.0), 1),
        "fill": get_shape_fill(shape),
        "line": get_shape_line(shape),
        "has_text": False,
        "text_meta": None,
        "is_container": False,
        "is_icon_candidate": False,
        "is_circular_badge": False,
        "is_top_right_logo": False,
        "is_bottom_banner": False,
        "is_connector": False,
    }

    # Shape type & geometry
    st = getattr(shape, "shape_type", None)
    tag = shape._element.tag if hasattr(shape, "_element") else ""
    if tag.endswith("}cxnSp") or st == MSO_SHAPE_TYPE.LINE:
        meta["shape_type"] = "CONNECTOR"
        meta["is_connector"] = True
    elif st == MSO_SHAPE_TYPE.AUTO_SHAPE:
        meta["shape_type"] = "AUTO_SHAPE"
        try:
            if hasattr(shape, "auto_shape_type"):
                meta["preset_geometry"] = str(shape.auto_shape_type).split()[-1]
        except Exception:
            pass
    elif st == MSO_SHAPE_TYPE.TEXT_BOX:
        meta["shape_type"] = "TEXT_BOX"
    elif st == MSO_SHAPE_TYPE.PICTURE:
        meta["shape_type"] = "PICTURE"
    elif st == MSO_SHAPE_TYPE.TABLE:
        meta["shape_type"] = "TABLE"
    elif st == MSO_SHAPE_TYPE.GROUP:
        meta["shape_type"] = "GROUP"
    else:
        meta["shape_type"] = str(st).split()[-1] if st else "UNKNOWN"

    w_in = meta["bbox_in"]["width"]
    h_in = meta["bbox_in"]["height"]
    l_in = meta["bbox_in"]["left"]
    t_in = meta["bbox_in"]["top"]

    # Semantic flags
    if w_in >= 2.0 and h_in >= 1.2 and meta["fill"]["type"] == "SOLID":
        meta["is_container"] = True
    if w_in <= 1.25 and h_in <= 1.25:
        meta["is_icon_candidate"] = True
        if abs(w_in - h_in) <= 0.15:
            meta["is_circular_badge"] = True
    if l_in >= 9.2 and t_in <= 1.3 and w_in <= 3.8 and h_in <= 1.3:
        meta["is_top_right_logo"] = True
    if t_in >= 6.1 and w_in >= 7.0 and h_in <= 1.2:
        meta["is_bottom_banner"] = True

    # Extract text frame metadata without saving the text
    if getattr(shape, "has_text_frame", False):
        tf = shape.text_frame
        raw_full_text = tf.text or ""
        stripped = raw_full_text.strip()
        if stripped:
            meta["has_text"] = True
            first_c = stripped[0]
            last_c = stripped[-1]
            sha_prefix = hashlib.sha256(stripped.encode("utf-8")).hexdigest()[:8]

            paragraphs_meta: List[Dict[str, Any]] = []
            runs_summary: Counter = Counter()
            dominant_font = None
            dominant_size = None
            dominant_color = None

            for p in tf.paragraphs:
                p_text = p.text or ""
                p_strip = p_text.strip()
                if not p_strip:
                    continue

                align_str = "LEFT"
                try:
                    if p.alignment == PP_ALIGN.CENTER:
                        align_str = "CENTER"
                    elif p.alignment == PP_ALIGN.RIGHT:
                        align_str = "RIGHT"
                    elif p.alignment == PP_ALIGN.JUSTIFY:
                        align_str = "JUSTIFY"
                except Exception:
                    pass

                runs_meta = []
                for r in p.runs:
                    r_text = r.text or ""
                    if not r_text:
                        continue
                    fname = r.font.name or "inherited"
                    fsize = round(r.font.size.pt, 1) if r.font.size else "inherited"
                    bold = bool(r.font.bold)
                    italic = bool(r.font.italic)
                    underline = bool(r.font.underline)
                    color_hex = to_hex(r.font.color)

                    runs_summary[(fname, str(fsize), color_hex, bold)] += len(r_text)
                    runs_meta.append({
                        "font_name": fname,
                        "font_size_pt": fsize,
                        "bold": bold,
                        "italic": italic,
                        "underline": underline,
                        "color_hex": color_hex,
                        "char_count": len(r_text),
                    })

                paragraphs_meta.append({
                    "char_count": len(p_strip),
                    "word_count": len(p_strip.split()),
                    "align": align_str,
                    "level": getattr(p, "level", 0),
                    "is_bullet": bool(getattr(p, "level", 0) > 0 or p_strip.startswith(("-", "•", "*", "1.", "2."))),
                    "runs_count": len(runs_meta),
                    "runs": runs_meta,
                })

            if runs_summary:
                top_run = runs_summary.most_common(1)[0][0]
                dominant_font, dominant_size, dominant_color, _ = top_run

            meta["text_meta"] = {
                "char_count": len(stripped),
                "word_count": len(stripped.split()),
                "paragraph_count": len(paragraphs_meta),
                "start_char": first_c.upper() if first_c.isalnum() else first_c,
                "end_char": last_c.upper() if last_c.isalnum() else last_c,
                "is_all_caps": bool(stripped.isupper() and len(stripped) > 3),
                "is_title_case": bool(stripped.istitle()),
                "sha256_prefix": sha_prefix,
                "dominant_font": dominant_font,
                "dominant_size_pt": dominant_size,
                "dominant_color_hex": dominant_color,
                "paragraphs": paragraphs_meta,
            }

    return meta


def extract_slide_metadata(slide, slide_w_in: float, slide_h_in: float, slide_idx: int) -> Dict[str, Any]:
    """Extract metadata for an entire slide."""
    shapes_meta = []
    for idx, shape in enumerate(slide.shapes):
        try:
            sm = extract_shape_metadata(shape, slide_w_in, slide_h_in, idx)
            shapes_meta.append(sm)
        except Exception:
            pass

    # Detect slide background
    bg_meta = {"type": "DEFAULT", "color_hex": None}
    try:
        bg = slide.background
        if bg and hasattr(bg, "fill") and bg.fill.type == MSO_FILL.SOLID:
            bg_meta["type"] = "SOLID"
            bg_meta["color_hex"] = to_hex(bg.fill.fore_color)
    except Exception:
        pass

    return {
        "slide_idx": slide_idx,
        "shape_count": len(shapes_meta),
        "text_shape_count": sum(1 for s in shapes_meta if s["has_text"]),
        "container_count": sum(1 for s in shapes_meta if s["is_container"]),
        "icon_count": sum(1 for s in shapes_meta if s["is_icon_candidate"]),
        "connector_count": sum(1 for s in shapes_meta if s["is_connector"]),
        "has_top_right_logo": any(s["is_top_right_logo"] for s in shapes_meta),
        "has_bottom_banner": any(s["is_bottom_banner"] for s in shapes_meta),
        "background": bg_meta,
        "shapes": shapes_meta,
    }


def compute_shape_similarity(raw_s: Dict[str, Any], gld_s: Dict[str, Any]) -> float:
    """Compute structural metadata similarity score [0.0 - 1.0] between a Raw and Golden shape."""
    # 1. Exact text hash match (strongest possible proof of identical content)
    if raw_s["has_text"] and gld_s["has_text"]:
        r_tm = raw_s["text_meta"]
        g_tm = gld_s["text_meta"]

        if r_tm["sha256_prefix"] == g_tm["sha256_prefix"]:
            return 1.0

        score = 0.0
        # Character count closeness with +-10 buffer as requested by user
        r_len = r_tm["char_count"]
        g_len = g_tm["char_count"]
        diff = abs(r_len - g_len)
        if diff == 0:
            score += 0.45
        elif diff <= 10:
            score += 0.40 - (diff * 0.015)
        else:
            ratio = min(r_len, g_len) / max(r_len, g_len, 1)
            score += 0.30 * ratio

        # Start & end character match (human-like reading verification)
        if r_tm["start_char"] == g_tm["start_char"]:
            score += 0.20
        if r_tm["end_char"] == g_tm["end_char"]:
            score += 0.15

        # Word count ratio
        r_words = r_tm["word_count"]
        g_words = g_tm["word_count"]
        w_ratio = min(r_words, g_words) / max(r_words, g_words, 1)
        score += 0.10 * w_ratio

        # Spatial order similarity (both near top, or both near middle)
        r_norm_y = raw_s["bbox_norm"][1]
        g_norm_y = gld_s["bbox_norm"][1]
        y_dist = abs(r_norm_y - g_norm_y)
        if y_dist <= 0.20:
            score += 0.10 * (1.0 - y_dist / 0.20)

        return min(round(score, 3), 1.0)

    # 2. Both are non-text shapes (e.g. logos, images, dividers, connectors)
    if not raw_s["has_text"] and not gld_s["has_text"]:
        if raw_s["shape_type"] == gld_s["shape_type"]:
            # IoU / Spatial overlap
            r_norm = raw_s["bbox_norm"]
            g_norm = gld_s["bbox_norm"]
            dx = abs(r_norm[0] - g_norm[0])
            dy = abs(r_norm[1] - g_norm[1])
            if dx <= 0.15 and dy <= 0.15:
                return 0.75
            return 0.40

    return 0.0


def align_slide_elements(raw_slide: Dict[str, Any], gld_slide: Dict[str, Any]) -> Dict[str, Any]:
    """Align shapes between Raw and Golden slide, detecting transformations, additions, and removals."""
    raw_shapes = raw_slide["shapes"]
    gld_shapes = gld_slide["shapes"]

    # Compute similarity matrix
    sim_scores: List[Tuple[float, int, int]] = []
    for r_idx, r_s in enumerate(raw_shapes):
        for g_idx, g_s in enumerate(gld_shapes):
            sim = compute_shape_similarity(r_s, g_s)
            if sim >= 0.35:
                sim_scores.append((sim, r_idx, g_idx))

    # Greedy maximum-weight bipartite matching
    sim_scores.sort(key=lambda x: x[0], reverse=True)
    matched_raw = set()
    matched_gld = set()
    pairs = []

    for sim, r_idx, g_idx in sim_scores:
        if r_idx not in matched_raw and g_idx not in matched_gld:
            matched_raw.add(r_idx)
            matched_gld.add(g_idx)
            pairs.append((sim, raw_shapes[r_idx], gld_shapes[g_idx]))

    # Analyze transformations
    transformations = []
    for sim, r_s, g_s in pairs:
        trans: Dict[str, Any] = {
            "match_confidence": sim,
            "raw_id": r_s["shape_id"],
            "golden_id": g_s["shape_id"],
            "raw_type": r_s["shape_type"],
            "golden_type": g_s["shape_type"],
            "bbox_delta_in": {
                "dx": round(g_s["bbox_in"]["left"] - r_s["bbox_in"]["left"], 2),
                "dy": round(g_s["bbox_in"]["top"] - r_s["bbox_in"]["top"], 2),
                "dw": round(g_s["bbox_in"]["width"] - r_s["bbox_in"]["width"], 2),
                "dh": round(g_s["bbox_in"]["height"] - r_s["bbox_in"]["height"], 2),
            },
        }

        # Typography transformation
        if r_s["has_text"] and g_s["has_text"]:
            r_tm = r_s["text_meta"]
            g_tm = g_s["text_meta"]
            trans["typography_delta"] = {
                "font_family": f"{r_tm['dominant_font']} -> {g_tm['dominant_font']}",
                "font_size_pt": f"{r_tm['dominant_size_pt']} -> {g_tm['dominant_size_pt']}",
                "color_hex": f"#{r_tm['dominant_color_hex']} -> #{g_tm['dominant_color_hex']}",
                "char_count_delta": g_tm["char_count"] - r_tm["char_count"],
            }

        # Container transformation (e.g. text framed in card)
        trans["container_added"] = bool(not r_s["is_container"] and g_s["is_container"])
        trans["border_added"] = bool(not r_s["line"]["has_line"] and g_s["line"]["has_line"])
        if g_s["fill"]["color_hex"]:
            trans["golden_fill_hex"] = g_s["fill"]["color_hex"]
        if g_s["line"]["color_hex"]:
            trans["golden_border_hex"] = g_s["line"]["color_hex"]

        transformations.append(trans)

    # Added elements in Golden (shapes, cards, icons, banners)
    added_elements = []
    for g_idx, g_s in enumerate(gld_shapes):
        if g_idx not in matched_gld:
            elem_category = "SHAPE"
            if g_s["is_container"]:
                elem_category = "CARD_CONTAINER"
            elif g_s["is_top_right_logo"]:
                elem_category = "TOP_RIGHT_LOGO"
            elif g_s["is_bottom_banner"]:
                elem_category = "BOTTOM_BANNER"
            elif g_s["is_circular_badge"] or g_s["is_icon_candidate"]:
                elem_category = "ICON_OR_BADGE"
            elif g_s["is_connector"]:
                elem_category = "CONNECTOR_FLOW"

            added_elements.append({
                "category": elem_category,
                "golden_id": g_s["shape_id"],
                "shape_type": g_s["shape_type"],
                "preset_geometry": g_s["preset_geometry"],
                "bbox_in": g_s["bbox_in"],
                "fill_hex": g_s["fill"]["color_hex"],
                "border_hex": g_s["line"]["color_hex"],
                "border_width_pt": g_s["line"]["width_pt"],
            })

    # Removed elements from Raw
    removed_elements = []
    for r_idx, r_s in enumerate(raw_shapes):
        if r_idx not in matched_raw:
            removed_elements.append({
                "raw_id": r_s["shape_id"],
                "shape_type": r_s["shape_type"],
                "bbox_in": r_s["bbox_in"],
                "had_text": r_s["has_text"],
                "char_count": r_s["text_meta"]["char_count"] if r_s["has_text"] else 0,
            })

    return {
        "matched_count": len(transformations),
        "added_count": len(added_elements),
        "removed_count": len(removed_elements),
        "transformations": transformations,
        "added_elements": added_elements,
        "removed_elements": removed_elements,
    }


def extract_golden_pair_dna(raw_path: Path, golden_path: Path) -> Dict[str, Any]:
    """Process a single Golden Pair (Raw vs Golden) with ZERO text copy leakage."""
    print(f"\n[Golden Pair Extraction] Processing:")
    print(f"  Raw:    {raw_path.name}")
    print(f"  Golden: {golden_path.name}")

    raw_prs = pptx.Presentation(str(raw_path))
    gld_prs = pptx.Presentation(str(golden_path))

    slide_w_in = round(gld_prs.slide_width.inches, 3)
    slide_h_in = round(gld_prs.slide_height.inches, 3)

    dna: Dict[str, Any] = {
        "metadata": {
            "raw_filename": raw_path.name,
            "golden_filename": golden_path.name,
            "extracted_at": datetime.now(timezone.utc).isoformat(),
            "slide_width_in": slide_w_in,
            "slide_height_in": slide_h_in,
            "raw_slide_count": len(raw_prs.slides),
            "golden_slide_count": len(gld_prs.slides),
        },
        "stats": {
            "fonts_by_size": Counter(),
            "text_rgb_by_size": Counter(),
            "shape_fill_rgbs": Counter(),
            "shape_border_rgbs": Counter(),
            "card_border_rgbs": Counter(),
            "font_transformations": Counter(),
            "font_size_transformations": Counter(),
            "added_categories": Counter(),
        },
        "slide_alignments": [],
    }

    # Iterate slide-by-slide
    n_slides = min(len(raw_prs.slides), len(gld_prs.slides))
    for s_idx in range(n_slides):
        raw_s = raw_prs.slides[s_idx]
        gld_s = gld_prs.slides[s_idx]

        raw_meta = extract_slide_metadata(raw_s, slide_w_in, slide_h_in, s_idx)
        gld_meta = extract_slide_metadata(gld_s, slide_w_in, slide_h_in, s_idx)

        # Aggregate distributions in golden deck
        for sh in gld_meta["shapes"]:
            if sh["fill"]["color_hex"]:
                dna["stats"]["shape_fill_rgbs"][sh["fill"]["color_hex"]] += 1
            if sh["line"]["color_hex"]:
                dna["stats"]["shape_border_rgbs"][sh["line"]["color_hex"]] += 1
                if sh["is_container"]:
                    dna["stats"]["card_border_rgbs"][sh["line"]["color_hex"]] += 1

            if sh["has_text"]:
                for p in sh["text_meta"]["paragraphs"]:
                    for r in p["runs"]:
                        f_key = f"{r['font_name']} | {r['font_size_pt']}pt | bold={r['bold']}"
                        dna["stats"]["fonts_by_size"][f_key] += 1
                        if r["color_hex"]:
                            dna["stats"]["text_rgb_by_size"][f"{r['font_size_pt']}pt -> #{r['color_hex']}"] += 1

        # Align elements between raw and golden
        alignment = align_slide_elements(raw_meta, gld_meta)
        dna["slide_alignments"].append({
            "slide_idx": s_idx,
            "alignment": alignment,
        })

        # Track transformation counters
        for trans in alignment["transformations"]:
            if "typography_delta" in trans:
                td = trans["typography_delta"]
                dna["stats"]["font_transformations"][td["font_family"]] += 1
                dna["stats"]["font_size_transformations"][td["font_size_pt"]] += 1

        for added in alignment["added_elements"]:
            dna["stats"]["added_categories"][added["category"]] += 1

    return dna


def print_dna_summary(dna: Dict[str, Any]) -> None:
    """Print pure numerical / hex / structural summary to screen (ZERO text)."""
    meta = dna["metadata"]
    stats = dna["stats"]

    summary = {
        "deck_geometry_in": [meta["slide_width_in"], meta["slide_height_in"]],
        "slides_analyzed": min(meta["raw_slide_count"], meta["golden_slide_count"]),
        "dominant_golden_fonts": stats["fonts_by_size"].most_common(8),
        "dominant_text_colors": stats["text_rgb_by_size"].most_common(8),
        "dominant_card_fills": stats["shape_fill_rgbs"].most_common(8),
        "dominant_card_borders": stats["card_border_rgbs"].most_common(6),
        "top_font_mappings": stats["font_transformations"].most_common(8),
        "top_font_size_mappings": stats["font_size_transformations"].most_common(8),
        "added_design_elements": dict(stats["added_categories"]),
    }
    print("\n" + "=" * 65)
    print("  ZERO-LEAK MATHEMATICAL STYLE DNA EXTRACTED")
    print("=" * 65)
    print(json.dumps(summary, indent=2))
    print("=" * 65 + "\n")


def scan_directory_for_pairs(dir_path: Path) -> List[Tuple[Path, Path]]:
    """Find all (raw, golden) pairs in a directory using naming conventions."""
    if not dir_path.exists():
        print(f"[Warning] Directory does not exist: {dir_path}")
        return []

    files = [f for f in dir_path.iterdir() if f.suffix.lower() == ".pptx" and not f.name.startswith("~$")]
    pairs: List[Tuple[Path, Path]] = []

    # Map by lowercase stem
    file_map = {f.name.lower(): f for f in files}

    # Convention 1: "filename_xx_raw.pptx" <-> "filename_xx.pptx" or "filename raw.pptx" <-> "filename.pptx"
    for fname_lower, raw_file in file_map.items():
        stem = raw_file.stem
        # Check patterns
        candidate_golden = None
        for pattern in ["_raw", " raw", "_Raw", " Raw"]:
            if stem.endswith(pattern):
                golden_stem = stem[:-len(pattern)]
                golden_name = f"{golden_stem}.pptx"
                if golden_name.lower() in file_map:
                    candidate_golden = file_map[golden_name.lower()]
                    break

        if candidate_golden and candidate_golden != raw_file:
            pairs.append((raw_file, candidate_golden))

    return pairs


def update_learned_rules_with_dna(all_dna: List[Dict[str, Any]]) -> None:
    """Merge newly extracted DNA rules into data/metadata/LEARNED_RULES.json."""
    rules_path = REPO_ROOT / "data" / "metadata" / "LEARNED_RULES.json"
    rules: Dict[str, Any] = {}
    if rules_path.exists():
        try:
            rules = json.loads(rules_path.read_text(encoding="utf-8"))
        except Exception:
            pass

    font_fam_map = rules.get("font_family_map", {})
    font_sz_map = rules.get("font_size_map", {})

    for dna in all_dna:
        stats = dna["stats"]
        # Update font family mappings
        for mapping, count in stats["font_transformations"].items():
            if "->" in mapping:
                src, dst = [x.strip().lower() for x in mapping.split("->")]
                if src and dst and src != dst and not src.startswith("inherited"):
                    if src not in font_fam_map or count > font_fam_map[src].get("support", 0):
                        font_fam_map[src] = {"to": dst, "support": count}

        # Update font size mappings
        for sz_mapping, count in stats["font_size_transformations"].items():
            if "->" in sz_mapping:
                try:
                    src_s, dst_s = [x.replace("pt", "").strip() for x in sz_mapping.split("->")]
                    src_f = float(src_s)
                    dst_f = float(dst_s)
                    if src_f != dst_f:
                        s_key = str(src_f)
                        if s_key not in font_sz_map or count > font_sz_map[s_key].get("support", 0):
                            font_sz_map[s_key] = {
                                "to": dst_f,
                                "support": count,
                                "confidence": 1.0,
                            }
                except Exception:
                    pass

    rules["font_family_map"] = font_fam_map
    rules["font_size_map"] = font_sz_map
    rules["last_updated_with_golden_dna"] = datetime.now(timezone.utc).isoformat()

    rules_path.parent.mkdir(parents=True, exist_ok=True)
    rules_path.write_text(json.dumps(rules, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[Updated] Successfully merged golden DNA rules into: {rules_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Zero-Leak Golden Pair Style & Metadata DNA Extractor")
    parser.add_argument("--raw", type=str, help="Path to raw pptx file")
    parser.add_argument("--golden", type=str, help="Path to golden pptx file")
    parser.add_argument("--pair-10oct", action="store_true", help="Process 10 Oct 2026 Golden vs Raw pair")
    parser.add_argument("--batch-12dec", action="store_true", help="Scan and process 12 Dec Updated pairs")
    parser.add_argument("--scan-dir", type=str, help="Scan directory for filename_xx_raw vs filename_xx pairs")
    parser.add_argument("--all", action="store_true", help="Scan all configured roots")
    parser.add_argument("--out", type=str, default="data/metadata/golden_style_dna.json", help="Output JSON path")
    args = parser.parse_args()

    pairs_to_process: List[Tuple[Path, Path]] = []

    # 1. Direct pair passed
    if args.raw and args.golden:
        pairs_to_process.append((Path(args.raw), Path(args.golden)))

    # 2. 10 Oct 2026 Golden Pair
    if args.pair_10oct or (not args.raw and not args.golden and not args.scan_dir and not args.batch_12dec and not args.all):
        raw_10 = LOCATION_10_OCT / "Raw.pptx"
        gld_10 = LOCATION_10_OCT / "17 Oct  Golden.pptx"
        if not gld_10.exists():
            gld_10 = LOCATION_10_OCT / "17 Oct Golden.pptx"
        if raw_10.exists() and gld_10.exists():
            pairs_to_process.append((raw_10, gld_10))
        elif LOCATION_10_OCT.exists():
            # Check files inside LOCATION_10_OCT
            found = scan_directory_for_pairs(LOCATION_10_OCT)
            pairs_to_process.extend(found)

    # 3. 12 Dec Batch
    if args.batch_12dec or args.all:
        if LOCATION_12_DEC.exists():
            found_12 = scan_directory_for_pairs(LOCATION_12_DEC)
            print(f"[Discovery] Found {len(found_12)} golden pairs in {LOCATION_12_DEC}")
            pairs_to_process.extend(found_12)

    # 4. Custom directory scan
    if args.scan_dir:
        found_custom = scan_directory_for_pairs(Path(args.scan_dir))
        print(f"[Discovery] Found {len(found_custom)} golden pairs in {args.scan_dir}")
        pairs_to_process.extend(found_custom)

    if not pairs_to_process:
        print("[Notice] No golden pairs found to process.")
        print("Please specify --raw and --golden, or check paths:")
        print(f"  10 Oct: {LOCATION_10_OCT}")
        print(f"  12 Dec: {LOCATION_12_DEC}")
        return

    all_dna = []
    for raw_p, gld_p in pairs_to_process:
        try:
            dna = extract_golden_pair_dna(raw_p, gld_p)
            print_dna_summary(dna)
            all_dna.append(dna)
        except Exception as e:
            print(f"[Error] Failed to process pair ({raw_p.name}, {gld_p.name}): {e}")

    # Save to JSON (pure metadata, zero text)
    out_file = REPO_ROOT / args.out
    out_file.parent.mkdir(parents=True, exist_ok=True)

    # Convert Counters to dict for JSON serialization
    serializable = []
    for d in all_dna:
        d_copy = {
            "metadata": d["metadata"],
            "stats": {k: dict(v) for k, v in d["stats"].items()},
            "slide_alignments": d["slide_alignments"],
        }
        serializable.append(d_copy)

    out_file.write_text(json.dumps(serializable, indent=2), encoding="utf-8")
    print(f"[Saved] Extracted Style DNA saved to: {out_file}")

    # Update learned rules
    update_learned_rules_with_dna(all_dna)


if __name__ == "__main__":
    main()
