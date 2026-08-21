"""Confidence fusion for rule/ML decisions.

    rule >= 0.90                 -> RULE
    0.60 <= rule < 0.90 + agree -> AGREEMENT (if ml_conf >= 0.65)
    ml  >= 0.85 (no rule)        -> ML
    otherwise                    -> FALLBACK_PRESERVE
"""
from __future__ import annotations

RULE_DOMINANT = 0.90
RULE_WINDOW = 0.60
ML_AGREE_MIN = 0.65
ML_SOLO_MIN = 0.85


def fuse(rule_conf: float | None, ml_conf: float | None, ops_agree: bool) -> tuple[str, str | None, float]:
    if rule_conf is not None and rule_conf >= RULE_DOMINANT:
        return "rule", "rule", rule_conf
    if rule_conf is not None and RULE_WINDOW <= rule_conf < RULE_DOMINANT:
        if ops_agree and ml_conf is not None and ml_conf >= ML_AGREE_MIN:
            return "agreement", "rule+ml", round(max(rule_conf, ml_conf), 3)
    if ml_conf is not None and ml_conf >= ML_SOLO_MIN:
        return "ml", "ml", ml_conf
    return "fallback_preserve", None, max(rule_conf or 0.0, ml_conf or 0.0)
