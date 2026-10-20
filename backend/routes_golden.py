"""Golden pipeline routes — retrieval + Hungarian + custGeom renderer.

Uses morphlite/pipeline/golden_morph.py: retrieves the best golden layout
per raw slide (anonymized index), recovers reading order with the Hungarian
algorithm, then renders glass cards / split steps / vector icons natively.
"""
from __future__ import annotations
import shutil, tempfile, sys
from pathlib import Path
from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import FileResponse

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from morphlite.pipeline.golden_morph import GoldenMorphPipeline

router = APIRouter(prefix="/api/golden", tags=["golden"])


def _pipe() -> GoldenMorphPipeline:
    try:
        return GoldenMorphPipeline()
    except Exception as e:
        raise HTTPException(500, detail=f"GoldenMorph init failed: {e}")


@router.get("/health")
async def health():
    p = _pipe()
    return {
        "status": "healthy",
        "pipeline": "golden_morph",
        "template": p.template_path,
        "index_entries": len(p.entries),
    }


@router.get("/process_test_ppt")
async def process_test_ppt():
    test_path = Path(r"C:\Users\Akshay.JOHN-XAVIER\OneDrive - Akkodis\Documents\Me\TestPPT.pptx")
    if not test_path.exists():
        test_path = REPO_ROOT / "TestPPT.pptx"
    if not test_path.exists():
        raise HTTPException(404, detail="TestPPT.pptx not found")
    tmp_out = tempfile.NamedTemporaryFile(delete=False, suffix=".pptx")
    tmp_out.close()
    pipe = _pipe()
    pipe.process(str(test_path), tmp_out.name)
    return FileResponse(
        tmp_out.name,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        filename="BrandMorph_Golden_TestPPT.pptx",
    )


@router.post("/process")
async def process(file: UploadFile = File(...)):
    suffix = Path(file.filename or "deck.pptx").suffix or ".pptx"
    tmp_in = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    shutil.copyfileobj(file.file, tmp_in)
    tmp_in.close()
    tmp_out = tempfile.NamedTemporaryFile(delete=False, suffix=".pptx")
    tmp_out.close()
    try:
        pipe = _pipe()
        pipe.process(tmp_in.name, tmp_out.name)
    except Exception as e:
        import traceback
        raise HTTPException(500, detail=f"{e}\n{traceback.format_exc(limit=6)}")
    finally:
        Path(tmp_in.name).unlink(missing_ok=True)
    return FileResponse(
        tmp_out.name,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        filename=f"Golden_{file.filename}",
    )
