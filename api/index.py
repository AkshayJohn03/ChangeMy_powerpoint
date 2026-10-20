"""Vercel serverless entrypoint — wraps BrandMorph FastAPI.

Vercel Python runtime expects an ASGI `app` at module level. We reuse
backend/main.py unchanged but expose it here for the /api/* rewrite.
"""
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
backend_path = REPO_ROOT / "backend"

for p in (str(REPO_ROOT), str(backend_path)):
    if p not in sys.path:
        sys.path.insert(0, p)

from backend.main import app  # noqa: E402, F401

__all__ = ["app"]
