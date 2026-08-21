"""Load models only when they passed the promotion gate."""
from __future__ import annotations

import json
from pathlib import Path

from .. import config

MODELS_DIR = config.BRANDMORPH_ROOT / "morphlite" / "models"


def load_promoted(task: str, version: str = "v2"):
    meta_path = MODELS_DIR / f"morphlite_{task}_{version}.json"
    if not meta_path.exists():
        return None
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    if not meta.get("promoted"):
        return None
    model_path = MODELS_DIR / f"morphlite_{task}_{version}.joblib"
    if not model_path.exists():
        return None
    import joblib

    return {"model": joblib.load(model_path), "metadata": meta}


def available_models() -> dict:
    out = {}
    for task in ("intent", "node"):
        for version in ("v1", "v2"):
            entry = load_promoted(task, version)
            if entry:
                out[f"{task}_{version}"] = entry["metadata"]
    return out
