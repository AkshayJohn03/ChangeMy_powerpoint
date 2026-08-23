"""Production action predictor (loads frozen brandmorph_action_model artifact)."""
from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np

from .. import config

MODELS_DIR = config.BRANDMORPH_ROOT / "models"
DEFAULT_ARTIFACT = MODELS_DIR / "brandmorph_action_model.joblib"


class ActionPredictor:
    def __init__(self, bundle: dict):
        self.model = bundle["model"]
        self.feature_names: list[str] = bundle["feature_names"]
        self.labels: list[str] = bundle["labels"]
        self.schema_version: str = bundle["schema_version"]
        self.winner: str = bundle.get("winner", "unknown")

    @classmethod
    def load(cls, path: Path | None = None) -> "ActionPredictor":
        p = Path(path or DEFAULT_ARTIFACT)
        if not p.exists():
            raise FileNotFoundError(f"production model not found: {p}")
        return cls(joblib.load(p))

    def predict(self, base_dicts: list[dict]) -> list[dict]:
        X = np.array([[float(b.get(k) or 0.0) for k in self.feature_names] for b in base_dicts])
        P = self.model.predict_proba(X)
        cols = [list(self.model.classes_).index(c) for c in self.labels]
        out = []
        for row in P[:, cols]:
            probs = {lab: round(float(p), 4) for lab, p in zip(self.labels, row)}
            argmax = max(probs, key=probs.get)
            out.append({"probs": probs, "argmax": argmax,
                        "confidence": probs[argmax], "schema_version": self.schema_version})
        return out


def load_policy_thresholds(path: Path | None = None) -> dict:
    p = Path(path or config.METADATA_DIR / "POLICY_THRESHOLDS.json")
    if not p.exists():
        raise FileNotFoundError(f"policy thresholds not found: {p}")
    return json.loads(p.read_text(encoding="utf-8"))
