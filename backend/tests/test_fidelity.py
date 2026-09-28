"""Fidelity sentinels: v1 destroyed charts/tables/groups/pictures (defect D1);
v2 must preserve them bit-for-bit."""

from brandmorph.engine.analyzer import analyze
from brandmorph.engine.pipeline import MorphOptions, MorphPipeline


def test_mixed_deck_content_preserved(tmp_path, akkodis):
    from conftest import build_mixed

    src = build_mixed(tmp_path / "mixed.pptx")
    out = tmp_path / "out.pptx"
    MorphPipeline(akkodis, options=MorphOptions()).run(src, out)

    before, after = analyze(src), analyze(out)
    assert before["slide_count"] == after["slide_count"]
    for b, a in zip(before["slides"], after["slides"]):
        for key in ("shape_count", "charts", "tables", "pictures", "text_shapes"):
            assert b[key] == a[key], f"{key} changed: {b[key]} -> {a[key]}"
    # the picture is the same bytes (never re-encoded)
    if before["image_hashes"]:
        assert before["image_hashes"] == after["image_hashes"]


def test_chart_series_recolored(tmp_path, akkodis):
    from conftest import build_mixed

    from brandmorph.brand.profile import PALETTE_ROLES

    src = build_mixed(tmp_path / "mixed.pptx")
    out = tmp_path / "out.pptx"
    report = MorphPipeline(akkodis, options=MorphOptions()).run(src, out)

    palette_hexes = {
        getattr(akkodis.palette, role).hex for role in PALETTE_ROLES
    }
    chart_entries = [e for e in report.entries if "chart" in e.element]
    assert chart_entries, "explicit chart colors must be mapped"
    for e in chart_entries:
        assert e.after in palette_hexes


def test_table_cell_recolored(tmp_path, akkodis):
    from conftest import build_mixed

    src = build_mixed(tmp_path / "mixed.pptx")
    out = tmp_path / "out.pptx"
    report = MorphPipeline(akkodis, options=MorphOptions()).run(src, out)

    cell_entries = [e for e in report.entries if e.role in ("surface", "surface_alt", "background")]
    assert cell_entries, "explicit table-cell fill must be mapped to a surface role"


def test_grouped_shapes_survive(tmp_path, akkodis):
    from conftest import build_mixed
    from pptx import Presentation
    from pptx.enum.shapes import MSO_SHAPE_TYPE

    src = build_mixed(tmp_path / "mixed.pptx")
    out = tmp_path / "out.pptx"
    MorphPipeline(akkodis, options=MorphOptions()).run(src, out)

    prs = Presentation(str(out))
    groups = [
        shp for shp in prs.slides[0].shapes if shp.shape_type == MSO_SHAPE_TYPE.GROUP
    ]
    assert groups, "group shapes must survive the morph"
    inner_text = [sh.text_frame.text for sh in groups[0].shapes
                  if getattr(sh, "has_text_frame", False) and sh.has_text_frame]
    assert any("Grouped note" in t for t in inner_text)
