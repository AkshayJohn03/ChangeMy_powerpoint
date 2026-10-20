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
from brandmorph.engine.safety import (
    UnsafeDeckError,
    save_upload_bounded,
    validate_deck,
)
from brandmorph.llm import env_client as llm_from_env
from builder import BrandTokens, NativePPTXBuilder
from decompiler import SlideDecompiler

app = FastAPI(title="BrandMorph", version=brandmorph_version)

# CORS: env-configurable allowlist (v1 shipped wildcard+credentials, defect D5)
_CORS_ORIGINS = [
    o.strip() for o in os.environ.get(
        "BRANDMORPH_CORS_ORIGINS",
        "http://localhost:5173,http://localhost:8443,http://127.0.0.1:5173,"
        "http://127.0.0.1:8443,tauri://localhost,https://tauri.localhost,"
        "https://akshayjohn.xyz,https://brandmorph-studio.vercel.app,"
        "https://brandmorph.akshayjohn.xyz",
    ).split(",") if o.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def hex_to_rgb(hex_str: str, fallback: RGBColor = RGBColor(37, 99, 235)) -> RGBColor:
    """Parse hex color string to RGBColor with safe normalization.

    Handles: #RRGGBB, RRGGBB, #RGB (shorthand), #RRGGBBAA (strips alpha).
    Returns fallback on any invalid input.
    """
    if not hex_str or not isinstance(hex_str, str):
        return fallback
    clean = hex_str.strip().lstrip("#")
    if len(clean) == 3:
        clean = "".join(c * 2 for c in clean)
    if len(clean) >= 6:
        try:
            r, g, b = (int(clean[i:i + 2], 16) for i in (0, 2, 4))
            return RGBColor(r, g, b)
        except ValueError:
            return fallback
    return fallback

def _save_upload(upload: UploadFile, suffix: str) -> str:
    """Stream upload to disk under a hard size cap (SECURITY.md: DoS defense)."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        save_upload_bounded(upload, tmp.name)
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

@app.get("/api/health")
async def health():
    return {"status": "ok", "engine": "brandmorph", "version": brandmorph_version}

@app.get("/api/demo_ast")
@app.get("/api/parse_test_ppt")
async def demo_ast():
    """Parse the bundled sample deck; no user data needed."""
    samples_dir = os.path.join(os.path.dirname(__file__), "samples")
    examples_dir = os.path.join(os.path.dirname(__file__), "examples")
    test_path = os.environ.get(
        "BRANDMORPH_TEST_DECK",
        os.path.join(samples_dir, "sample_legacy_pitch.pptx"),
    )
    if not os.path.exists(test_path):
        test_path = os.path.join(examples_dir, "demo_raw.pptx")
    if not os.path.exists(test_path):
        return {"status": "error", "message": "Sample deck not found. Place sample_legacy_pitch.pptx in backend/samples/ or demo_raw.pptx in backend/examples/."}
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


@app.get("/api/sample_pptx")
async def get_sample_pptx():
    """Download bundled unformatted sample presentation for one-click testing."""
    samples_dir = os.path.join(os.path.dirname(__file__), "samples")
    examples_dir = os.path.join(os.path.dirname(__file__), "examples")
    sample_path = os.path.join(samples_dir, "sample_legacy_pitch.pptx")
    if not os.path.exists(sample_path):
        sample_path = os.path.join(examples_dir, "demo_raw.pptx")
    if not os.path.exists(sample_path):
        raise HTTPException(status_code=404, detail="Sample presentation not found")
    return FileResponse(
        sample_path,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        filename="sample_legacy_pitch.pptx",
    )


@app.get("/api/brands")
async def get_brands():
    """List available W3C DTCG brand presets with their palettes and typography."""
    brands_dir = os.path.join(os.path.dirname(__file__), "brands")
    presets = []
    if os.path.exists(brands_dir):
        for f in sorted(os.listdir(brands_dir)):
            if f.endswith((".yaml", ".yml")):
                bid = f.rsplit(".", 1)[0]
                try:
                    dna = BrandDNA.load(bid)
                    pal = {}
                    for role in ["background", "surface", "surface_alt", "text_primary", "text_muted", "accent_primary", "accent_secondary"]:
                        c = getattr(dna.palette, role, None)
                        if c is not None and hasattr(c, "hex"):
                            pal[role] = c.hex
                    presets.append({
                        "id": bid,
                        "name": dna.name,
                        "palette": pal,
                        "typography": {
                            "heading": dna.typography.heading.family if dna.typography and dna.typography.heading else "Arial",
                            "body": dna.typography.body.family if dna.typography and dna.typography.body else "Segoe UI",
                        }
                    })
                except Exception:
                    pass
    return {"status": "success", "brands": presets}


@app.post("/api/morph")
@app.post("/api/morph_file")
@app.post("/api/brand/apply")
async def api_brand_apply(
    file: UploadFile = File(...),
    brand: str = Form("enterprise_navy"),
    dry_run: bool = Form(False),
    rewrite_copy: bool = Form(False),
):
    """Re-brand a deck in place. Returns report JSON, slide AST for canvas, and base64 deck.

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

        slides_ast = []
        original_ast = []
        try:
            morphed_dec = SlideDecompiler(out_tmp.name if not dry_run else src)
            slides_ast = morphed_dec.parse_deck()
        except Exception:
            pass

        try:
            orig_dec = SlideDecompiler(src)
            original_ast = orig_dec.parse_deck()
        except Exception:
            pass

        if dry_run:
            return {
                "status": "success",
                "report": report.to_json(),
                "slides": slides_ast or original_ast,
                "original_slides": original_ast,
                "slide_count": len(slides_ast or original_ast),
            }
        with open(out_tmp.name, "rb") as f:
            deck_b64 = base64.b64encode(f.read()).decode("ascii")
        return {
            "status": "success",
            "report": report.to_json(),
            "deck_base64": deck_b64,
            "filename": f"BrandMorph_{brand.replace('/', '_')}.pptx",
            "slides": slides_ast,
            "original_slides": original_ast,
            "slide_count": len(slides_ast),
        }
    except HTTPException:
        raise
    except UnsafeDeckError as e:
        raise HTTPException(status_code=422, detail=f"unsafe deck rejected: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        for p in (src, out_tmp.name):
            if os.path.exists(p):
                os.remove(p)


@app.post("/api/brand/apply_batch")
async def api_brand_apply_batch(
    files: list[UploadFile] = File(...),
    brand: str = Form("enterprise_navy"),
    dry_run: bool = Form(False),
):
    """Batch re-branding: each deck is isolated — one hostile/corrupt deck is
    rejected (HTTP 422 semantics per item) without failing the batch."""
    try:
        dna = BrandDNA.load(brand)
    except FileNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e))
    results = []
    for upload in files:
        src = None
        out_tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pptx")
        out_tmp.close()
        try:
            src = _save_upload(upload, ".pptx")
            validate_deck(src)  # reject before paying for analysis
            report = MorphPipeline(dna, None, MorphOptions(dry_run=dry_run)).run(
                src, out_tmp.name
            )
            with open(out_tmp.name, "rb") as f:
                deck_b64 = base64.b64encode(f.read()).decode("ascii")
            results.append({
                "file": upload.filename,
                "status": "ok",
                "total_changes": report.total_changes,
                "review_flags": report.review_flags,
                "deck_base64": None if dry_run else deck_b64,
            })
        except UnsafeDeckError as e:
            results.append({"file": upload.filename, "status": "rejected", "detail": str(e)})
        except Exception as e:
            results.append({"file": upload.filename, "status": "failed", "detail": str(e)[:200]})
        finally:
            for p in (src, out_tmp.name):
                if p and os.path.exists(p):
                    os.remove(p)
    ok = sum(1 for r in results if r["status"] == "ok")
    return {"status": "success", "succeeded": ok, "total": len(results), "results": results}


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
