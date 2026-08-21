"""Node-level and slide-context features extracted from the RAW AST only.

Blind by construction: no branded-side information may enter these features.
"""
from __future__ import annotations

import math

from ..ast import extractor

FEATURE_SCHEMA_VERSION = "1.1.0"

FEATURE_NAMES = [
    "is_text", "is_shape", "is_arrow", "is_line", "is_image", "is_table", "is_chart", "is_group",
    "x", "y", "w", "h", "cx", "cy",
    "area_log1p", "aspect", "rotation_flag", "container_depth",
    "font_size_pt", "size_rel_max", "size_rel_median", "is_largest_font",
    "bold", "italic",
    "text_len_log1p", "word_count_log1p", "numeric_ratio", "upper_ratio", "guidance_flag",
    "fill_present",
    "y_rank_frac", "x_rank_frac", "nn_dist",
    "ctx_n_nodes_log1p", "ctx_n_text_frac",
]


def _dominant_size(node: dict) -> float:
    sizes = {}
    for p in node.get("paragraphs") or []:
        for r in p.get("runs") or []:
            if r.get("font_size_pt"):
                s = round(r["font_size_pt"], 2)
                sizes[s] = sizes.get(s, 0) + 1
    return max(sizes, key=sizes.get) if sizes else 0.0


def _node_text(node: dict) -> str:
    return " ".join(p["text"] for p in node.get("paragraphs") or [])


def _bbox(node: dict):
    b = node.get("bbox_norm") or {}
    return (b.get("x"), b.get("y"), b.get("w"), b.get("h"))


def slide_context(nodes: list[dict]) -> dict:
    flat = extractor.flatten_nodes(nodes)
    texts = [_node_text(n) for n in flat]
    sizes = [_dominant_size(n) for n in flat if n["type"] == "TEXT" and _dominant_size(n) > 0]
    return {
        "n": len(flat),
        "flat": flat,
        "texts": texts,
        "max_size": max(sizes) if sizes else 0.0,
        "median_size": sorted(sizes)[len(sizes) // 2] if sizes else 0.0,
    }


def extract_slide_node_features(nodes: list[dict]) -> list[dict]:
    ctx = slide_context(nodes)
    flat = ctx["flat"]

    cands = []
    for n in flat:
        x, y, w, h = _bbox(n)
        cx = cy = None
        if None not in (x, y, w, h):
            cx, cy = x + w / 2, y + h / 2
        cands.append((cx, cy))
    ranked_y = sorted(range(len(flat)), key=lambda i: (cands[i][1] is None, cands[i][1] or 0))
    ranked_x = sorted(range(len(flat)), key=lambda i: (cands[i][0] is None, cands[i][0] or 0))
    y_rank = {i: k / max(len(flat) - 1, 1) for k, i in enumerate(ranked_y)}
    x_rank = {i: k / max(len(flat) - 1, 1) for k, i in enumerate(ranked_x)}

    out = []
    for i, n in enumerate(flat):
        x, y, w, h = _bbox(n)
        t = n["type"]
        text = ctx["texts"][i]
        size = _dominant_size(n)
        cx, cy = cands[i]

        nn = 9.9
        for j, (ojx, ojy) in enumerate(cands):
            if j == i or ojx is None or cx is None:
                continue
            d = math.hypot(ojx - cx, ojy - cy)
            nn = min(nn, d)

        chars = len(text.strip())
        words = len(text.split())
        numeric_ratio = (sum(ch.isdigit() for ch in text) / chars) if chars else 0.0
        upper_ratio = (sum(ch.isupper() for ch in text) / max(sum(ch.isalpha() for ch in text), 1)) if chars else 0.0
        low = text.lower()
        bold = any(r.get("bold") for p in n.get("paragraphs") or [] for r in p.get("runs") or [])
        italic = any(r.get("italic") for p in n.get("paragraphs") or [] for r in p.get("runs") or [])

        feats = {
            "is_text": int(t == "TEXT"),
            "is_shape": int(t == "SHAPE"),
            "is_arrow": int(t == "ARROW"),
            "is_line": int(t == "LINE"),
            "is_image": int(t == "IMAGE"),
            "is_table": int(t == "TABLE"),
            "is_chart": int(t == "CHART"),
            "is_group": int(t == "GROUP"),
            "x": x if x is not None else -1.0,
            "y": y if y is not None else -1.0,
            "w": w if w is not None else 0.0,
            "h": h if h is not None else 0.0,
            "cx": cx if cx is not None else -1.0,
            "cy": cy if cy is not None else -1.0,
            "area_log1p": math.log1p(abs(w * h)) if None not in (w, h) else 0.0,
            "aspect": min(max(w / h, 0), 50) if None not in (w, h) and h else 0.0,
            "rotation_flag": int(abs(n.get("rotation") or 0) > 1),
            "container_depth": n.get("container_depth") or 0,
            "font_size_pt": size,
            "size_rel_max": size / ctx["max_size"] if ctx["max_size"] else 0.0,
            "size_rel_median": size / ctx["median_size"] if ctx["median_size"] else 0.0,
            "is_largest_font": int(ctx["max_size"] > 0 and size >= ctx["max_size"]),
            "bold": int(bool(bold)),
            "italic": int(bool(italic)),
            "text_len_log1p": math.log1p(chars),
            "word_count_log1p": math.log1p(words),
            "numeric_ratio": round(numeric_ratio, 4),
            "upper_ratio": round(upper_ratio, 4),
            "guidance_flag": int(("font guidance" in low) or ("do not change" in low)),
            "fill_present": int(bool(n.get("fill_color"))),
            "y_rank_frac": round(y_rank[i], 4),
            "x_rank_frac": round(x_rank[i], 4),
            "nn_dist": round(min(nn, 9.9), 4),
            "ctx_n_nodes_log1p": round(math.log1p(ctx["n"]), 4),
            "ctx_n_text_frac": round(sum(1 for f in flat if f["type"] == "TEXT") / max(ctx["n"], 1), 4),
        }
        out.append(feats)
    return out


def node_ids_of_slide(nodes: list[dict]) -> list[str]:
    return [n["id"] for n in extractor.flatten_nodes(nodes)]
