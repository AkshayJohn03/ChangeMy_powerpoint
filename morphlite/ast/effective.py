"""Effective-property resolution through the PowerPoint inheritance chain.

    run -> paragraph default -> shape lstStyle -> layout placeholder ->
    master placeholder -> master txStyles -> theme fonts -> unresolved

Zip/XML level, read-only. Per-run chain resolution, aggregated to shape
level by majority vote with recorded origin + confidence per field.
"""
from __future__ import annotations

import re
import zipfile
from collections import Counter, defaultdict
from xml.etree import ElementTree as ET

NS_A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
NS_P = "{http://schemas.openxmlformats.org/presentationml/2006/main}"

CONF = {
    "run": 0.99,
    "paragraph_default": 0.92,
    "shape_list_style": 0.88,
    "layout_placeholder": 0.72,
    "master_placeholder": 0.66,
    "master_title_style": 0.62,
    "master_body_style": 0.62,
    "master_other_style": 0.58,
    "theme": 0.55,
}

STYLE_FOR_PH = {
    "title": "titleStyle",
    "ctrTitle": "titleStyle",
    "body": "bodyStyle",
    "subTitle": "bodyStyle",
}
FIELDS = ("size", "bold", "italic", "color", "family")


def _parse(zf, part):
    try:
        return ET.fromstring(zf.read(part))
    except Exception:
        return None


def _rels(zf, part):
    folder, fname = part.rsplit("/", 1)
    path = f"{folder}/_rels/{fname}.rels"
    if path not in zf.namelist():
        return {}
    root = _parse(zf, path)
    return {r.get("Id"): r.get("Target") for r in root} if root is not None else {}


def _resolve_target(base, target):
    parts = (base + "/" + target).split("/")
    out = []
    for p in parts:
        if p == "..":
            if out:
                out.pop()
        elif p not in ("", "."):
            out.append(p)
    return "/".join(out)


def _color_from_fill(fill_el, clr_map, palette):
    if fill_el is None:
        return None
    srgb = fill_el.find(f"{NS_A}srgbClr")
    if srgb is not None:
        return (srgb.get("val") or "").upper()
    scheme = fill_el.find(f"{NS_A}schemeClr")
    if scheme is not None:
        token = scheme.get("val")
        mapped = clr_map.get(token, token) if clr_map else token
        hexval = palette.get(mapped)
        if hexval:
            tinted = scheme.find(f"{NS_A}lumMod") is not None or scheme.find(f"{NS_A}lumOff") is not None
            return hexval + "~tinted" if tinted else hexval
    return None


def _read_props(el, clr_map, palette):
    """Read size/bold/italic/color/family directly from an rPr/defRPr element."""
    if el is None:
        return {}
    out = {}
    sz = el.get("sz")
    if sz:
        try:
            out["size"] = round(int(sz) / 100.0, 2)
        except ValueError:
            pass
    b, i = el.get("b"), el.get("i")
    if b is not None:
        out["bold"] = b in ("1", "true")
    if i is not None:
        out["italic"] = i in ("1", "true")
    color = _color_from_fill(el.find(f"{NS_A}solidFill"), clr_map, palette)
    if color:
        out["color"] = color
    latin = el.find(f"{NS_A}latin")
    if latin is not None and latin.get("typeface"):
        out["family"] = latin.get("typeface")
    return out


def _style_levels(style_el, clr_map, palette):
    levels = {}
    if style_el is None:
        return levels
    for child in style_el:
        m = re.match(rf"{re.escape(NS_A)}lvl(\d)pPr$", child.tag)
        if not m:
            continue
        props = _read_props(child.find(f"{NS_A}defRPr"), clr_map, palette)
        if props:
            levels[int(m.group(1)) - 1] = props
    return levels


def _ph_key(ph_el):
    if ph_el is None:
        return None
    return (ph_el.get("type") or "obj", ph_el.get("idx") or "0")


def _find_ph(sp):
    return sp.find(f"{NS_P}nvSpPr/{NS_P}nvPr/{NS_P}ph")

FIELD_KEY = {"size": "font_size_pt", "bold": "bold", "italic": "italic", "color": "color", "family": "font_family"}


class DeckTypographyResolver:
    def __init__(self, pptx_path: str):
        self.zf = zipfile.ZipFile(pptx_path)
        names = self.zf.namelist()
        self.slide_parts = sorted(
            (n for n in names if re.match(r"ppt/slides/slide\d+\.xml$", n)),
            key=lambda n: int(re.search(r"(\d+)", n).group(1)),
        )
        self._layouts = {}
        self._masters = {}

    def close(self):
        self.zf.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    def _layout(self, slide_part):
        if slide_part not in self._layouts:
            target = next((t for t in _rels(self.zf, slide_part).values() if "slideLayout" in t), None)
            part = _resolve_target("ppt/slides", target) if target else None
            data = {"phs": {}, "master_part": None}
            if part and part in self.zf.namelist():
                root = _parse(self.zf, part)
                if root is not None:
                    for sp in root.iter(f"{NS_P}sp"):
                        key = _ph_key(_find_ph(sp))
                        if key and key not in data["phs"]:
                            data["phs"][key] = _style_levels(
                                sp.find(f"{NS_P}txBody/{NS_A}lstStyle"), {}, {}
                            )
                    mt = next((t for t in _rels(self.zf, part).values() if "slideMaster" in t), None)
                    data["master_part"] = _resolve_target("ppt/slideLayouts", mt) if mt else None
            self._layouts[slide_part] = data
        return self._layouts[slide_part]

    def _master(self, master_part):
        if master_part not in self._masters:
            data = {"phs": {}, "txstyles": {}, "clr_map": {}, "palette": {}, "fonts": {}}
            if master_part and master_part in self.zf.namelist():
                root = _parse(self.zf, master_part)
                if root is not None:
                    cm = root.find(f"{NS_P}clrMap")
                    if cm is not None:
                        data["clr_map"] = dict(cm.attrib)
                    ts = root.find(f"{NS_P}txStyles")
                    if ts is not None:
                        for name in ("titleStyle", "bodyStyle", "otherStyle"):
                            el = ts.find(f"{NS_P}{name}")
                            data["txstyles"][name] = _style_levels(el, data["clr_map"], data["palette"])
                    for sp in root.iter(f"{NS_P}sp"):
                        key = _ph_key(_find_ph(sp))
                        if key and key not in data["phs"]:
                            data["phs"][key] = _style_levels(
                                sp.find(f"{NS_P}txBody/{NS_A}lstStyle"), data["clr_map"], data["palette"]
                            )
                    tt = next((t for t in _rels(self.zf, master_part).values() if "theme" in t), None)
                    if tt:
                        theme_part = _resolve_target("ppt/slideMasters", tt)
                        troot = _parse(self.zf, theme_part)
                        if troot is not None:
                            scheme = troot.find(f".//{NS_A}clrScheme")
                            if scheme is not None:
                                for child in scheme:
                                    tag = child.tag.split("}")[1]
                                    srgb = child.find(f"{NS_A}srgbClr")
                                    sysc = child.find(f"{NS_A}sysClr")
                                    if srgb is not None:
                                        data["palette"][tag] = (srgb.get("val") or "").upper()
                                    elif sysc is not None:
                                        data["palette"][tag] = (sysc.get("lastClr") or "").upper()
                            fs = troot.find(f".//{NS_A}fontScheme")
                            if fs is not None:
                                for tag in ("majorFont", "minorFont"):
                                    el = fs.find(f"{NS_A}{tag}/{NS_A}latin")
                                    data["fonts"][tag] = el.get("typeface") if el is not None else None
            self._masters[master_part] = data
        return self._masters[master_part]

    def _resolve_run(self, rpr, para_def, lvl, ctx):
        shape_levels = ctx["shape_levels"]
        lay_levels = ctx["lay_levels"]
        mas_levels = ctx["mas_levels"]
        txlevels = ctx["txlevels"]
        fonts = ctx["fonts"]
        titleish = ctx["titleish"]
        style_name = ctx["style_name"]
        chain = [
            ("paragraph_default", para_def),
            ("shape_list_style", shape_levels.get(lvl)),
            ("layout_placeholder", lay_levels.get(lvl)),
            ("master_placeholder", mas_levels.get(lvl)),
            ({"titleStyle": "master_title_style", "bodyStyle": "master_body_style"}.get(style_name, "master_other_style"), txlevels.get(lvl)),
        ]
        out = {}
        direct = _read_props(rpr, ctx["clr_map"], ctx["palette"])
        for f in FIELDS:
            val, origin = None, "unresolved"
            if f in direct:
                val, origin = direct[f], "run"
            else:
                for org_name, props in chain:
                    if props and f in props:
                        val, origin = props[f], org_name
                        break
            if f == "family" and isinstance(val, str) and val.startswith(("+mn", "+mj")):
                resolved = fonts.get("majorFont" if val.startswith("+mj") else "minorFont")
                if resolved:
                    val = resolved
                    origin = "theme" if origin != "run" else "run"
            elif f == "family" and val is None:
                fallback = fonts.get("majorFont" if titleish else "minorFont")
                if fallback:
                    val, origin = fallback, "theme"
            if f == "size" and val is None:
                continue
            out[f] = (val, origin)
        return out

    def resolve_slide(self, slide_index: int) -> dict:
        """Returns {shape_id: {font_<field>: {value, origin, confidence}, _n_runs}}."""
        part = self.slide_parts[slide_index]
        root = _parse(self.zf, part)
        result = {}
        if root is None:
            return result
        lay = self._layout(part)
        mas = self._master(lay.get("master_part"))

        for sp in root.iter(f"{NS_P}sp"):
            nv = sp.find(f"{NS_P}nvSpPr/{NS_P}cNvPr")
            sid = nv.get("id") if nv is not None else None
            tx = sp.find(f"{NS_P}txBody")
            if sid is None or tx is None:
                continue
            ph_key = _ph_key(_find_ph(sp))
            style_name = STYLE_FOR_PH.get(ph_key[0], "otherStyle") if ph_key else "otherStyle"
            ctx = {
                "shape_levels": _style_levels(tx.find(f"{NS_A}lstStyle"), mas["clr_map"], mas["palette"]),
                "lay_levels": (lay["phs"].get(ph_key) or {}) if ph_key else {},
                "mas_levels": (mas["phs"].get(ph_key) or {}) if ph_key else {},
                "txlevels": mas["txstyles"].get(style_name, {}),
                "style_name": style_name,
                "fonts": mas["fonts"],
                "clr_map": mas["clr_map"],
                "palette": mas["palette"],
                "titleish": bool(ph_key and ph_key[0] in ("title", "ctrTitle")),
            }

            field_votes = defaultdict(lambda: defaultdict(Counter))
            run_count = 0
            for p in tx.findall(f"{NS_A}p"):
                ppr = p.find(f"{NS_A}pPr")
                lvl_raw = ppr.get("lvl") if ppr is not None else None
                lvl = int(lvl_raw) if lvl_raw not in (None, "") else 0
                para_def = _read_props(ppr.find(f"{NS_A}defRPr"), mas["clr_map"], mas["palette"]) if ppr is not None else {}
                runs = p.findall(f"{NS_A}r")

                targets = runs if runs else [None]
                for r in targets:
                    run_count += 1
                    rpr = r.find(f"{NS_A}rPr") if r is not None else None
                    resolved = self._resolve_run(rpr, para_def, lvl, ctx)
                    for f, (val, origin) in resolved.items():
                        if val is not None:
                            field_votes[f][origin][val] += 1

            shape_out = {"_n_runs": run_count}
            for f in FIELDS:
                origin_votes = field_votes.get(f)
                if not origin_votes:
                    continue
                combined = Counter()
                origin_of_value = {}
                for origin, values in origin_votes.items():
                    for val, n in values.items():
                        combined[val] += n
                        origin_of_value.setdefault(val, Counter())[origin] += n
                value, support = combined.most_common(1)[0]
                origin = origin_of_value[value].most_common(1)[0][0]
                shape_out[FIELD_KEY[f]] = {
                    "value": value,
                    "origin": origin,
                    "confidence": CONF.get(origin, 0.4),
                    "support": support,
                }
            if len(shape_out) > 1:
                result[sid] = shape_out
        return result
