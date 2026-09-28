"""ThemeTransformer: rewrite the OOXML theme parts inside a saved .pptx.

python-pptx cannot reach `ppt/theme/theme1.xml`, so this stage operates at the
zip/XML level after the python-pptx passes have saved. Rewriting the clrScheme
and fontScheme is what makes every theme-referenced element (schemeClr) update
at once — the pass that makes a morphed deck look *native* instead of repainted.

Slot mapping (design §2.1 ③):
  dk1 -> text_primary   lt1 -> background   dk2 -> surface   lt2 -> surface_alt
  accent1 -> accent_primary   accent2 -> accent_secondary
  accent3..6 -> hue-true Lab lightness ladder of accent_primary
  hlink -> link   folHlink -> text_muted

lxml (not ElementTree) is used because theme parts carry several namespace
declarations referenced by mc:Ignorable; lxml preserves them verbatim.
"""

from __future__ import annotations

import shutil
import tempfile
import zipfile
from pathlib import Path

from lxml import etree

from ..brand.profile import BrandDNA
from ..report import ChangeEntry, MorphReport
from .colorutil import shade
from .safety import safe_fromstring

_A = "http://schemas.openxmlformats.org/drawingml/2006/main"
_NS = {"a": _A}

CLR_SLOTS = {
    "dk1": "text_primary",
    "lt1": "background",
    "dk2": "surface",
    "lt2": "surface_alt",
    "accent1": "accent_primary",
    "accent2": "accent_secondary",
    "hlink": "link",
    "folHlink": "text_muted",
}
# hue-true lightness ladder off accent_primary — tints/shades, never new hues
SHADE_LADDER = {"accent3": 12.0, "accent4": 6.0, "accent5": -6.0, "accent6": -12.0}


def _slot_hex(dna: BrandDNA, slot: str) -> str:
    if slot in SHADE_LADDER:
        return shade(dna.palette.accent_primary.hex, SHADE_LADDER[slot])
    return getattr(dna.palette, CLR_SLOTS[slot]).hex


def _current_hex(slot_el) -> str | None:
    for child in slot_el:
        tag = etree.QName(child).localname
        if tag == "srgbClr":
            return (child.get("val") or "").upper()
        if tag == "sysClr":
            last = child.get("lastClr")
            if last:
                return last.upper()
    return None


def transform_theme_bytes(
    xml_bytes: bytes,
    dna: BrandDNA,
    theme_name: str,
    report: MorphReport | None = None,
) -> bytes:
    root = safe_fromstring(xml_bytes)

    scheme = root.find(".//a:clrScheme", _NS)
    if scheme is not None:
        for slot_el in list(scheme):
            slot = etree.QName(slot_el).localname
            if slot not in CLR_SLOTS and slot not in SHADE_LADDER:
                continue
            before = _current_hex(slot_el) or "??????"
            target = _slot_hex(dna, slot)
            if before != target:
                for child in list(slot_el):
                    slot_el.remove(child)
                srgb = etree.SubElement(slot_el, f"{{{_A}}}srgbClr")
                srgb.set("val", target)
                if report is not None:
                    report.add(ChangeEntry(
                        stage="theme", slide=None,
                        element=f"{theme_name}#{slot}", kind="color",
                        before=before, after=target,
                        role=CLR_SLOTS.get(slot, "accent_shade"),
                    ))

    fontscheme = root.find(".//a:fontScheme", _NS)
    if fontscheme is not None:
        for scope, spec in (
            ("majorFont", dna.typography.heading),
            ("minorFont", dna.typography.body),
        ):
            el = fontscheme.find(f"a:{scope}", _NS)
            if el is None:
                continue
            for face in ("latin", "ea", "cs"):
                fe = el.find(f"a:{face}", _NS)
                if fe is None:
                    continue
                if fe.get("typeface") != spec.family:
                    before = fe.get("typeface") or ""
                    fe.set("typeface", spec.family)
                    if report is not None:
                        report.add(ChangeEntry(
                            stage="theme", slide=None,
                            element=f"{theme_name}#{scope}/{face}", kind="font",
                            before=before, after=spec.family,
                            role="heading" if scope == "majorFont" else "body",
                        ))

    return etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)


def transform(path: str | Path, dna: BrandDNA, report: MorphReport | None = None) -> None:
    """Rewrite every ppt/theme/*.xml part inside the pptx zip, in place."""
    src = Path(path)
    fd, tmp_name = tempfile.mkstemp(suffix=".pptx", dir=str(src.parent))
    import os

    os.close(fd)
    try:
        with zipfile.ZipFile(src, "r") as zin, \
                zipfile.ZipFile(tmp_name, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                data = zin.read(item.filename)
                if item.filename.startswith("ppt/theme/") and item.filename.endswith(".xml"):
                    try:
                        data = transform_theme_bytes(
                            data, dna, item.filename.rsplit("/", 1)[-1], report
                        )
                    except etree.XMLSyntaxError:
                        pass  # leave unknown/unparseable theme parts untouched
                zout.writestr(item, data)
        shutil.move(tmp_name, str(src))
    except Exception:
        Path(tmp_name).unlink(missing_ok=True)
        raise
