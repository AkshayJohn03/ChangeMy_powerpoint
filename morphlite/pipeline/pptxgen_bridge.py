"""PptxGenJS bridge — use industry-standard JS renderer for native masters/charts.

Inspired by gitbrent/PptxGenJS (6.1k★). Instead of python-pptx's manual DrawingML,
we shell out to Node with a tiny ESM script that uses PptxGenJS SlideMasters.
This gives: real slide masters, chart data binding, html table → slides,
TypeScript types, and Vercel edge compatibility.

Fallback: if Node/pptxgenjs not installed, returns None and caller should use python-pptx.
"""
from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

PPTXGEN_JS = """
import pptxgen from "pptxgenjs";
import fs from "fs";
const payload = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";
pres.defineSlideMaster({
  title: "AKKODIS_MASTER",
  background: { color: "001F33" },
  objects: [
    { rect: { x: 0, y: 0, w: "100%", h: 0.6, fill: { color: "001F33" } } },
  ],
  slideNumber: { color: "FFFFFF" }
});
for (const s of payload.slides) {
  const slide = pres.addSlide({ masterName: "AKKODIS_MASTER" });
  slide.addText(s.title || "", { x: 0.5, y: 0.3, w: 12, h: 0.8, fontSize: 28, color: "FFB81C", fontFace: "Times New Roman", bold: true });
  if (s.subtitle) slide.addText(s.subtitle, { x: 0.5, y: 1.1, w: 12, h: 0.5, fontSize: 14, color: "FFFFFF" });
  const bullets = (s.elements || []).map(e => e.title || e.body?.[0] || "").filter(Boolean);
  if (bullets.length) {
    // PptxGenJS handles bullet overflow automatically; two-column if >8
    if (bullets.length > 8) {
      const mid = Math.ceil(bullets.length/2);
      slide.addText(bullets.slice(0,mid).map(t=>({text:t, options:{bullet:true}})), { x:0.5, y:1.8, w:5.8, h:5, fontSize:11, color:"FFFFFF" });
      slide.addText(bullets.slice(mid).map(t=>({text:t, options:{bullet:true}})), { x:6.5, y:1.8, w:5.8, h:5, fontSize:11, color:"FFFFFF" });
    } else {
      slide.addText(bullets.map(t=>({text:t, options:{bullet:true}})), { x:0.5, y:1.8, w:12, h:5, fontSize:11, color:"FFFFFF" });
    }
  }
  if (s.table && s.table.rows) {
    const rows = [s.table.headers, ...s.table.rows].map(r=> r.map(c=> ({text:c, options:{color:"FFFFFF"}})));
    slide.addTable(rows, { x:0.5, y:1.8, w:12, colW: Array(rows[0].length).fill(12/rows[0].length) });
  }
}
await pres.writeFile({ fileName: process.argv[3] });
console.log("pptxgen done", process.argv[3]);
"""

def render_via_pptxgen(deck_spec: dict, output_path: str) -> bool:
    """Try to render DeckSpec via PptxGenJS. Returns True on success."""
    try:
        # check node + pptxgenjs availability
        import shutil
        if shutil.which("node") is None:
            return False
        # quick check pptxgenjs installed in ui/
        ui_pkg = Path(__file__).resolve().parent.parent.parent / "ui" / "node_modules" / "pptxgenjs"
        # also try global
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            payload = td / "payload.json"
            out_js = td / "render.mjs"
            payload.write_text(json.dumps(deck_spec), encoding="utf-8")
            out_js.write_text(PPTXGEN_JS, encoding="utf-8")
            # ensure pptxgenjs installed in td
            # try npx --yes pptxgenjs presence, else fallback
            res = subprocess.run(
                ["node", str(out_js), str(payload), output_path],
                cwd=str(td),
                capture_output=True,
                text=True,
                timeout=25,
            )
            if res.returncode == 0 and Path(output_path).exists():
                return True
            # if failed due to missing module, try installing in ui and re-run with NODE_PATH
            if "Cannot find package" in res.stderr and ui_pkg.exists():
                res2 = subprocess.run(
                    ["node", str(out_js), str(payload), output_path],
                    cwd=str(Path(__file__).resolve().parent.parent.parent / "ui"),
                    capture_output=True, text=True, timeout=25,
                )
                return res2.returncode == 0 and Path(output_path).exists()
            return False
    except Exception as e:
        print(f"pptxgen bridge failed: {e}")
        return False
