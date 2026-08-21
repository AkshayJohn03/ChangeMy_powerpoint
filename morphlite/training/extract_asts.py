"""Batch AST extraction over the sorted data/source workspace.

    python -m morphlite.training.extract_asts
"""
from __future__ import annotations

import json
import time
import traceback
from pathlib import Path

from .. import config
from ..ast import extractor

AST_ROOT = config.EXTRACTED_DIR / "ast"


def load_dest_index() -> dict[str, dict]:
    index = {}
    manifest = config.METADATA_DIR / "file_manifest.jsonl"
    with open(manifest, encoding="utf-8") as fh:
        for line in fh:
            rec = json.loads(line)
            dest = rec.get("dest")
            if dest:
                index[dest] = rec
    return index


def run() -> None:
    index = load_dest_index()
    files = sorted(p for p in config.SOURCE_DIR.rglob("*") if p.suffix.lower() == ".pptx")
    errors_log = []
    out_manifest = []
    t0 = time.time()

    for i, path in enumerate(files, 1):
        rel = path.relative_to(config.SOURCE_DIR)
        parts = rel.parts
        if parts[0] == "paired" and len(parts) > 1:
            bucket = f"paired_{parts[1]}"
            batch = parts[2] if len(parts) > 2 else "default"
        else:
            bucket = parts[0]
            batch = parts[1] if len(parts) > 1 else "default"
        rec = index.get(str(path), {})
        name_key = rec.get("name_key") or rec.get("key", "")
        md5 = rec.get("md5", "")

        try:
            deck = extractor.extract_deck(path, bucket, batch, name_key, md5)
            out_path = extractor.save_deck(deck, AST_ROOT)
            out_manifest.append(
                {
                    "deck_id": deck["deck_id"],
                    "source": str(path),
                    "bucket": bucket,
                    "batch": batch,
                    "name_key": name_key,
                    "n_slides": deck["n_slides"],
                    "ast_path": str(out_path),
                    "status": "OK",
                }
            )
            print(f"[{i}/{len(files)}] OK  {deck['deck_id']}  slides={deck['n_slides']}", flush=True)
        except Exception as exc:
            errors_log.append({"source": str(path), "error": repr(exc), "trace": traceback.format_exc(limit=3)})
            print(f"[{i}/{len(files)}] FAIL {path.name}: {exc!r}", flush=True)

    with open(AST_ROOT / "extraction_manifest.jsonl", "w", encoding="utf-8") as fh:
        for r in out_manifest:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")

    summary = {
        "decks_total": len(files),
        "decks_ok": len(out_manifest),
        "decks_failed": len(errors_log),
        "elapsed_sec": round(time.time() - t0, 1),
    }
    if errors_log:
        (AST_ROOT / "errors.json").write_text(json.dumps(errors_log, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    run()
