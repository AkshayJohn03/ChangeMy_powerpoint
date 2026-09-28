"""DirectFormatMapper: role-preserving explicit color mapping."""

from pptx import Presentation

from brandmorph.engine.pipeline import MorphOptions, MorphPipeline


def _runs(path):
    prs = Presentation(str(path))
    out = []
    for slide in prs.slides:
        for shape in slide.shapes:
            if getattr(shape, "has_text_frame", False) and shape.has_text_frame:
                for p in shape.text_frame.paragraphs:
                    for r in p.runs:
                        if r.font.color and r.font.color.type is not None:
                            try:
                                out.append((r.text, str(r.font.color.rgb)))
                            except Exception:
                                pass
    return out


def test_white_on_dark_is_perceptually_brand_and_left_alone(tmp_path, akkodis):
    """Brand text_primary (F2F6FC) is dE 4.7 from pure white — inside the
    idempotence band, so white ink on a dark deck is correctly treated as
    already-on-brand and left untouched (perceptual mapping, not literal)."""
    from conftest import build_hardcoded

    src = build_hardcoded(tmp_path / "deck.pptx")
    out = tmp_path / "out.pptx"
    MorphPipeline(akkodis, options=MorphOptions()).run(src, out)

    colors = dict(_runs(out))
    assert colors["Quarterly Business Review"] == "FFFFFF"


def test_dim_gray_maps_to_text_muted(tmp_path, akkodis):
    from conftest import build_hardcoded

    src = build_hardcoded(tmp_path / "deck.pptx")
    out = tmp_path / "out.pptx"
    report = MorphPipeline(akkodis, options=MorphOptions()).run(src, out)

    colors = dict(_runs(out))
    assert colors["Footer note, low emphasis"] == "93A5C4"
    entry = next(e for e in report.entries if e.role == "text_muted")
    assert entry.stage == "format"


def test_red_maps_to_danger_not_random(tmp_path, akkodis):
    from conftest import build_hardcoded

    src = build_hardcoded(tmp_path / "deck.pptx")
    out = tmp_path / "out.pptx"
    MorphPipeline(akkodis, options=MorphOptions()).run(src, out)

    colors = dict(_runs(out))
    assert colors["Margin alert"] == "E5484D"


def test_already_brand_color_untouched(tmp_path, akkodis):
    from conftest import build_hardcoded

    src = build_hardcoded(tmp_path / "deck.pptx")
    out = tmp_path / "out.pptx"
    MorphPipeline(akkodis, options=MorphOptions()).run(src, out)

    colors = dict(_runs(out))
    assert colors["Already on brand"] == "FFB81C"


def test_mapping_idempotent(tmp_path, akkodis):
    from conftest import build_hardcoded

    src = build_hardcoded(tmp_path / "deck.pptx")
    out1 = tmp_path / "pass1.pptx"
    out2 = tmp_path / "pass2.pptx"
    MorphPipeline(akkodis, options=MorphOptions()).run(src, out1)
    report2 = MorphPipeline(akkodis, options=MorphOptions()).run(out1, out2)
    assert report2.counts_by_stage.get("format", 0) == 0


def test_glossary_and_banned_words(tmp_path, akkodis):
    from conftest import build_hardcoded

    src = build_hardcoded(tmp_path / "deck.pptx")
    out = tmp_path / "out.pptx"
    report = MorphPipeline(akkodis, options=MorphOptions()).run(src, out)

    texts = [t for t, _ in _runs(out)]
    assert any("Utilize" not in t and "use new tooling" in t for t in texts), \
        "glossary 'Utilize'->'use' must be enforced"
    assert any("cheap" not in t for t in texts)  # no banned word introduced


def test_dry_run_produces_plan_only(tmp_path, akkodis):
    from conftest import build_hardcoded

    src = build_hardcoded(tmp_path / "deck.pptx")
    missing = tmp_path / "should_not_exist.pptx"
    report = MorphPipeline(akkodis, options=MorphOptions(dry_run=True)).run(
        src, missing
    )
    assert not missing.exists()
    assert report.total_changes > 0
    assert report.idempotence_hash


def test_light_deck_maps_with_light_brand(tmp_path, corporate_light):
    """Same deck, light brand: white fills stay white (background role)."""
    from conftest import build_hardcoded

    src = build_hardcoded(tmp_path / "deck.pptx")
    out = tmp_path / "out_light.pptx"
    report = MorphPipeline(corporate_light, options=MorphOptions()).run(src, out)

    bg_entries = [e for e in report.entries if e.role == "background"]
    assert bg_entries, "dark bg rect must remap to light brand background"
    assert all(e.after == "FFFFFF" for e in bg_entries)
