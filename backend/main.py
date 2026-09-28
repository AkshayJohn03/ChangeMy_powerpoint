import base64
import os
import shutil
import tempfile
from typing import Any

import uvicorn
from fastapi import Body, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pptx.dml.color import RGBColor

from brandmorph import __version__ as brandmorph_version
from brandmorph.brand.profile import BrandDNA
from brandmorph.engine.analyzer import analyze as deck_inventory
from brandmorph.engine.pipeline import MorphOptions, MorphPipeline
from brandmorph.llm import env_client as llm_from_env
from builder import BrandTokens, NativePPTXBuilder
from decompiler import SlideDecompiler

app = FastAPI(title="BrandMorph", version=brandmorph_version)

# CORS: env-configurable allowlist (v1 shipped wildcard+credentials, defect D5)
_CORS_ORIGINS = [
    o.strip() for o in os.environ.get(
        "BRANDMORPH_CORS_ORIGINS",
        "http://localhost:5173,http://localhost:8443,http://127.0.0.1:5173,"
        "http://127.0.0.1:8443,tauri://localhost,https://tauri.localhost",
    ).split(",") if o.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def hex_to_rgb(hex_str: str) -> RGBColor:
    hex_str = hex_str.lstrip("#")
    if len(hex_str) == 6:
        r, g, b = tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))
        return RGBColor(r, g, b)
    return RGBColor(37, 99, 235)

def _save_upload(upload: UploadFile, suffix: str) -> str:
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        shutil.copyfileobj(upload.file, tmp)
        return tmp.name

@app.post("/api/parse_deck")
async def parse_deck(file: UploadFile = File(...)):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pptx") as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    try:
        decompiler = SlideDecompiler(tmp_path)
        ast = decompiler.parse_deck()
        return {"status": "success", "slides": ast, "slide_count": len(ast)}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

@app.get("/api/parse_test_ppt")
async def parse_test_ppt():
    # v1 hardcoded a personal OneDrive path here (defect D5); now env-configurable
    test_path = os.environ.get("BRANDMORPH_TEST_DECK", "")
    if not test_path:
        return {"status": "error", "message": "Set BRANDMORPH_TEST_DECK to a .pptx path to use this helper."}
    if not os.path.exists(test_path):
        return {"status": "error", "message": f"Test file not found at {test_path}"}
    try:
        decompiler = SlideDecompiler(test_path)
        ast = decompiler.parse_deck()
        return {"status": "success", "slides": ast, "slide_count": len(ast)}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/api/export_deck")
async def export_deck(payload: dict[str, Any] = Body(...)):
    try:
        slides_ast = payload.get("slides", [])
        tokens = payload.get("tokens", {})
        
        # Configure custom brand tokens if provided
        if "bgColor" in tokens:
            BrandTokens.BG_COLOR = hex_to_rgb(tokens["bgColor"])
        if "cardBg" in tokens:
            BrandTokens.CARD_BG = hex_to_rgb(tokens["cardBg"])
        if "titleFont" in tokens:
            BrandTokens.FONT_TITLE = tokens["titleFont"]
        if "bodyFont" in tokens:
            BrandTokens.FONT_BODY = tokens["bodyFont"]

        builder = NativePPTXBuilder()
        for slide_ast in slides_ast:
            builder.build_slide(slide_ast)

        out_tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pptx")
        out_tmp.close()
        builder.save(out_tmp.name)

        return FileResponse(
            out_tmp.name,
            media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            filename="Reskinned_BrandMorph_Deck.pptx"
        )
    except Exception as e:
        return {"status": "error", "message": str(e)}

# ---------------------------------------------------------------------------
# BrandMorph v2 — in-place brand morphing engine (see docs/V2_DESIGN.md).
# Legacy endpoints above keep their exact contract for the Tauri UI.
# ---------------------------------------------------------------------------

@app.get("/api/version")
async def version():
    return {"engine": "brandmorph", "version": brandmorph_version, "mode": "v2-inplace"}


@app.post("/api/deck/inventory")
async def api_deck_inventory(file: UploadFile = File(...)):
    """What would change? Analyzer-only preview (no transformation)."""
    tmp_path = _save_upload(file, ".pptx")
    try:
        return {"status": "success", "inventory": deck_inventory(tmp_path)}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


@app.post("/api/brand/apply")
async def api_brand_apply(
    file: UploadFile = File(...),
    brand: str = Form("akkodis"),
    dry_run: bool = Form(False),
    rewrite_copy: bool = Form(False),
):
    """Re-brand a deck in place. Returns report JSON + base64 deck.

    `dry_run=true` returns the morph plan without producing a deck.
    `rewrite_copy=true` enables LLM tone rewriting (needs LLM_API_KEY).
    """
    try:
        dna = BrandDNA.load(brand)
    except FileNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e))
    src = _save_upload(file, ".pptx")
    out_tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pptx")
    out_tmp.close()
    try:
        llm = llm_from_env() if rewrite_copy else None
        report = MorphPipeline(
            dna, llm,
            MorphOptions(dry_run=dry_run, rewrite_copy=True if rewrite_copy else None),
        ).run(src, out_tmp.name)
        if dry_run:
            return {"status": "success", "report": report.to_json()}
        with open(out_tmp.name, "rb") as f:
            deck_b64 = base64.b64encode(f.read()).decode("ascii")
        return {
            "status": "success",
            "report": report.to_json(),
            "deck_base64": deck_b64,
            "filename": f"BrandMorph_{brand.replace('/', '_')}.pptx",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        for p in (src, out_tmp.name):
            if os.path.exists(p):
                os.remove(p)


@app.post("/api/brand/extract")
async def api_brand_extract(file: UploadFile = File(...)):
    """Draft a BrandDNA profile from a brand-guideline PDF (LLM-assisted)."""
    llm = llm_from_env()
    if llm is None:
        raise HTTPException(
            status_code=501,
            detail="LLM-assisted PDF extraction requires LLM_API_KEY. "
                   "Until then, author a YAML profile by hand (brands/*.yaml).",
        )
    from brandmorph.brand.profile import extract_draft_async

    pdf_bytes = await file.read()
    draft = await extract_draft_async(pdf_bytes, llm)
    if draft is None:
        raise HTTPException(status_code=422, detail="Could not parse a brand profile from this PDF.")
    import yaml as _yaml

    return {
        "status": "success",
        "brand_name": draft.name,
        "brand_yaml": _yaml.safe_dump(draft.model_dump(), sort_keys=False, allow_unicode=True),
    }


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
