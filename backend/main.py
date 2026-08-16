from fastapi import FastAPI, UploadFile, File, Response, Body
import uvicorn
import shutil
import os
import tempfile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from decompiler import SlideDecompiler
from builder import NativePPTXBuilder, BrandTokens
from pptx.dml.color import RGBColor
from typing import Dict, Any, List

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
    test_path = r"C:\Users\Akshay.JOHN-XAVIER\OneDrive - Akkodis\Documents\Me\TestPPT.pptx"
    if not os.path.exists(test_path):
        return {"status": "error", "message": f"Test file not found at {test_path}"}
    try:
        decompiler = SlideDecompiler(test_path)
        ast = decompiler.parse_deck()
        return {"status": "success", "slides": ast, "slide_count": len(ast)}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/api/export_deck")
async def export_deck(payload: Dict[str, Any] = Body(...)):
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

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
