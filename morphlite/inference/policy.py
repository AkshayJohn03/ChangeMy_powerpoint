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
        remove_cfg = self.classes.get("REMOVE", {}).get("safety_gates", {})
        self.max_remove_per_slide = remove_cfg.get("max_remove_per_slide", 5)
        self.max_remove_fraction = remove_cfg.get("max_remove_fraction", 0.30)

    def apply_slide_budget(self, decisions: list[dict]) -> list[dict]:
        """Enforce per-slide REMOVE budget. Sorts by confidence desc, keeps top N."""
        remove_candidates = [d for d in decisions if d["action"] == "REMOVE" and d["policy"] == APPLY]
        if len(remove_candidates) <= self.max_remove_per_slide:
            return decisions
        sorted_cands = sorted(remove_candidates, key=lambda d: -d["confidence"])
        keep_set = set(id(d) for d in sorted_cands[:self.max_remove_per_slide])
        for d in decisions:
            if d["action"] == "REMOVE" and d["policy"] == APPLY and id(d) not in keep_set:
                d["policy"] = REVIEW
                d["reason"] = "slide_remove_budget_exceeded"
        return decisions

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
