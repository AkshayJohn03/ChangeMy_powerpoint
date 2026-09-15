"""Vercel serverless entrypoint — wraps BrandMorph FastAPI.

Vercel Python runtime expects an ASGI `app` at module level. We reuse
backend/main.py unchanged but expose it here for the /api/* rewrite.

For local dev, `backend/main.py` is still the entrypoint (uvicorn).
For Vercel, this file is the handler.
"""
import sys
from pathlib import Path

# Add repo roots so imports resolve both locally and on Vercel
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "backend"))

from backend.main import app  # noqa: E402, F401

# Vercel expects `app` to be importable
__all__ = ["app"]
