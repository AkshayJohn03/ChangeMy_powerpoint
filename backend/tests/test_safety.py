"""Safety layer: hostile decks must be rejected before any parsing (SECURITY.md)."""

import io
import zipfile

import pytest
from lxml import etree

from brandmorph.engine.pipeline import MorphOptions, MorphPipeline
from brandmorph.engine.safety import (
    UnsafeDeckError,
    safe_fromstring,
    validate_deck,
)


def _make_zip(path, entries: dict[str, bytes], compress_type=zipfile.ZIP_DEFLATED):
    with zipfile.ZipFile(path, "w") as z:
        for name, data in entries.items():
            z.writestr(zipfile.ZipInfo(name), data, compress_type=compress_type)


def _real_pptx_bytes(tmp_path):
    from conftest import build_hardcoded

    deck = build_hardcoded(tmp_path / "src.pptx")
    return deck.read_bytes()


def test_not_a_zip_rejected(tmp_path):
    p = tmp_path / "fake.pptx"
    p.write_bytes(b"this is not a zip file at all" * 10)
    with pytest.raises(UnsafeDeckError):
        validate_deck(p)


def test_missing_content_types_rejected(tmp_path):
    p = tmp_path / "noct.pptx"
    _make_zip(p, {"ppt/slides/slide1.xml": b"<xml/>"})
    with pytest.raises(UnsafeDeckError):
        validate_deck(p)


def test_zip_slip_entry_rejected(tmp_path):
    p = tmp_path / "slip.pptx"
    _make_zip(p, {
        "[Content_Types].xml": b"<Types/>",
        "../../evil.xml": b"<x/>",
    })
    with pytest.raises(UnsafeDeckError):
        validate_deck(p)


def test_zip_bomb_ratio_rejected(tmp_path):
    """40 KB of compressible zeros declaring ~200 MB uncompressed."""
    p = tmp_path / "bomb.pptx"
    blob = b"\x00" * (200 * 1024 * 1024)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", b"<Types/>")
        z.writestr("ppt/huge.xml", blob)
    p.write_bytes(buf.getvalue())
    with pytest.raises(UnsafeDeckError):
        validate_deck(p, max_total=50 * 1024 * 1024, max_ratio=200)


def test_healthy_deck_passes(tmp_path):
    from conftest import build_hardcoded

    deck = build_hardcoded(tmp_path / "deck.pptx")
    validate_deck(deck)  # must not raise


def test_xml_entity_bomb_defused():
    """Billion-laughs: SAFE_PARSER must refuse entity expansion."""
    xml = (
        b'<?xml version="1.0"?><!DOCTYPE lolz [<!ENTITY lol "lol"><!ENTITY lol2 '
        b'"&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;"/>]><lolz>&lol2;</lolz>'
    )
    try:
        root = safe_fromstring(xml)
        assert root.tag == "lolz"
        assert len(root.text or "") < 20, "entity expansion must not be performed"
    except etree.XMLSyntaxError:
        pass  # refusing to resolve undefined entities is equally safe


def test_pipeline_rejects_hostile_deck(tmp_path):
    from conftest import build_hardcoded

    bomb = tmp_path / "bomb.pptx"
    _make_zip(bomb, {"[Content_Types].xml": b"<Types/>", "../../x": b"x"})
    good = build_hardcoded(tmp_path / "good.pptx")
    pipeline = MorphPipeline(_brand(), options=MorphOptions())
    with pytest.raises(UnsafeDeckError):
        pipeline.run(bomb, tmp_path / "out.pptx")
    # and a healthy deck still works end-to-end through the same pipeline
    report = pipeline.run(good, tmp_path / "out.pptx")
    assert report.total_changes > 0


def _brand():
    from brandmorph.brand.profile import BrandDNA

    return BrandDNA.load("akkodis")


def test_api_upload_cap(tmp_path, monkeypatch):
    """_save_upload must enforce the size cap (DoS defense in depth)."""
    import main

    class FakeUpload:
        def __init__(self, size):
            self.file = io.BytesIO(b"x" * size)

    monkeypatch.setattr(main, "DEFAULT_CAP", None, raising=False)
    from brandmorph.engine import safety

    with pytest.raises(UnsafeDeckError):
        safety.save_upload_bounded(
            FakeUpload(3 * 1024 * 1024), str(tmp_path / "big.bin"), max_bytes=1024
        )
