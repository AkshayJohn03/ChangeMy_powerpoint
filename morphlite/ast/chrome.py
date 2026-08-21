"""Deck-chrome extraction at zip level (no python-pptx).

Captures the layers where the Akkodis transformation actually lives:
    - theme palettes + fonts          ppt/theme/*.xml
    - master -> theme wiring          ppt/slideMasters/*
    - layout names                    ppt/slideLayouts/*
    - per-slide layout reference      slide rels
    - per-slide background fill       <p:bg> solid/blip (+ image hash)
    - per-slide <p:style> theme refs  fillRef / lnRef / fontRef / effectRef
"""
from __future__ import annotations

import hashlib
import re
import zipfile
from collections import Counter
from xml.etree import ElementTree as ET

NS_A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
NS_P = "{http://schemas.openxmlformats.org/presentationml/2006/main}"
NS_R = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"

_THEME_RE = re.compile(r"^ppt/theme/(theme\d+)\.xml$")


def _parse(zf: zipfile.ZipFile, part: str):
    try:
        return ET.fromstring(zf.read(part))
    except Exception:
        return None


def _rels(zf: zipfile.ZipFile, part: str) -> dict[str, str]:
    folder, fname = part.rsplit("/", 1)
    path = f"{folder}/_rels/{fname}.rels"
    if path not in zf.namelist():
        return {}
    root = _parse(zf, path)
    if root is None:
        return {}
    return {rel.get("Id"): rel.get("Target") for rel in root}


def _resolve(base_dir: str, target: str) -> str:
    parts = (base_dir + "/" + target).split("/")
    out: list[str] = []
    for p in parts:
        if p == "..":
            if out:
                out.pop()
        elif p not in ("", "."):
            out.append(p)
    return "/".join(out)


def theme_palettes(zf: zipfile.ZipFile) -> dict:
    out = {}
    for name in zf.namelist():
        m = _THEME_RE.match(name)
        if not m:
            continue
        root = _parse(zf, name)
        if root is None:
            continue
        scheme = root.find(f".//{NS_A}clrScheme")
        palette = {}
        if scheme is not None:
            for child in scheme:
                tag = child.tag.split("}")[1]
                srgb = child.find(f"{NS_A}srgbClr")
                sysc = child.find(f"{NS_A}sysClr")
                if srgb is not None:
                    palette[tag] = (srgb.get("val") or "").upper()
                elif sysc is not None:
                    last = sysc.get("lastClr")
                    palette[tag] = (last or sysc.get("val") or "").upper()
        fonts = {}
        for font_tag in ("majorFont", "minorFont"):
            el = root.find(f".//{NS_A}{font_tag}/{NS_A}latin")
            fonts[font_tag] = el.get("typeface") if el is not None else None
        out[m.group(1)] = {"palette": palette, "fonts": fonts}
    return out


def _bg_info(zf: zipfile.ZipFile, slide_part: str, root) -> dict | None:
    bg = root.find(f"{NS_P}cSld/{NS_P}bg")
    if bg is None:
        return None
    bg_pr = bg.find(f"{NS_P}bgPr")
    if bg_pr is None:
        return None
    solid = bg_pr.find(f".//{NS_A}solidFill/{NS_A}srgbClr")
    if solid is not None:
        return {"type": "solid", "color": (solid.get("val") or "").upper(), "image_md5_8": None}
    blip = bg_pr.find(f".//{NS_A}blipFill/{NS_A}blip")
    if blip is not None:
        rid = blip.get(f"{NS_R}embed")
        target = _resolve("ppt/slides", _rels(zf, slide_part).get(rid, ""))
        digest = None
        if target and target in zf.namelist():
            digest = hashlib.md5(zf.read(target)).hexdigest()[:8]
        return {"type": "picture", "color": None, "image_md5_8": digest}
    return {"type": "inherit_or_other", "color": None, "image_md5_8": None}


def _style_refs(root) -> dict:
    fills: dict = {}
    schemes: dict = {}
    for style in root.iter(f"{NS_P}style"):
        for child in style:
            tag = child.tag.split("}")[1]
            idx = child.get("idx")
            key = f"{tag}[{idx}]"
            fills[key] = fills.get(key, 0) + 1
            scheme = child.find(f"{NS_A}srgbClr")
            scheme_ref = child.find(f"{NS_A}schemeClr")
            if scheme_ref is not None:
                sv = scheme_ref.get("val")
                schemes[f"{tag}->{sv}"] = schemes.get(f"{tag}->{sv}", 0) + 1
            elif scheme is not None:
                schemes[f"{tag}->#{(scheme.get('val') or '').upper()}"] = schemes.get(f"{tag}->#{(scheme.get('val') or '').upper()}", 0) + 1

    def top(d, n=6):
        return dict(sorted(d.items(), key=lambda kv: -kv[1])[:n])

    return {"refs": top(fills), "scheme_targets": top(schemes)}


def _find_ph(sp):
    return sp.find(f"{NS_P}nvSpPr/{NS_P}nvPr/{NS_P}ph")


def _q(v) -> int | None:
    try:
        return int(round(int(v) / 360000))
    except Exception:
        return None


def _layout_structure(root) -> dict:
    topo = []
    counts = Counter()
    for child in root.iter():
        tag = child.tag.split("}")[-1]
        if tag in ("sp", "pic", "graphicFrame", "cxnSp", "grpSp"):
            counts[tag] += 1
    for sp in root.iter(f"{NS_P}sp"):
        ph = _find_ph(sp)
        if ph is None:
            continue
        xfrm = sp.find(f"{NS_P}spPr/{NS_A}xfrm")
        if xfrm is None:
            off = ext = None
        else:
            off = xfrm.find(f"{NS_A}off")
            ext = xfrm.find(f"{NS_A}ext")
        row = [
            ph.get("type") or "obj",
            _q(off.get("x")) if off is not None else None,
            _q(off.get("y")) if off is not None else None,
            _q(ext.get("cx")) if ext is not None else None,
            _q(ext.get("cy")) if ext is not None else None,
        ]
        topo.append("|".join(str(v) for v in row))
    return {"ph_topology": sorted(topo), "shape_counts": dict(counts)}


def _master_ladders(root) -> dict:
    out = {}
    ts = root.find(f"{NS_P}txStyles")
    if ts is None:
        return out
    for name in ("titleStyle", "bodyStyle", "otherStyle"):
        el = ts.find(f"{NS_P}{name}")
        sizes = []
        if el is not None:
            for child in el.iter(f"{NS_A}defRPr"):
                sz = child.get("sz")
                if sz:
                    try:
                        sizes.append(round(int(sz) / 100.0, 1))
                    except ValueError:
                        pass
        out[name] = sorted(set(sizes))
    return out


def extract_chrome(pptx_path: str) -> dict:
    with zipfile.ZipFile(pptx_path) as zf:
        names = set(zf.namelist())
        themes = theme_palettes(zf)

        masters_meta = {}
        for name in sorted(n for n in names if re.match(r"ppt/slideMasters/slideMaster\d+\.xml$", n)):
            rels = _rels(zf, name)
            theme_target = next((t for t in rels.values() if "theme" in t), None)
            masters_meta[name] = {
                "theme": _resolve("ppt/slideMasters", theme_target).split("/")[-1] if theme_target else None
            }

        layouts_meta = {}
        for name in sorted(n for n in names if re.match(r"ppt/slideLayouts/slideLayout\d+\.xml$", n)):
            root = _parse(zf, name)
            lname = None
            structure = {"ph_topology": [], "shape_counts": {}}
            if root is not None:
                csld = root.find(f"{NS_P}cSld")
                lname = csld.get("name") if csld is not None else None
                structure = _layout_structure(root)
            rels_map = _rels(zf, name)
            master = ""
            mt_target = next((t for t in rels_map.values() if "slideMaster" in t), None)
            if mt_target:
                master = _resolve("ppt/slideLayouts", mt_target).split("/")[-1]
            layouts_meta[name.split("/")[-1]] = {"name": lname, "master": master or None, **structure}

        masters_ladders = {}
        for mname in sorted(n for n in names if re.match(r"ppt/slideMasters/slideMaster\d+\.xml$", n)):
            mroot = _parse(zf, mname)
            if mroot is not None:
                masters_ladders[mname.split("/")[-1]] = _master_ladders(mroot)

        slide_parts = sorted(
            (n for n in names if re.match(r"ppt/slides/slide\d+\.xml$", n)),
            key=lambda n: int(re.search(r"(\d+)", n).group(1)),
        )
        slides = []
        for i, sp in enumerate(slide_parts, 1):
            root = _parse(zf, sp)
            rec = {"index": i, "layout": None, "background": None, "style_refs": {}, "scheme_targets": {}}
            if root is not None:
                rels = _rels(zf, sp)
                layout_target = next((t for t in rels.values() if "slideLayout" in t), None)
                if layout_target:
                    lf = _resolve("ppt/slides", layout_target).split("/")[-1]
                    meta = layouts_meta.get(lf, {})
                    rec["layout"] = meta.get("name") or lf
                    rec["layout_master"] = meta.get("master")
                rec["background"] = _bg_info(zf, sp, root)
                refs = _style_refs(root)
                rec["style_refs"] = refs["refs"]
                rec["scheme_targets"] = refs["scheme_targets"]
            slides.append(rec)

    return {
        "chrome_version": "1.1.0",
        "themes": themes,
        "masters": masters_meta,
        "master_ladders": masters_ladders,
        "layouts": layouts_meta,
        "slides": slides,
    }
