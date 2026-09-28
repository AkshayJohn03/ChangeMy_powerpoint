"""Theme surgery: schemeClr elements must pick up brand DNA via theme1.xml."""

import zipfile

from brandmorph.engine.pipeline import MorphOptions, MorphPipeline


def _theme_xml(path):
    with zipfile.ZipFile(path) as z:
        return z.read("ppt/theme/theme1.xml").decode("utf-8")


def test_theme_scheme_rewritten(tmp_path, akkodis):
    from conftest import build_themed

    src = build_themed(tmp_path / "themed.pptx")
    out = tmp_path / "out.pptx"
    report = MorphPipeline(akkodis, options=MorphOptions()).run(src, out)

    xml = _theme_xml(out)
    assert "FFB81C" in xml, "accent1 slot should carry the brand gold"
    assert "030C1E" in xml, "lt1... dk2 slot should carry the brand surface"
    assert 'typeface="Arial"' in xml, "majorFont (heading) -> brand heading family"
    assert 'typeface="Segoe UI"' in xml, "minorFont (body) -> brand body family"

    theme_entries = [e for e in report.entries if e.stage == "theme"]
    assert theme_entries, "theme changes must be logged"


def test_theme_fonts_replaced(tmp_path, corporate_light):
    from conftest import build_themed

    src = build_themed(tmp_path / "themed.pptx")
    out = tmp_path / "out_light.pptx"
    MorphPipeline(corporate_light, options=MorphOptions()).run(src, out)

    xml = _theme_xml(out)
    assert 'typeface="Georgia"' in xml  # corporate_light heading
    assert 'typeface="Calibri"' in xml  # corporate_light body


def test_theme_idempotent(tmp_path, akkodis):
    from conftest import build_themed

    src = build_themed(tmp_path / "themed.pptx")
    out1 = tmp_path / "pass1.pptx"
    out2 = tmp_path / "pass2.pptx"
    MorphPipeline(akkodis, options=MorphOptions()).run(src, out1)
    report2 = MorphPipeline(akkodis, options=MorphOptions()).run(out1, out2)
    assert report2.counts_by_stage.get("theme", 0) == 0
