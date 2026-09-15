"""BrandMorph v0.4 — LLM-structured pipeline (intelligent).

Raw PPTX -> ContentModel (visual-order text) -> Spec (typed DeckSpec via LLM or heuristic)
-> Deterministic Akkodis renderer -> branded PPTX.

Runs WITHOUT any API key (MockLLM heuristic fallback). When Azure/OpenAI
env vars are set, uses the real LLM. Deterministic rendering always.
"""
from __future__ import annotations

import hashlib
import os
import shutil
import sys
import tempfile
import uuid
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT))

from morphlite.models.content_model import extract_deck  # noqa: E402
from morphlite.llm.provider import get_provider, CONFIG  # noqa: E402
from morphlite.llm.spec_builder import SpecBuilder  # noqa: E402
from morphlite.render.renderer import BrandRenderer  # noqa: E402

router = APIRouter(prefix="/api/v02", tags=["v02-intelligent"])

_sessions: dict[str, dict] = {}


@router.get("/health")
async def health():
    return {
        "status": "healthy",
        "pipeline": "intelligent_v02",
        "llm_configured": CONFIG.llm_is_configured(),
        "provider": CONFIG.pick_provider(),
        "azure_endpoint_set": bool(CONFIG.endpoint),
        "openai_base_set": bool(CONFIG.openai_base_url),
        "renderer": "deterministic_akkodis",
    }


@router.get("/process_test_ppt")
async def process_test_ppt():
    test_path = Path(r"C:\Users\Akshay.JOHN-XAVIER\OneDrive - Akkodis\Documents\Me\TestPPT.pptx")
    if not test_path.exists():
        test_path = _REPO_ROOT / "TestPPT.pptx"
    if not test_path.exists():
        raise HTTPException(404, detail="TestPPT.pptx not found")
    
    out_dir = tempfile.mkdtemp(prefix="brandmorph_v02_")
    tmp_out = str(Path(out_dir) / "branded.pptx")
    deck_id = str(uuid.uuid4())[:8]

    deck = extract_deck(str(test_path))
    prov = get_provider("")
    builder = SpecBuilder(provider=prov)
    deck_spec = builder.build(deck)
    renderer = BrandRenderer()
    renderer.render(deck_spec, tmp_out)

    _sessions[deck_id] = {
        "deck_id": deck_id,
        "output_path": tmp_out,
        "spec": deck_spec.to_dict(),
        "n_slides": len(deck_spec.slides),
        "source_filename": "TestPPT.pptx",
    }
    return {
        "status": "success",
        "deck_id": deck_id,
        "n_slides": len(deck_spec.slides),
        "n_raw_slides": deck.n_slides,
        "provider": prov.name,
        "pipeline": "intelligent_v02",
        "binary_changed": True,
        "slides": [{"slide": s.slide_number, "title": s.title, "archetype": s.archetype.value} for s in deck_spec.slides],
    }


@router.post("/process")
async def process_deck(file: UploadFile = File(...), provider: str = ""):
    suffix = Path(file.filename or "deck.pptx").suffix or ".pptx"
    tmp_in = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    shutil.copyfileobj(file.file, tmp_in)
    tmp_in.close()

    out_dir = tempfile.mkdtemp(prefix="brandmorph_v02_")
    tmp_out = str(Path(out_dir) / f"branded{suffix}")
    deck_id = str(uuid.uuid4())[:8]

    try:
        deck = extract_deck(tmp_in.name)
        # provider override from query, else auto
        prov_name = provider or CONFIG.pick_provider()
        llm = get_provider(prov_name if prov_name != "mock" else "mock")
        spec = SpecBuilder(llm=llm).build(deck)

        renderer = BrandRenderer()
        renderer.render(spec, tmp_out)

        input_hash = hashlib.sha256(Path(tmp_in.name).read_bytes()).hexdigest()
        output_hash = hashlib.sha256(Path(tmp_out).read_bytes()).hexdigest()

        result = {
            "deck_id": deck_id,
            "n_slides": len(spec.slides),
            "n_raw_slides": deck.n_slides,
            "input_sha256": input_hash,
            "output_sha256": output_hash,
            "binary_changed": input_hash != output_hash,
            "provider": prov_name,
            "slides": [
                {"slide": s.source_slide, "archetype": s.archetype, "title": s.title[:80]}
                for s in spec.slides
            ],
            "pipeline": "intelligent_v02 (ContentModel -> DeckSpec -> deterministic render)",
        }
    except Exception as exc:
        import traceback
        raise HTTPException(status_code=500, detail=f"{exc}\n{traceback.format_exc(limit=12)}")
    finally:
        if os.path.exists(tmp_in.name):
            os.remove(tmp_in.name)

    _sessions[deck_id] = {
        "result": result,
        "output_path": tmp_out,
        "work_dir": out_dir,
        "input_name": file.filename,
    }
    return {"status": "success", **result}


@router.get("/results/{deck_id}")
async def get_results(deck_id: str):
    if deck_id not in _sessions:
        raise HTTPException(status_code=404, detail="deck_id not found")
    return {"status": "success", "results": _sessions[deck_id]["result"]}


@router.get("/export/{deck_id}")
async def export_deck(deck_id: str):
    if deck_id not in _sessions:
        raise HTTPException(status_code=404, detail="deck_id not found")
    entry = _sessions[deck_id]
    output = entry["output_path"]
    if not Path(output).exists():
        raise HTTPException(status_code=410, detail="output expired")
    original = entry.get("input_name") or "deck.pptx"
    return FileResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        filename=f"BrandMorph_v02_{original}",
    )


# Also expose a spec-only endpoint for debugging / showcase
@router.post("/spec")
async def get_spec(file: UploadFile = File(...), provider: str = ""):
    suffix = Path(file.filename or "deck.pptx").suffix or ".pptx"
    tmp_in = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    shutil.copyfileobj(file.file, tmp_in)
    tmp_in.close()
    try:
        deck = extract_deck(tmp_in.name)
        prov_name = provider or CONFIG.pick_provider()
        llm = get_provider(prov_name if prov_name != "mock" else "mock")
        spec = SpecBuilder(llm=llm).build(deck)
        return {
            "status": "success",
            "n_slides": len(spec.slides),
            "provider": prov_name,
            "content_prompt": deck.to_prompt()[:4000],
            "spec": {
                "brand": spec.brand,
                "slides": [
                    {
                        "archetype": s.archetype,
                        "title": s.title,
                        "source_slide": s.source_slide,
                        "elements": [{"title": e.title} for e in s.elements[:3]],
                    }
                    for s in spec.slides
                ],
            },
        }
    finally:
        if os.path.exists(tmp_in.name):
            os.remove(tmp_in.name)
