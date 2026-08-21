"""Batch chrome extraction over the sorted workspace.

    python -m morphlite.training.extract_chromes
"""
from __future__ import annotations

import json
import time
from pathlib import Path

from .. import config
from ..ast.chrome import extract_chrome

CHROME_ROOT = config.EXTRACTED_DIR / "chrome"


def run() -> None:
    CHROME_ROOT.mkdir(parents=True, exist_ok=True)
    files = sorted(p for p in config.SOURCE_DIR.rglob("*") if p.suffix.lower() == ".pptx")
    t0 = time.time()
    ok = 0
    for i, path in enumerate(files, 1):
        rel = path.relative_to(config.SOURCE_DIR)
        parts = rel.parts
        if parts[0] == "paired" and len(parts) > 1:
            bucket = f"paired_{parts[1]}"
            batch = parts[2] if len(parts) > 2 else "default"
        else:
            bucket = parts[0]
            batch = parts[1] if len(parts) > 1 else "default"
        from ..ast.node_ids import deck_id as make_deck_id
        did = make_deck_id(bucket, batch, path.name)
        try:
            chrome = extract_chrome(str(path))
            out = CHROME_ROOT / f"{did}.json"
            out.write_text(json.dumps(chrome, ensure_ascii=False), encoding="utf-8")
            ok += 1
            if i % 25 == 0:
                print(f"[{i}/{len(files)}] {did}", flush=True)
        except Exception as exc:
            print(f"[{i}/{len(files)}] FAIL {path.name}: {exc!r}", flush=True)
    print(json.dumps({"decks": len(files), "ok": ok, "elapsed_sec": round(time.time() - t0, 1)}, indent=2))


if __name__ == "__main__":
    run()
