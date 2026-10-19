"""Vercel Serverless Function entrypoint for FastAPI backend."""

import os
import sys

# Ensure backend directory is in python module search path
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from main import app  # noqa: F401, E402
