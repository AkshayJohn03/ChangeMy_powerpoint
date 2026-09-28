"""Optional visual-QA renderer (design §2.1 ⑨).

Detects LibreOffice (`soffice`) and renders a deck to PDF for before/after
comparison. When soffice is absent the stage is skipped gracefully and the
caller reports that — a missing renderer never fails a morph.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

_SOFFICE_CANDIDATES = [
    "soffice",
    r"C:\Program Files\LibreOffice\program\soffice.exe",
    r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
    "/usr/bin/soffice",
    "/usr/local/bin/soffice",
    "/Applications/LibreOffice.app/Contents/MacOS/soffice",
]


def find_soffice() -> str | None:
    for cand in _SOFFICE_CANDIDATES:
        found = shutil.which(cand)
        if found:
            return found
        if Path(cand).exists():
            return cand
    return None


def render_pdf(pptx_path: str | Path, out_dir: str | Path) -> Path | None:
    """Render deck -> PDF. Returns None when soffice is unavailable."""
    soffice = find_soffice()
    if soffice is None:
        return None
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [soffice, "--headless", "--convert-to", "pdf", "--outdir", str(out), str(pptx_path)],
        check=True, capture_output=True, timeout=180,
    )
    return out / (Path(pptx_path).stem + ".pdf")
