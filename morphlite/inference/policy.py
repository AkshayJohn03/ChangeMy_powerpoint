"""Confidence-based transformation policy.

The model predicts; the policy decides. The renderer never sees raw probabilities.
"""
from __future__ import annotations

APPLY = "APPLY"
REVIEW = "REVIEW"
PRESERVE = "PRESERVE"
NOOP = "NOOP"

REVIEW_BAND_MIN_CONFIDENCE = 0.50


class PolicyEngine:
    def __init__(self, thresholds_payload: dict):
        self.schema_version = thresholds_payload.get("schema_version")
        self.classes = thresholds_payload["classes"]
        self.non_apply = set(thresholds_payload.get("non_apply_classes", ["UNCHANGED"]))

    def decide(self, argmax: str, confidence: float) -> dict:
        if argmax in self.non_apply:
            return {"policy": NOOP, "threshold": None,
                    "reason": f"{argmax} is a non-action class"}
        cfg = self.classes.get(argmax)
        if cfg is None:
            return {"policy": PRESERVE, "threshold": None,
                    "reason": "unknown class in policy table"}
        t = cfg.get("auto_apply_threshold")
        if t is None:
            if confidence >= REVIEW_BAND_MIN_CONFIDENCE:
                return {"policy": REVIEW, "threshold": None,
                        "reason": f"{cfg.get('reason','review_only')} and confidence {confidence:.2f} >= review band"}
            return {"policy": PRESERVE, "threshold": None,
                    "reason": f"{cfg.get('reason','review_only')} below review band"}
        if confidence >= t:
            return {"policy": APPLY, "threshold": t,
                    "reason": f"confidence {confidence:.2f} >= apply threshold {t:.2f}"}
        if confidence >= REVIEW_BAND_MIN_CONFIDENCE:
            return {"policy": REVIEW, "threshold": t,
                    "reason": f"below apply threshold {t:.2f}, inside review band"}
        return {"policy": PRESERVE, "threshold": t,
                "reason": f"below apply threshold {t:.2f} and review band"}
