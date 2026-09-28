"""FontRoleMapper: assign brand fonts by ROLE, not by guesswork.

v1 decided "is this a title?" with a bbox heuristic (`top < 1.5 and height
< 1.2`, builder.py:86) — misclassification cascaded into wrong sizes and
overflow. v2 classifies with real signals, in priority order:
  1. placeholder identity (ctrTitle/title -> heading; body/subTitle -> body)
  2. explicit run size (>= 16pt -> heading)
  3. fallback -> body

Writes latin + east-asian + complex-script typefaces (python-pptx's
`font.name` only sets latin, so CJK decks would silently keep the old font —
diagnosis-adjacent defect caught during design).
"""

from __future__ import annotations

from lxml import etree
from pptx import Presentation

from ..brand.profile import BrandDNA
from ..report import ChangeEntry, MorphReport

_A = "http://schemas.openxmlformats.org/drawingml/2006/main"

_HEADING_PH = {"title", "ctrTitle"}
_BODY_PH = {"body", "subTitle", "sldNum", "ftr", "dt", "obj"}
_HEADING_SIZE_PT_HUNDREDS = 1600  # >= 16pt counts as heading text


def _local(el) -> str:
    return etree.QName(el).localname


class FontRoleMapper:
    def __init__(self, dna: BrandDNA, report: MorphReport):
        self.dna = dna
        self.report = report

    def run(self, prs: Presentation) -> None:
        for master in prs.slide_masters:
            self._sweep(master.element, f"master:{master.name or 'default'}")
            for layout in master.slide_layouts:
                self._sweep(layout.element, f"layout:{layout.name}")
        for idx, slide in enumerate(prs.slides):
            self._sweep(slide.element, f"slide:{idx}", slide_idx=idx)

    def _sweep(self, root, label: str, slide_idx: int | None = None) -> None:
        for latin in list(root.iter(f"{{{_A}}}latin")):
            parent = latin.getparent()
            if parent is None or _local(parent) not in ("rPr", "defRPr", "endParaRPr"):
                continue
            current = latin.get("typeface") or ""
            if current in (self.dna.typography.heading.family, self.dna.typography.body.family):
                continue  # already brand (idempotence)
            if current in self.dna.rules.preserve_display_fonts:
                continue
            role = self._role(latin)
            family = (
                self.dna.typography.heading.family
                if role == "heading"
                else self.dna.typography.body.family
            )
            latin.set("typeface", family)
            self._set_script_faces(parent, family, role)
            self.report.add(ChangeEntry(
                stage="font", slide=slide_idx, element=label, kind="font",
                before=current or "(inherited)", after=family, role=role,
            ))

    def _role(self, latin_el) -> str:
        for anc in latin_el.iterancestors():
            name = _local(anc)
            if name == "ph":
                ph_type = anc.get("type") or "obj"
                if ph_type in _HEADING_PH:
                    return "heading"
                return "body"
            if name == "sp":
                break  # reached the shape without a placeholder -> size heuristic
        sz = latin_el.getparent().get("sz")
        if sz:
            try:
                if int(sz) >= _HEADING_SIZE_PT_HUNDREDS:
                    return "heading"
            except ValueError:
                pass
        return "body"

    def _set_script_faces(self, rpr_el, family: str, role: str) -> None:
        """Create/update a:ea and a:cs so CJK/Arabic/Hebrew runs follow too."""
        latin = rpr_el.find(f"{{{_A}}}latin")
        if latin is None:
            return
        for tag in ("ea", "cs"):
            el = rpr_el.find(f"{{{_A}}}{tag}")
            if el is None:
                el = etree.Element(f"{{{_A}}}{tag}")
                latin.addnext(el) if tag == "ea" else (
                    rpr_el.find(f"{{{_A}}}ea").addnext(el)
                    if rpr_el.find(f"{{{_A}}}ea") is not None
                    else latin.addnext(el)
                )
            el.set("typeface", family)
