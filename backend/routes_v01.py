"""BrandMorph v0.1 API routes — mountable FastAPI router."""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
import uuid
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT))

from morphlite.pipeline.engine import BrandMorphPipeline  # noqa: E402

router = APIRouter(prefix="/api/v01", tags=["v01"])

_sessions: dict[str, dict] = {}


@router.post("/process")
async def process_deck(file: UploadFile = File(...)):
    suffix = Path(file.filename or "deck.pptx").suffix or ".pptx"
    tmp_in = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    shutil.copyfileobj(file.file, tmp_in)
    tmp_in.close()

    out_dir = tempfile.mkdtemp(prefix="brandmorph_")
    tmp_out = str(Path(out_dir) / f"transformed{suffix}")

    try:
        pipeline = BrandMorphPipeline()
        result = pipeline.process(tmp_in.name, tmp_out)
    except Exception as exc:
        import traceback
        raise HTTPException(status_code=500, detail=f"{exc}\n{traceback.format_exc(limit=3)}")
    finally:
        import os
        if os.path.exists(tmp_in.name):
            os.remove(tmp_in.name)

    deck_id = result.deck_id
    _sessions[deck_id] = {
        "analysis": result.to_json(),
        "output_path": tmp_out,
        "work_dir": out_dir,
        "input_name": file.filename,
    }

    return {
        "status": "success",
        "deck_id": deck_id,
        "n_slides": len(result.slides),
        "totals": result.plan.get("totals", {}),
        "slides_preview": [
            {"slide": s["slide_number"], **s["summary"]}
            for s in result.slides[:5]
        ],
    }


@router.get("/results/{deck_id}")
async def get_results(deck_id: str):
    if deck_id not in _sessions:
        raise HTTPException(status_code=404, detail="deck_id not found")
    return {"status": "success", "results": _sessions[deck_id]["analysis"]}


@router.get("/plan/{deck_id}")
async def get_plan(deck_id: str):
    if deck_id not in _sessions:
        raise HTTPException(status_code=404, detail="deck_id not found")
    return _sessions[deck_id]["analysis"]["transformation_plan"]


@router.get("/export/{deck_id}")
async def export_deck(deck_id: str):
    if deck_id not in _sessions:
        raise HTTPException(status_code=404, detail="deck_id not found")
    entry = _sessions[deck_id]
    output = entry["output_path"]
    if not Path(output).exists():
        raise HTTPException(status_code=410, detail="output file expired")
    original = entry.get("input_name") or "deck.pptx"
    download_name = f"BrandMorph_{original}"
    return FileResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        filename=download_name,
    )
