"""BrandMorph v0.3 API routes — template-driven pipeline."""
from __future__ import annotations

import os
import shutil
import sys
import tempfile
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, HTMLResponse

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT))

from morphlite.pipeline.template_driven import TemplateDrivenPipeline  # noqa: E402

router = APIRouter(prefix="/api/v01", tags=["v01"])

_sessions: dict[str, dict] = {}

_UI_HTML = Path(__file__).resolve().parent / "v01_ui.html"

# Brand template path — configurable via env or default
BRAND_TEMPLATE_PATH = os.environ.get(
    "BRANDMORPH_TEMPLATE",
    str(Path(os.path.expanduser("~")) / "OneDrive - Akkodis" / "Documents" / "Me" / "Brand_guideline_Akkodis.pptx"),
)


def _get_template_path() -> str:
    if os.path.exists(BRAND_TEMPLATE_PATH):
        return BRAND_TEMPLATE_PATH
    # fallback: look in data/brand_template
    local = _REPO_ROOT / "data" / "brand_template" / "Brand_guideline_Akkodis.pptx"
    if local.exists():
        return str(local)
    raise HTTPException(status_code=500, detail=f"Brand template not found at {BRAND_TEMPLATE_PATH}")


@router.get("/", response_class=HTMLResponse)
async def index():
    if _UI_HTML.exists():
        return HTMLResponse(_UI_HTML.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>BrandMorph v0.3</h1><p>UI file missing</p>")


@router.get("/health")
async def health():
    template_exists = os.path.exists(BRAND_TEMPLATE_PATH)
    model_exists = (_REPO_ROOT / "models" / "slide_type_classifier.joblib").exists()
    return {
        "status": "healthy",
        "template_available": template_exists,
        "template_path": BRAND_TEMPLATE_PATH,
        "slide_classifier_loaded": model_exists,
        "pipeline": "template_driven_v0.3",
    }


@router.post("/process")
async def process_deck(file: UploadFile = File(...)):
    template_path = _get_template_path()

    suffix = Path(file.filename or "deck.pptx").suffix or ".pptx"
    tmp_in = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    shutil.copyfileobj(file.file, tmp_in)
    tmp_in.close()

    out_dir = tempfile.mkdtemp(prefix="brandmorph_")
    tmp_out = str(Path(out_dir) / f"branded{suffix}")

    try:
        pipeline = TemplateDrivenPipeline(template_path)
        result = pipeline.process(tmp_in.name, tmp_out)
    except Exception as exc:
        import traceback
        raise HTTPException(status_code=500, detail=f"{exc}\n{traceback.format_exc(limit=5)}")
    finally:
        import os
        if os.path.exists(tmp_in.name):
            os.remove(tmp_in.name)

    deck_id = result["deck_id"]
    slide_types = result.get("slide_type_map", [])

    type_counts = {}
    for st in slide_types:
        t = st["type"]
        type_counts[t] = type_counts.get(t, 0) + 1

    _sessions[deck_id] = {
        "result": result,
        "output_path": tmp_out,
        "work_dir": out_dir,
        "input_name": file.filename,
    }

    return {
        "status": "success",
        "deck_id": deck_id,
        "n_slides": result["n_slides"],
        "binary_changed": result["binary_changed"],
        "slide_types": type_counts,
        "slides": [
            {"slide": st["slide"], "type": st["type"]}
            for st in slide_types
        ],
    }


@router.get("/results/{deck_id}")
async def get_results(deck_id: str):
    if deck_id not in _sessions:
        raise HTTPException(status_code=404, detail="deck_id not found")
    return {"status": "success", "results": _sessions[deck_id]["result"]}


@router.get("/plan/{deck_id}")
async def get_plan(deck_id: str):
    if deck_id not in _sessions:
        raise HTTPException(status_code=404, detail="deck_id not found")
    return {"decisions": _sessions[deck_id]["result"].get("decisions", [])}


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
