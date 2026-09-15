"""Phase 14: Wire v2 node model into pipeline with policy engine.

Architecture:
    Stage 1: Deterministic brand layer (backgrounds, fills, borders)
    Stage 2: ML per-node model (multiclass + binary MOVE/REMOVE)
    Stage 3: Policy engine (confidence + safety gates)
    Stage 4: Mutation engine (verified before/after)
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import numpy as np
import pptx
from pptx.util import Pt
from pptx.dml.color import RGBColor
from pptx.oxml.ns import qn

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from morphlite.pipeline.brand_profile import DEFAULT_PROFILE, BrandProfile
from morphlite.pipeline.mutation_engine import MutationEngine


class NodeModelInference:
    """Loads and runs the v2 per-node transformation model."""

    def __init__(self, model_path: str | None = None):
        p = Path(model_path or Path(__file__).resolve().parent.parent.parent / "models" / "brandmorph_node_model_v2.joblib")
        if not p.exists():
            self.available = False
            return
        bundle = joblib.load(p)
        self.multiclass = bundle["multiclass"]
        self.move_detector = bundle["move_detector"]
        self.remove_detector = bundle["remove_detector"]
        self.feature_names_base = bundle["feature_names_base"]
        self.feature_names_rel = bundle["feature_names_rel"]
        self.labels = bundle["labels"]
        self.move_threshold = bundle.get("move_threshold", 0.2)
        self.remove_threshold = bundle.get("remove_threshold", 0.5)
        self.schema_version = bundle.get("schema_version", "node_model_v2")
        self.available = True

    def predict(self, X_base: np.ndarray, X_rel: np.ndarray, X_slide: np.ndarray) -> list[dict]:
        X = np.hstack([X_base, X_rel, X_slide])
        mc_probs = self.multiclass.predict_proba(X)
        mc_labels = self.multiclass.classes_
        move_p = self.move_detector.predict_proba(X)
        remove_p = self.remove_detector.predict_proba(X)

        move_col = list(self.move_detector.classes_).index(1) if 1 in self.move_detector.classes_ else 0
        rem_col = list(self.remove_detector.classes_).index(1) if 1 in self.remove_detector.classes_ else 0

        results = []
        for i in range(len(X)):
            mc_idx = int(np.argmax(mc_probs[i]))
            action = str(mc_labels[mc_idx])
            mc_conf = float(mc_probs[i][mc_idx])

            move_prob = float(move_p[i][move_col]) if move_p.shape[1] > move_col else 0.0
            remove_prob = float(remove_p[i][rem_col]) if remove_p.shape[1] > rem_col else 0.0

            # Override with binary detector if confidence is higher
            if remove_prob > mc_probs[i][mc_idx] and remove_prob > 0.4:
                action = "REMOVE"
                mc_conf = remove_prob
            if move_prob > 0.3 and move_prob > mc_probs[i][mc_idx]:
                action = "MOVE"
                mc_conf = move_prob

            results.append({
                "action": action,
                "confidence": round(mc_conf, 4),
                "move_probability": round(move_prob, 4),
                "remove_probability": round(remove_prob, 4),
                "multiclass_probs": {str(mc_labels[j]): round(float(mc_probs[i][j]), 4) for j in range(len(mc_labels))},
            })
        return results


import joblib  # noqa: E402


class PolicyEngineV2:
    """Action-specific policy with structural safety gates."""

    def __init__(self, thresholds_path: str | None = None):
        p = Path(thresholds_path or Path(__file__).resolve().parent.parent.parent / "data" / "metadata" / "POLICY_THRESHOLDS.json")
        if p.exists():
            data = json.loads(p.read_text(encoding="utf-8"))
            self.classes = data.get("classes", {})
        else:
            self.classes = {}

        self.thresholds = {
            "REMOVE": self.classes.get("REMOVE", {}).get("auto_apply_threshold", 0.70),
            "RESIZE": self.classes.get("RESIZE", {}).get("auto_apply_threshold", 0.35),
            "RESTYLE": self.classes.get("RESTYLE", {}).get("auto_apply_threshold", 0.30),
            "RECOLOR": self.classes.get("RECOLOR", {}).get("auto_apply_threshold", 0.50),
            "MOVE": 0.90,  # very high bar for auto-apply
        }
        self.max_remove_per_slide = 5

    def decide(self, action: str, confidence: float, shape_info: dict) -> str:
        if action == "UNCHANGED":
            return "NOOP"

        threshold = self.thresholds.get(action, 0.90)

        if action == "REMOVE":
            # Structural guards
            if shape_info.get("is_table") or shape_info.get("is_chart"):
                return "PRESERVE"
            if shape_info.get("text_len", 0) > 200:
                return "REVIEW"
            if confidence >= threshold:
                return "APPLY"
            return "REVIEW"

        if action == "MOVE":
            return "REVIEW"  # always review in v0.2

        if confidence >= threshold:
            return "APPLY"
        if confidence >= threshold * 0.6:
            return "REVIEW"
        return "PRESERVE"


class SlideRemoveBudget:
    """Per-slide REMOVE circuit breaker."""

    def __init__(self, max_per_slide: int = 5, max_fraction: float = 0.30):
        self.max_per_slide = max_per_slide
        self.max_fraction = max_fraction

    def enforce(self, decisions: list[dict]) -> list[dict]:
        remove_candidates = [
            (i, d) for i, d in enumerate(decisions)
            if d["action"] == "REMOVE" and d["policy"] == "APPLY"
        ]
        total_nodes = len(decisions)
        max_allowed = min(self.max_per_slide, int(total_nodes * self.max_fraction))

        if len(remove_candidates) <= max_allowed:
            return decisions

        sorted_cands = sorted(remove_candidates, key=lambda x: -x[1].get("confidence", 0))
        keep_ids = set(id(d) for _, d in sorted_cands[:max_allowed])

        for i, d in remove_candidates:
            if id(d) not in keep_ids:
                d["policy"] = "REVIEW"
                d["reason"] = "slide_remove_budget_exceeded"

        return decisions
