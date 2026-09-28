"""API contract: legacy endpoints unchanged, v2 endpoints added (design §2.2)."""

import base64
import io

import pytest
from fastapi.testclient import TestClient
from pptx import Presentation

import main


@pytest.fixture(scope="module")
def client():
    return TestClient(main.app)


def _upload(path):
    return {"file": (path.name, path.read_bytes(),
                     "application/vnd.openxmlformats-officedocument.presentationml.presentation")}


def test_version(client):
    r = client.get("/api/version")
    assert r.status_code == 200
    assert r.json()["mode"] == "v2-inplace"


def test_legacy_parse_deck_still_works(client, tmp_path):
    from conftest import build_hardcoded

    deck = build_hardcoded(tmp_path / "deck.pptx")
    r = client.post("/api/parse_deck", files=_upload(deck))
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "success"
    assert body["slide_count"] >= 1


def test_legacy_export_deck_still_works(client, tmp_path):
    """The Tauri UI's AST->rebuild contract must keep functioning."""
    from conftest import build_hardcoded

    deck = build_hardcoded(tmp_path / "deck.pptx")
    r = client.post(
        "/api/export_deck",
        json={"slides": [], "tokens": {"bgColor": "#030C1E", "titleFont": "Arial"}},
    )
    assert r.status_code == 200
    assert r.headers["content-type"].startswith(
        "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    )


def test_deck_inventory(client, tmp_path):
    from conftest import build_mixed

    deck = build_mixed(tmp_path / "mixed.pptx")
    r = client.post("/api/deck/inventory", files=_upload(deck))
    assert r.status_code == 200
    inv = r.json()["inventory"]
    assert inv["slide_count"] == 1
    assert inv["slides"][0]["charts"] == 1
    assert inv["slides"][0]["tables"] == 1


def test_brand_apply_returns_deck_and_report(client, tmp_path):
    from conftest import build_hardcoded

    deck = build_hardcoded(tmp_path / "deck.pptx")
    r = client.post(
        "/api/brand/apply",
        files=_upload(deck),
        data={"brand": "akkodis", "dry_run": "false"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "success"
    assert body["report"]["total_changes"] > 0
    prs = Presentation(io.BytesIO(base64.b64decode(body["deck_base64"])))
    assert len(prs.slides.__iter__.__self__._sldIdLst) >= 1  # deck opens + has slides


def test_brand_apply_dry_run(client, tmp_path):
    from conftest import build_hardcoded

    deck = build_hardcoded(tmp_path / "deck.pptx")
    r = client.post(
        "/api/brand/apply",
        files=_upload(deck),
        data={"brand": "akkodis", "dry_run": "true"},
    )
    assert r.status_code == 200
    body = r.json()
    assert "deck_base64" not in body
    assert body["report"]["total_changes"] > 0


def test_brand_apply_unknown_brand(client, tmp_path):
    from conftest import build_hardcoded

    deck = build_hardcoded(tmp_path / "deck.pptx")
    r = client.post(
        "/api/brand/apply",
        files=_upload(deck),
        data={"brand": "no-such-brand"},
    )
    assert r.status_code == 400


def test_brand_extract_needs_llm(client, tmp_path):
    from conftest import build_hardcoded

    deck = build_hardcoded(tmp_path / "deck.pptx")
    r = client.post("/api/brand/extract", files=_upload(deck))
    assert r.status_code == 501  # explicit, documented degradation without LLM_API_KEY
