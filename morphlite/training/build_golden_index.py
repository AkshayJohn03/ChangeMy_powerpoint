"""Build the anonymized golden layout index + sanitized <3MB master template.

Part 1 — data/metadata/golden_layout_index.json (<2MB):
  For every golden branded slide (43 pairs / 301 slide alignments) plus the
  10 tagged master-template slides, records the structural slot list
  (role + normalized bbox + typography + colors) and a compact signature
  vector. NO client text and NO client filenames are stored: slide ids are
  anonymized as golden_pair_NNN_slide_SS.

Part 2 — data/brand_template/Akkodis_Sanitized_Master_Lite.pptx (<3MB):
  Re-encodes every embedded raster with Pillow (max 1600px, JPEG q78;
  alpha images stay PNG) and placeholder-shrinks embedded videos, keeping
  100% of slides/masters/layouts/shapes/{tags}. PNG->JPEG renames update
  [Content_Types].xml and every .rels reference, so PowerPoint opens clean.
"""
from __future__ import annotations

import io
import json
import re
import sys
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

import pptx
from PIL import Image
from pptx.enum.dml import MSO_FILL
from pptx.enum.shapes import MSO_SHAPE_TYPE

PAIRS_PATH = REPO / "data" / "pairs" / "slide_alignments.jsonl"
MANIFEST_PATH = REPO / "data" / "extracted" / "ast" / "extraction_manifest.jsonl"
INDEX_PATH = REPO / "data" / "metadata" / "golden_layout_index.json"
TAGGED = REPO / "data" / "brand_template" / "Brand_guideline_Akkodis_tagged.pptx"
LITE = REPO / "data" / "brand_template" / "Akkodis_Sanitized_Master_Lite.pptx"

EMU = 914400.0


# ---------------------------------------------------------------------------
# Slot extraction (structural only — text is never stored)
# ---------------------------------------------------------------------------
def _fill_hex(shape) -> str | None:
    try:
        f = shape.fill
        if f.type == MSO_FILL.SOLID:
            c = f.fore_color
            if c.type is not None:
                return str(c.rgb)
    except Exception:
        pass
    return None


def _border_hex(shape) -> str | None:
    try:
        ln = shape.line
        if ln.fill.type == MSO_FILL.SOLID:
            return str(ln.color.rgb)
    except Exception:
        pass
    return None


def _first_font(shape):
    name = pt = None
    color = None
    try:
        for p in shape.text_frame.paragraphs:
            for r in p.runs:
                if pt is None and r.font.size:
                    pt = round(r.font.size.pt, 1)
                if name is None and r.font.name:
                    name = r.font.name
                if color is None:
                    try:
                        if r.font.color.type is not None:
                            color = str(r.font.color.rgb)
                    except Exception:
                        pass
                if pt is not None and name is not None and color is not None:
                    return name, pt, color
    except Exception:
        pass
    return name, pt, color


def extract_slots(slide, slide_w: float, slide_h: float) -> dict:
    slots: list[dict] = []
    arrows = n_images = n_tables = 0
    n_short = n_bullets = 0
    max_font = 0.0

    for shape in slide.shapes:
        st = getattr(shape, "shape_type", None)
        tag = shape._element.tag
        try:
            if st == MSO_SHAPE_TYPE.LINE or tag.endswith("}cxnSp"):
                arrows += 1
                continue
        except Exception:
            pass
        if getattr(shape, "has_table", False):
            n_tables += 1
            continue
        if st == MSO_SHAPE_TYPE.PICTURE:
            n_images += 1
            continue
        if not getattr(shape, "has_text_frame", False):
            continue
        txt = shape.text_frame.text.strip()
        if not txt or (len(txt) <= 2 and txt.isdigit()):
            continue

        left = (shape.left or 0) / EMU
        top = (shape.top or 0) / EMU
        w = (shape.width or 0) / EMU
        h = (shape.height or 0) / EMU
        font_name, font_pt, color_hex = _first_font(shape)
        if font_pt:
            max_font = max(max_font, font_pt)

        if top / max(slide_h, 0.01) < 0.25:
            role = "title" if len(txt) <= 80 else "bullet"
        elif len(txt) <= 38:
            role = "card_title"
            n_short += 1
        else:
            role = "bullet"
            n_bullets += 1

        slots.append({
            "slot_id": len(slots),
            "role": role,
            "bbox_in": [round(left, 2), round(top, 2), round(w, 2), round(h, 2)],
            "font_name": font_name,
            "font_pt": font_pt,
            "color_hex": color_hex,
            "fill_hex": _fill_hex(shape),
            "border_hex": _border_hex(shape),
        })

    n_text = len(slots)
    sig = [
        n_text / 20.0,
        n_short / 20.0,
        n_bullets / 20.0,
        min(arrows, 20) / 20.0,
        float(n_tables),
        min(n_images, 10) / 10.0,
        max_font / 72.0,
        1.0 if any(s["role"] == "title" for s in slots) else 0.0,
        n_short / max(n_text, 1),
        n_bullets / max(n_text, 1),
        1.0 if arrows >= 2 else 0.0,
        min(n_text, 30) / 30.0,
    ]
    return {
        "n_text_slots": n_text,
        "n_card_slots": n_short,
        "n_bullets": n_bullets,
        "n_images": n_images,
        "n_tables": n_tables,
        "has_table": n_tables > 0,
        "has_flow_arrows": arrows >= 2,
        "max_font_pt": round(max_font, 1),
        "signature": [round(v, 3) for v in sig],
        "slots": slots,
    }


def classify(rec: dict) -> str:
    if rec["n_images"] >= 1 and rec["n_text_slots"] <= 3:
        return "media_hero"
    if rec["has_flow_arrows"] and rec["n_card_slots"] >= 3:
        return "flow_diagram"
    if rec["n_card_slots"] >= 8:
        return "card_grid"
    if rec["n_bullets"] >= 4:
        return "bullets"
    return "content"


# ---------------------------------------------------------------------------
# Part 1: golden layout index
# ---------------------------------------------------------------------------
def build_index() -> dict:
    manifest: dict[str, dict] = {}
    for line in MANIFEST_PATH.read_text(encoding="utf-8").splitlines():
        r = json.loads(line)
        manifest[r["deck_id"]] = r

    alignments = [json.loads(l) for l in PAIRS_PATH.read_text(encoding="utf-8").splitlines()]
    entries: list[dict] = []
    deck_cache: dict[str, object] = {}
    missing = 0

    for i, al in enumerate(alignments, start=1):
        sid = al.get("branded_slide_id")
        if not sid:
            missing += 1
            continue
        deck_id = re.sub(r"__s\d+$", "", sid)
        m = manifest.get(deck_id)
        src = m.get("source") if m else None
        if not src or not Path(src).exists():
            missing += 1
            continue
        prs = deck_cache.get(deck_id)
        if prs is None:
            try:
                prs = pptx.Presentation(src)
            except Exception:
                missing += 1
                continue
            deck_cache[deck_id] = prs
        match = re.search(r"__s(\d+)$", sid)
        sno = int(match.group(1)) if match else 1
        if sno > len(prs.slides):
            missing += 1
            continue

        slide = prs.slides[sno - 1]
        w = (prs.slide_width or 0) / EMU
        h = (prs.slide_height or 0) / EMU
        rec = extract_slots(slide, w or 13.333, h or 7.5)
        rec.update({
            "id": f"golden_pair_{i:02d}_slide_{sno:02d}",
            "deck_pair_id": al.get("deck_pair_id"),
            "archetype": classify(rec),
        })
        entries.append(rec)

    # tagged master-template slides (the official layouts themselves)
    if TAGGED.exists():
        tpl = pptx.Presentation(str(TAGGED))
        w = (tpl.slide_width or 0) / EMU or 13.333
        h = (tpl.slide_height or 0) / EMU or 7.5
        for sno, slide in enumerate(tpl.slides, start=1):
            rec = extract_slots(slide, w, h)
            rec.update({
                "id": f"master_slide_{sno:02d}",
                "deck_pair_id": None,
                "archetype": "master_" + classify(rec),
            })
            entries.append(rec)

    hist: dict[str, int] = {}
    for e in entries:
        hist[e["archetype"]] = hist.get(e["archetype"], 0) + 1

    out = {
        "version": 1,
        "n_slides": len(entries),
        "archetype_histogram": hist,
        "missing_sources": missing,
        "entries": entries,
    }
    INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    INDEX_PATH.write_text(json.dumps(out, indent=1), encoding="utf-8")
    return out


# ---------------------------------------------------------------------------
# Part 2: sanitized lite master template
# ---------------------------------------------------------------------------
MIN_MP4 = (
    (24).to_bytes(4, "big") + b"ftyp" + b"isom"
    + (512).to_bytes(4, "big") + b"isomiso2"
    + (8).to_bytes(4, "big") + b"free"
)


def build_lite_template(max_dim: int = 1600, jpeg_q: int = 78) -> tuple[int, dict]:
    zin = zipfile.ZipFile(TAGGED)
    replacements: dict[str, tuple[str, bytes]] = {}
    stats = {"images": 0, "png_kept": 0, "jpeg": 0, "videos": 0, "skipped": 0}

    for item in zin.infolist():
        name = item.filename
        if not name.startswith("ppt/media/"):
            continue
        ext = name.rsplit(".", 1)[-1].lower()
        if ext == "mp4":
            replacements[name] = (name, MIN_MP4)
            stats["videos"] += 1
            continue
        if ext not in ("png", "jpg", "jpeg"):
            continue
        raw = zin.read(name)
        try:
            img = Image.open(io.BytesIO(raw))
            img.load()
        except Exception:
            stats["skipped"] += 1
            continue

        has_alpha = False
        try:
            if img.mode in ("RGBA", "LA"):
                has_alpha = img.getchannel("A").getextrema()[0] < 255
            elif img.mode == "P" and "transparency" in img.info:
                has_alpha = True
        except Exception:
            has_alpha = img.mode in ("RGBA", "LA")

        dim_cap = max_dim if not has_alpha else max(600, int(max_dim * 0.75))
        w, h = img.size
        if max(w, h) > dim_cap:
            scale = dim_cap / max(w, h)
            img = img.resize((max(1, int(w * scale)), max(1, int(h * scale))), Image.LANCZOS)

        buf = io.BytesIO()
        if has_alpha:
            img.save(buf, format="PNG", optimize=True)
            if buf.tell() > 250_000:
                try:
                    qbuf = io.BytesIO()
                    img.quantize(colors=256, method=Image.FASTOCTREE).save(qbuf, format="PNG", optimize=True)
                    if 0 < qbuf.tell() < buf.tell():
                        buf = qbuf
                        stats["quantized"] = stats.get("quantized", 0) + 1
                except Exception:
                    pass
            new_ext = "png"
            stats["png_kept"] += 1
        else:
            img.convert("RGB").save(buf, format="JPEG", quality=jpeg_q, optimize=True)
            new_ext = "jpeg"
            stats["jpeg"] += 1
        data = buf.getvalue()
        if len(data) >= item.file_size:
            stats["skipped"] += 1
            continue
        new_name = re.sub(r"\.[A-Za-z]+$", "." + new_ext, name)
        replacements[name] = (new_name, data)
        stats["images"] += 1

    renames = {old: new for old, (new, _d) in replacements.items() if new != old}

    tmp = LITE.with_suffix(".tmp")
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            if item.filename in replacements:
                new_name, data = replacements[item.filename]
                zout.writestr(new_name, data)
                continue
            data = zin.read(item.filename)
            if item.filename.endswith(".rels") and renames:
                txt = data.decode("utf-8")
                for old, new in renames.items():
                    txt = txt.replace(old.split("/")[-1], new.split("/")[-1])
                data = txt.encode("utf-8")
            elif item.filename == "[Content_Types].xml" and renames:
                txt = data.decode("utf-8")
                if any(n.endswith(".jpeg") for n in renames.values()) and 'Extension="jpeg"' not in txt:
                    txt = txt.replace("</Types>", '<Default Extension="jpeg" ContentType="image/jpeg"/></Types>')
                data = txt.encode("utf-8")
            zout.writestr(item, data)

    tmp.replace(LITE)
    return LITE.stat().st_size, stats


def build_lite_until_budget(max_mb: float = 3.0) -> dict:
    attempts = []
    final = None
    for max_dim, q in ((1600, 78), (1280, 70), (1024, 64), (900, 58)):
        size, stats = build_lite_template(max_dim, q)
        attempts.append({"max_dim": max_dim, "jpeg_q": q, "size_mb": round(size / 1e6, 2)})
        final = {"size_mb": round(size / 1e6, 2), "stats": stats, "attempts": attempts}
        if size < max_mb * 1024 * 1024:
            break
    return final or {}


if __name__ == "__main__":
    print("== building golden layout index ==", flush=True)
    idx = build_index()
    idx_size = INDEX_PATH.stat().st_size / 1e6
    print(json.dumps({
        "index_entries": idx["n_slides"],
        "index_histogram": idx["archetype_histogram"],
        "index_size_mb": round(idx_size, 2),
        "index_missing_sources": idx["missing_sources"],
    }, indent=1))

    print("== building sanitized lite template ==", flush=True)
    lite = build_lite_until_budget()
    print(json.dumps(lite, indent=1))
