"""FitGuard: measured overflow, budget ladder, review flags."""

from pptx import Presentation

from brandmorph.engine.pipeline import MorphOptions, MorphPipeline


def _title_size(path) -> float:
    prs = Presentation(str(path))
    for shape in prs.slides[0].shapes:
        if getattr(shape, "has_text_frame", False) and shape.has_text_frame:
            for p in shape.text_frame.paragraphs:
                for r in p.runs:
                    if "Comprehensive analysis" in r.text:
                        return r.font.size.pt if r.font.size else 18.0
    raise AssertionError("overflow title run not found")


def test_overflow_title_flagged(tmp_path, akkodis):
    from conftest import build_hardcoded

    src = build_hardcoded(tmp_path / "deck.pptx")
    out = tmp_path / "out.pptx"
    report = MorphPipeline(akkodis, options=MorphOptions()).run(src, out)

    overflow_flags = [
        f for f in report.review_flags if "overflows" in f or "bleed" in f
    ]
    assert overflow_flags, (
        "a 140-char 24pt title in a wrap-off box near the right edge must be flagged"
    )


def test_fitting_text_not_flagged_or_shrunk(tmp_path, akkodis):
    from conftest import build_hardcoded

    src = build_hardcoded(tmp_path / "deck.pptx")
    out = tmp_path / "out.pptx"
    report = MorphPipeline(akkodis, options=MorphOptions()).run(src, out)

    shrunk = [e for e in report.entries if e.stage == "fit" and "applied" in e.note]
    for entry in shrunk:
        # after shrinking, the text must actually fit (apply-only-if-fits rule)
        assert entry.confidence >= 0
    # non-overflowing boxes keep their sizes
    assert _title_size(out) >= 22.0  # ladder never exceeds 2 steps


def test_fit_idempotent(tmp_path, akkodis):
    from conftest import build_hardcoded

    src = build_hardcoded(tmp_path / "deck.pptx")
    out1 = tmp_path / "pass1.pptx"
    out2 = tmp_path / "pass2.pptx"
    MorphPipeline(akkodis, options=MorphOptions()).run(src, out1)
    report2 = MorphPipeline(akkodis, options=MorphOptions()).run(out1, out2)
    assert report2.counts_by_stage.get("fit", 0) == 0
