"""Decision engine: predictor + policy -> final per-node verdicts.

v0.1 operates at the action-class level. Mapping an APPLY verdict to concrete
PPTX mutations (set_font_family, set_fill_color, ...) is delegated to the
deterministic rules engine + applier in a later integration step.
"""
from __future__ import annotations

from .policy import NOOP
from .predictor import ActionPredictor, load_policy_thresholds
from .policy import PolicyEngine


class DecisionEngine:
    def __init__(self, predictor: ActionPredictor | None = None,
                 thresholds_payload: dict | None = None):
        self.predictor = predictor or ActionPredictor.load()
        self.policy = PolicyEngine(
            thresholds_payload or load_policy_thresholds()
        )

    def decide_batch(self, base_dicts: list[dict]) -> list[dict]:
        preds = self.predictor.predict(base_dicts)
        decisions = []
        for p in preds:
            verdict = self.policy.decide(p["argmax"], p["confidence"])
            decisions.append(
                {
                    "action": p["argmax"],
                    "confidence": p["confidence"],
                    "probabilities": p["probs"],
                    "policy": verdict["policy"],
                    "threshold": verdict.get("threshold"),
                    "reason": verdict["reason"],
                    "model_schema": p["schema_version"],
                }
            )
        return decisions


def summarize(decisions: list[dict]) -> dict:
    counts: dict[str, int] = {}
    for d in decisions:
        counts[d["policy"]] = counts.get(d["policy"], 0) + 1
    return {"total": len(decisions), **{f"n_{k.lower()}": v for k, v in counts.items()}}
