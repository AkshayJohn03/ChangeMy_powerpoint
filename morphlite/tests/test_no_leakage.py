"""Compliance gate: ensure no original identity leaks into displayable artifacts.

Scans every file that may be committed or shown (code, docs, whitelisted
aggregate metadata) for occurrences of restricted tokens derived from the
registry. Never prints the tokens themselves.

    python -m morphlite.tests.test_no_leakage
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

BRANDMORPH_ROOT = Path(__file__).resolve().parents[2]
REGISTRY = BRANDMORPH_ROOT / "data" / "metadata" / "deck_registry.json"

SCAN_ROOTS = ["morphlite", "AGENTS.md", ".gitignore", "backend/main.py", "backend/decompiler.py", "backend/builder.py"]
SCAN_EXTS = {".py", ".md", ".json", ".toml", ".cfg", ".txt"}
ALLOWED_DATA_FILES = {
    "EFFECTIVE_COVERAGE.json",
    "FINGERPRINT_STATS.json",
    "ML_BENCHMARKS.json",
    "ML_BENCHMARKS_V2.json",
    "inventory.json",
    "pair_discovery_summary.json",
    "alignment_summary.json",
    "BASELINE_EVAL.json",
}


def _restricted_stems() -> set[str]:
    reg = json.loads(REGISTRY.read_text(encoding="utf-8"))
    stems = set()
    for entry in reg["decks"].values():
        stem = Path(entry["original_filename"]).stem.strip().lower()
        if stem:
            stems.add(" ".join(stem.split()))
    return stems


FORBIDDEN_IN_AGGREGATES = ["onedrive", ".pptx", "original_filename", "users\\"]


def _scan_targets() -> list[Path]:
    targets = []
    for root in SCAN_ROOTS:
        p = BRANDMORPH_ROOT / root
        if p.is_file():
            targets.append(p)
        elif p.is_dir():
            targets.extend(q for q in p.rglob("*") if q.suffix.lower() in SCAN_EXTS and "__pycache__" not in str(q))
    meta = BRANDMORPH_ROOT / "data" / "metadata"
    if meta.is_dir():
        for q in meta.glob("*"):
            if q.name in ALLOWED_DATA_FILES:
                targets.append(q)
    return sorted(set(targets))


def main() -> int:
    if not REGISTRY.exists():
        print("registry missing; nothing to enforce yet -> PASS (vacuous)")
        return 0
    stems = _restricted_stems()
    offenders = []
    files_scanned = 0
    meta_dir = BRANDMORPH_ROOT / "data" / "metadata"
    for path in _scan_targets():
        try:
            text = path.read_text(encoding="utf-8", errors="ignore").lower()
        except Exception:
            continue
        text = " ".join(text.split())
        files_scanned += 1
        hit = None
        for stem in stems:
            if len(stem) >= 12 and stem in text:
                hit = len(stem)
                break
        is_aggregate = path.parent == meta_dir and path.name in ALLOWED_DATA_FILES
        if not hit and is_aggregate:
            for marker in FORBIDDEN_IN_AGGREGATES:
                if marker in text:
                    hit = -1
                    break
        if hit:
            offenders.append((str(path.relative_to(BRANDMORPH_ROOT)), hit))

    print(f"scanned_files={files_scanned} restricted_stems={len(stems)}")
    if offenders:
        print(f"LEAK DETECTED in {len(offenders)} file(s):")
        for rel, marker_len in offenders:
            print(f"  {rel} (match length {marker_len})")
        print("GATE FAILED")
        return 1
    print("NO LEAKAGE FOUND -> GATE PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
