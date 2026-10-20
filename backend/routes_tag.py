"""Tag-based pipeline — docxtemplater-style, most brand-faithful.

Uses morphlite/pipeline/template_tag.py which deep-copies template slides
and replaces {title}/{bullets} tags. 100% native shapes/backgrounds preserved.
"""
from __future__ import annotations
import shutil, tempfile, sys
from pathlib import Path
from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import FileResponse

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from morphlite.pipeline.template_tag import TemplateTagPipeline

LITE_TEMPLATE = REPO_ROOT / "data" / "brand_template" / "Akkodis_Sanitized_Master_Lite.pptx"
TAGGED_TEMPLATE = REPO_ROOT / "data" / "brand_template" / "Brand_guideline_Akkodis_tagged.pptx"
TEMPLATE = REPO_ROOT / "data" / "brand_template" / "Brand_guideline_Akkodis.pptx"
FALLBACK = Path(r"C:\Users\Akshay.JOHN-XAVIER\OneDrive - Akkodis\Documents\Me\Brand_guideline_Akkodis.pptx")

def _tpl():
    if LITE_TEMPLATE.exists(): return str(LITE_TEMPLATE)
    if TAGGED_TEMPLATE.exists(): return str(TAGGED_TEMPLATE)
    if TEMPLATE.exists(): return str(TEMPLATE)
    if FALLBACK.exists(): return str(FALLBACK)
    raise HTTPException(500, detail="Brand template not found")

router = APIRouter(prefix="/api/tag", tags=["tag"])

@router.get("/health")
async def health():
    p = _tpl()
    pipe = TemplateTagPipeline(p)
    return {"status":"healthy","pipeline":"tag_v1","template": p, "template_slides": len(pipe.tpl.slides), "tags_per_slide": pipe.slide_tags}

@router.get("/process_test_ppt")
async def process_test_ppt():
    test_path = Path(r"C:\Users\Akshay.JOHN-XAVIER\OneDrive - Akkodis\Documents\Me\TestPPT.pptx")
    if not test_path.exists():
        test_path = REPO_ROOT / "TestPPT.pptx"
    if not test_path.exists():
        raise HTTPException(404, detail="TestPPT.pptx not found")
    tpl = _tpl()
    tmp_out = tempfile.NamedTemporaryFile(delete=False, suffix=".pptx")
    tmp_out.close()
    pipe = TemplateTagPipeline(tpl)
    pipe.process(str(test_path), tmp_out.name)
    return FileResponse(tmp_out.name, media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation", filename="BrandMorph_Tag_TestPPT.pptx")

@router.post("/process")
async def process(file: UploadFile = File(...)):
    tpl = _tpl()
    suffix = Path(file.filename or "deck.pptx").suffix or ".pptx"
    tmp_in = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    shutil.copyfileobj(file.file, tmp_in)
    tmp_in.close()
    tmp_out = tempfile.NamedTemporaryFile(delete=False, suffix=".pptx")
    tmp_out.close()
    try:
        pipe = TemplateTagPipeline(tpl)
        res = pipe.process(tmp_in.name, tmp_out.name)
    except Exception as e:
        import traceback
        raise HTTPException(500, detail=f"{e}\n{traceback.format_exc(limit=6)}")
    finally:
        Path(tmp_in.name).unlink(missing_ok=True)
    return FileResponse(tmp_out.name, media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation", filename=f"Tag_{file.filename}")

@router.post("/spec")
async def spec(file: UploadFile = File(...)):
    from morphlite.models.content_model import extract_deck
    suffix = Path(file.filename or "deck.pptx").suffix or ".pptx"
    tmp_in = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    shutil.copyfileobj(file.file, tmp_in)
    tmp_in.close()
    try:
        deck = extract_deck(tmp_in.name)
        return {"n_slides": deck.n_slides, "prompt": deck.to_prompt()[:3500], "sample_payload": TemplateTagPipeline(_tpl())._deck_to_payloads(deck)[:2]}
    finally:
        Path(tmp_in.name).unlink(missing_ok=True)
