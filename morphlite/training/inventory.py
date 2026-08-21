"""Dataset inventory scanner and sorter.

Scans the OneDrive source roots, detects raw/branded roles by filename and
folder conventions, pairs raw <-> branded decks, copies everything into the
normalized data/source workspace (originals untouched) and emits manifests:

    data/metadata/file_manifest.jsonl
    data/metadata/pairs_auto_detected.jsonl
    data/metadata/inventory.json
    data/metadata/DATASET_REPORT.md

Usage:
    python -m morphlite.training.inventory --dry-run
    python -m morphlite.training.inventory --apply
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import zipfile
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from .. import config
from ..naming import (
    ROLE_CLEAN,
    ROLE_RAW,
    ROLE_TEMPLATE,
    detect_template,
    folder_role,
    normalize_name,
)

PPT_EXTS = {".pptx", ".ppt"}
SLIDE_RE = re.compile(r"^ppt/slides/slide\d+\.xml$")
SLDSZ_RE = re.compile(r'<p:sldSz[^>]*cx="(\d+)"[^>]*cy="(\d+)"')
EMU_PER_INCH = 914400


def md5_of(path: Path) -> str:
    h = hashlib.md5()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def inspect_pptx(path: Path) -> tuple[int | None, str | None]:
    try:
        with zipfile.ZipFile(path) as zf:
            names = zf.namelist()
            slides = sum(1 for n in names if SLIDE_RE.match(n))
            size = None
            pres = next((n for n in names if n == "ppt/presentation.xml"), None)
            if pres:
                m = SLDSZ_RE.search(zf.read(pres).decode("utf-8", "ignore"))
                if m:
                    w = round(int(m.group(1)) / EMU_PER_INCH, 3)
                    h = round(int(m.group(2)) / EMU_PER_INCH, 3)
                    size = f"{w}x{h}"
        return slides, size
    except Exception:
        return None, None


def in_parts(rel_lower: str, parts) -> bool:
    return any(part.lower() in rel_lower for part in parts)


def _cache_load() -> dict:
    f = config.METADATA_DIR / ".hash_cache.json"
    if f.exists():
        try:
            return json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def _cache_save(cache: dict) -> None:
    config.METADATA_DIR.mkdir(parents=True, exist_ok=True)
    (config.METADATA_DIR / ".hash_cache.json").write_text(
        json.dumps(cache), encoding="utf-8"
    )


_CACHE = _cache_load()


def cached_inspect(path: Path) -> tuple[str, int | None, str | None]:
    st = path.stat()
    ck = f"{path}|{st.st_size}|{st.st_mtime_ns}"
    hit = _CACHE.get(ck)
    if hit:
        return hit["md5"], hit["slides"], hit["slide_size"]
    digest = md5_of(path)
    slides, size = inspect_pptx(path)
    _CACHE[ck] = {"md5": digest, "slides": slides, "slide_size": size}
    if len(_CACHE) % 10 == 0:
        _cache_save(_CACHE)
        print(f"  inspected {len(_CACHE)} files...", flush=True)
    return digest, slides, size


def scan() -> list[dict]:
    records = []
    for batch, root_str, convention in config.DOCUMENT_ROOTS:
        root = Path(root_str)
        if not root.is_dir():
            continue
        for path in sorted(root.rglob("*")):
            if not path.is_file() or path.suffix.lower() not in PPT_EXTS:
                continue
            if path.stem.startswith("~$"):
                continue
            rel_lower = "\\".join([batch] + list(path.relative_to(root).parts[:-1])).lower()
            info = normalize_name(path.stem)
            evidence = []
            role = None
            conf = 0.5

            frole = folder_role(path, config.RAW_FOLDER_NAMES, config.CLEAN_FOLDER_NAMES)
            if info.had_raw_marker:
                role, conf = ROLE_RAW, 0.95
                evidence.append("raw_marker_in_filename")
            elif frole == ROLE_RAW:
                role, conf = ROLE_RAW, 0.90
                evidence.append("parent_folder_raw")
            elif frole == ROLE_CLEAN:
                role, conf = ROLE_CLEAN, 0.90
                evidence.append("parent_folder_clean")

            if role is None and in_parts(rel_lower, config.DUPLICATE_CHECK_PATH_PARTS):
                role, conf = ROLE_CLEAN, 0.60
                evidence.append("duplicate_tree_needs_verification")

            if role is None:
                if detect_template(path, config.TEMPLATE_HINTS, config.TEMPLATE_EXACT):
                    role, conf = ROLE_TEMPLATE, 0.95
                    evidence.append("template_name_hint")
                elif convention == "clean_only":
                    role, conf = ROLE_CLEAN, 0.80
                    evidence.append("batch_marked_clean")
                else:
                    role, conf = ROLE_CLEAN, 0.70
                    evidence.append("default_clean_candidate")

            print(f"[{batch}] file {len(records) + 1}", flush=True)
            digest, slides, slide_size = cached_inspect(path)
            records.append(
                {
                    "path": str(path),
                    "batch": batch,
                    "rel_dir": rel_lower,
                    "size": path.stat().st_size,
                    "md5": digest,
                    "slides": slides,
                    "slide_size": slide_size,
                    "key": info.key,
                    "had_version_token": info.had_version_token,
                    "convention": convention,
                    "role": role,
                    "confidence": conf,
                    "evidence": evidence,
                    "alternating_confirmed": False,
                    "alternating_candidate": False,
                }
            )
    return records


def mark_alternating(records: list[dict]) -> None:
    for r in records:
        stem_key = r["key"]
        if any(s in stem_key or s in r["path"].lower() for s in config.ALTERNATING_CONFIRMED_SUBSTRINGS):
            r["alternating_confirmed"] = True
        elif in_parts(r["rel_dir"], config.ALTERNATING_CANDIDATE_PATH_PARTS):
            r["alternating_candidate"] = True


def dedupe(records: list[dict]) -> None:
    seen: dict[str, dict] = {}
    for r in sorted(records, key=lambda x: (-x["confidence"], len(x["path"]))):
        first = seen.get(r["md5"])
        if first is not None:
            r["duplicate_of"] = first["path"]
        else:
            seen[r["md5"]] = r


def pair(records: list[dict]) -> list[dict]:
    groups: dict[tuple, list[dict]] = defaultdict(list)
    for r in records:
        if "duplicate_of" not in r:
            groups[(r["batch"], r["key"])].append(r)

    pairs = []
    idx = 0
    for (batch, key), members in sorted(groups.items()):
        for m in members:
            m["_paired"] = False
        raws = [m for m in members if m["role"] == ROLE_RAW]
        cleans = [m for m in members if m["role"] == ROLE_CLEAN]
        for raw in raws:
            same_dir = [c for c in cleans if "_partner" not in c and Path(c["path"]).parent == Path(raw["path"]).parent]
            pool = same_dir or [c for c in cleans if "_partner" not in c]
            if not pool:
                raw["_unpaired"] = True
                continue
            clean = pool[0]
            clean["_partner"] = True
            clean["_paired"] = True
            raw["_paired"] = True
            idx += 1
            conf = 0.95 if same_dir else 0.85
            pairs.append(
                {
                    "pair_id": f"pair_{idx:04d}",
                    "batch": batch,
                    "key": raw["key_public"],
                    "raw_slide": raw["path"],
                    "branded_slide": clean["path"],
                    "pair_confidence": conf,
                    "basis": "same_dir_filename" if same_dir else "folder_convention",
                    "status": "AUTO_PAIRED",
                }
            )
    return pairs


def assign_buckets(records: list[dict], pairs: list[dict]) -> None:
    paired_paths = set()
    for p in pairs:
        paired_paths.add(p["raw_slide"])
        paired_paths.add(p["branded_slide"])

    for r in records:
        if "duplicate_of" in r:
            r["bucket"] = None
            continue
        if r["role"] == ROLE_TEMPLATE:
            r["bucket"] = "template"
        elif r.get("_paired"):
            r["bucket"] = "paired_raw" if r["role"] == ROLE_RAW else "paired_branded"
        elif r["role"] == ROLE_RAW:
            r["bucket"] = "raw_only"
        elif r["alternating_confirmed"]:
            r["bucket"] = "alternating"
            r["evidence"].append("category_b_user_confirmed")
        elif r["alternating_candidate"]:
            r["bucket"] = "alternating"
            r["evidence"].append("category_b_candidate")
        elif r["confidence"] <= 0.60:
            r["bucket"] = "review"
        elif not r.get("had_version_token") and r["convention"] != "clean_only":
            r["bucket"] = "review"
            r["confidence"] = 0.55
            r["evidence"].append("unversioned_variant_needs_verification")
        else:
            r["bucket"] = "branded_only"


BUCKETS = {
    "paired_raw": config.BUCKET_PAIRED_RAW,
    "paired_branded": config.BUCKET_PAIRED_BRANDED,
    "alternating": config.BUCKET_ALTERNATING,
    "raw_only": config.BUCKET_RAW_ONLY,
    "branded_only": config.BUCKET_BRANDED_ONLY,
    "template": config.BUCKET_TEMPLATE,
    "review": config.BUCKET_REVIEW,
}


def assign_opaque_ids(records: list[dict]) -> tuple[dict, dict]:
    """Assign deck_NNNN ids + family tokens. Returns (fam_map, reg_entries)."""
    fam_map: dict[str, str] = {}
    for r in sorted(records, key=lambda x: (x["batch"], x["rel_dir"], x["key"])):
        if r["key"] not in fam_map:
            fam_map[r["key"]] = f"fam_{len(fam_map) + 1:03d}"

    registry = {}
    for n, r in enumerate(sorted(records, key=lambda x: (x["batch"], x["rel_dir"], x["key"], x["md5"])), 1):
        opaque = f"deck_{n:04d}"
        r["opaque_id"] = opaque
        r["family"] = fam_map[r["key"]]
        registry[opaque] = {
            "original_path": r["path"],
            "original_filename": Path(r["path"]).name,
            "md5": r["md5"],
            "batch": r["batch"],
            "bucket": r.get("bucket") or r["batch"],
            "family": fam_map[r["key"]],
        }
        r["key_public"] = fam_map[r["key"]]
    return fam_map, registry


def write_registry(registry: dict) -> None:
    payload = {
        "_notice": "RESTRICTED: opaque->original mapping. Never display or transmit.",
        "decks": dict(sorted(registry.items())),
    }
    (config.METADATA_DIR / "deck_registry.json").write_text(
        json.dumps(payload, indent=1, ensure_ascii=False), encoding="utf-8"
    )


def materialize(records: list[dict], apply_changes: bool) -> None:
    used: set[str] = set()
    for r in records:
        if r["bucket"] is None:
            r["dest"] = None
            continue
        batch_dir = BUCKETS[r["bucket"]] / r["batch"]
        target = batch_dir / f"{r['opaque_id']}{Path(r['path']).suffix.lower()}"
        while apply_changes and target.exists() and md5_of(target) != r["md5"]:
            raise RuntimeError(f"opaque id collision with different content: {target.name}")
        used.add(str(target).lower())
        r["dest"] = str(target)
        if apply_changes:
            batch_dir.mkdir(parents=True, exist_ok=True)
            if not target.exists():
                shutil.copy2(r["path"], target)


def write_outputs(records: list[dict], pairs: list[dict], apply_changes: bool) -> dict:
    config.METADATA_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).isoformat()

    with open(config.METADATA_DIR / "file_manifest.jsonl", "w", encoding="utf-8") as fh:
        for r in records:
            row = {k: v for k, v in r.items() if not k.startswith("_")}
            row["name_key"] = row.pop("key", "")
            row["rel_dir"] = "<restricted>"
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")

    with open(config.METADATA_DIR / "pairs_auto_detected.jsonl", "w", encoding="utf-8") as fh:
        for p in pairs:
            fh.write(json.dumps(p, ensure_ascii=False) + "\n")

    unique = [r for r in records if "duplicate_of" not in r]
    sizes = defaultdict(int)
    for r in unique:
        if r["slide_size"]:
            sizes[r["slide_size"]] += 1

    inventory = {
        "generated_at": stamp,
        "applied": apply_changes,
        "total_decks": len(unique),
        "total_slides": sum(r["slides"] or 0 for r in unique),
        "paired_raw": sum(1 for r in unique if r["bucket"] == "paired_raw"),
        "paired_branded": sum(1 for r in unique if r["bucket"] == "paired_branded"),
        "auto_pairs": len(pairs),
        "alternating_decks": sum(1 for r in unique if r["bucket"] == "alternating"),
        "raw_only_decks": sum(1 for r in unique if r["bucket"] == "raw_only"),
        "branded_only_decks": sum(1 for r in unique if r["bucket"] == "branded_only"),
        "template_decks": sum(1 for r in unique if r["bucket"] == "template"),
        "review_decks": sum(1 for r in unique if r["bucket"] == "review"),
        "duplicates": sum(1 for r in records if "duplicate_of" in r),
        "slide_size_distribution": dict(sorted(sizes.items(), key=lambda kv: -kv[1])),
        "node_type_distribution": {},
        "note_node_types": "requires Phase 1 AST extraction",
    }
    with open(config.METADATA_DIR / "inventory.json", "w", encoding="utf-8") as fh:
        json.dump(inventory, fh, indent=2, ensure_ascii=False)

    lines = [
        "# MorphLite Dataset Report",
        "",
        f"Generated: {stamp}  |  Applied: {apply_changes}",
        "",
        "| Bucket | Decks |",
        "|---|---|",
        f"| Paired raw | {inventory['paired_raw']} |",
        f"| Paired branded | {inventory['paired_branded']} |",
        f"| Alternating (Cat B) | {inventory['alternating_decks']} |",
        f"| Raw-only | {inventory['raw_only_decks']} |",
        f"| Branded-only | {inventory['branded_only_decks']} |",
        f"| Template | {inventory['template_decks']} |",
        f"| Review | {inventory['review_decks']} |",
        f"| Exact duplicates skipped | {inventory['duplicates']} |",
        "",
        f"Total decks: **{inventory['total_decks']}**  |  Total slides: **{inventory['total_slides']}**",
        "",
        "## Slide size distribution",
        "",
        "| Size (in) | Count |",
        "|---|---|",
    ]
    for size, cnt in inventory["slide_size_distribution"].items():
        lines.append(f"| {size} | {cnt} |")
    lines += ["", "## Auto-detected pairs", ""]
    for p in pairs:
        lines.append(f"- `{p['pair_id']}` ({p['basis']}, conf {p['pair_confidence']}): `{Path(p['raw_slide']).name}` <-> `{Path(p['branded_slide']).name}`")
    with open(config.METADATA_DIR / "DATASET_REPORT.md", "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")

    return inventory


def main() -> None:
    ap = argparse.ArgumentParser(description="MorphLite dataset inventory & sorter")
    ap.add_argument("--apply", action="store_true", help="copy files into data/source (default: dry run)")
    args = ap.parse_args()

    records = scan()
    _cache_save(_CACHE)
    mark_alternating(records)
    dedupe(records)
    _fam_map, registry = assign_opaque_ids(records)
    pairs = pair(records)
    assign_buckets(records, pairs)
    materialize(records, args.apply)
    write_registry(registry)
    inv = write_outputs(records, pairs, args.apply)

    print(json.dumps(inv, indent=2))


if __name__ == "__main__":
    main()
