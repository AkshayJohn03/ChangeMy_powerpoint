"""Safety layer: decks are an attack surface (SECURITY.md).

A .pptx is a ZIP of XML parts. A hostile deck can be:
  - a **zip bomb** (petabytes of XML behind a 40 KB file) -> ratio + total caps
  - a **zip-slip** archive (entry paths escaping the extraction dir) -> path rules
  - an **XML-entity bomb** ("billion laughs") -> hardened lxml parser that
    refuses entity expansion entirely

Every entry point that opens untrusted deck bytes (CLI, pipeline, API upload,
render) goes through validate_deck(); every lxml parse of untrusted XML uses
SAFE_PARSER. Limits are conservative defaults with env overrides.
"""

from __future__ import annotations

import os
import zipfile
from pathlib import Path

from lxml import etree

DEFAULT_MAX_TOTAL_UNCOMPRESSED = int(
    os.environ.get("BRANDMORPH_MAX_TOTAL_UNCOMPRESSED", str(250 * 1024 * 1024))  # 250 MB
)
DEFAULT_MAX_RATIO = int(os.environ.get("BRANDMORPH_MAX_COMPRESSION_RATIO", "200"))
DEFAULT_MAX_ENTRIES = int(os.environ.get("BRANDMORPH_MAX_ENTRIES", "5000"))
DEFAULT_MAX_UPLOAD = int(os.environ.get("BRANDMORPH_MAX_UPLOAD", str(120 * 1024 * 1024)))  # 120 MB

_MAGIC = b"PK\x03\x04"


class UnsafeDeckError(ValueError):
    """Raised when a deck fails safety validation. Message states which rule."""


# --- hardened XML parsing (entity bombs) -----------------------------------
SAFE_PARSER = etree.XMLParser(
    resolve_entities=False,
    no_network=True,
    load_dtd=False,
    dtd_validation=False,
    huge_tree=False,
    recover=False,
)


def safe_fromstring(xml_bytes: bytes):
    """lxml fromstring with entity expansion and network access disabled."""
    return etree.fromstring(xml_bytes, SAFE_PARSER)


# --- archive validation (zip bombs, zip slip, magic bytes) ------------------
def validate_deck(path: str | Path, *, max_total: int | None = None,
                  max_ratio: int | None = None,
                  max_entries: int | None = None) -> None:
    """Validate an untrusted .pptx before anything opens it.

    Raises UnsafeDeckError with a human-readable rule name. Cost is one pass
    over the central directory (no decompression) except for the ratio check
    which reads per-entry declared sizes — zip metadata can lie, so the ratio
    uses the *declared* uncompressed size, and the reader itself is additionally
    bounded by the total cap when parts are read later.
    """
    max_total = max_total if max_total is not None else DEFAULT_MAX_TOTAL_UNCOMPRESSED
    max_ratio = max_ratio if max_ratio is not None else DEFAULT_MAX_RATIO
    max_entries = max_entries if max_entries is not None else DEFAULT_MAX_ENTRIES

    p = Path(path)
    if not p.exists() or not p.is_file():
        raise UnsafeDeckError("not a file")
    with open(p, "rb") as f:
        if f.read(4) != _MAGIC:
            raise UnsafeDeckError("not a ZIP archive (bad magic bytes)")
    try:
        zf = zipfile.ZipFile(p)
    except zipfile.BadZipFile as e:
        raise UnsafeDeckError(f"corrupt ZIP: {e}") from e
    with zf:
        names = zf.namelist()
        if len(names) > max_entries:
            raise UnsafeDeckError(f"too many archive entries ({len(names)} > {max_entries})")
        if "[Content_Types].xml" not in names:
            raise UnsafeDeckError("missing [Content_Types].xml — not an OOXML package")
        total = 0
        for info in zf.infolist():
            name = info.filename
            if name.startswith("/") or "\\" in name or ".." in Path(name).parts:
                raise UnsafeDeckError(f"unsafe entry path: {name!r} (zip-slip)")
            declared = info.file_size
            total += declared
            if total > max_total:
                raise UnsafeDeckError(
                    f"declared uncompressed size exceeds cap ({total} > {max_total}) — "
                    f"probable zip bomb"
                )
            if declared > 0:
                ratio = declared // max(1, info.compress_size)
                if ratio > max_ratio:
                    raise UnsafeDeckError(
                        f"entry {name!r} compression ratio {ratio} > {max_ratio} — "
                        f"probable zip bomb"
                    )


def save_upload_bounded(upload, dst: str | Path, max_bytes: int | None = None) -> int:
    """Stream an upload to disk with a hard size cap (returns bytes written).

    Raises UnsafeDeckError past the cap — protects the API from memory/
    disk-exhaustion via oversized uploads (defense in depth alongside any
    reverse-proxy limit).
    """
    max_bytes = max_bytes if max_bytes is not None else DEFAULT_MAX_UPLOAD
    written = 0
    with open(dst, "wb") as out:
        while True:
            chunk = upload.file.read(1024 * 512)
            if not chunk:
                break
            written += len(chunk)
            if written > max_bytes:
                out.close()
                Path(dst).unlink(missing_ok=True)
                raise UnsafeDeckError(f"upload exceeds cap ({written} > {max_bytes})")
            out.write(chunk)
    return written
