"""Belief classification for separating identity from tactics."""

from __future__ import annotations

from typing import Any


def classify_belief(belief: dict[str, Any]) -> dict[str, Any]:
    statement = str(belief.get("statement", "")).lower()
    status = str(belief.get("status", "active"))
    confidence = float(belief.get("confidence", 0.0))
    reality_score = float(belief.get("reality_score", 0.0))
    if status.startswith("retire"):
        label = "Retired Belief"
        reason = "belief is already marked for retirement"
    elif any(term in statement for term in ["guardian", "governance", "safety", "append-only", "operator"]):
        label = "Core Belief"
        reason = "belief refers to persistent governance or safety identity"
    elif confidence >= 0.8 and reality_score >= 70:
        label = "Supporting Belief"
        reason = "belief has strong confidence and acceptable reality score"
    elif confidence < 0.55 or reality_score < 55:
        label = "Experimental Belief"
        reason = "belief needs more evidence before identity-level adoption"
    else:
        label = "Temporary Belief"
        reason = "belief is useful but not identity-defining"
    return {"belief_id": belief.get("belief_id"), "classification": label, "reason": reason}


def classify_beliefs(beliefs: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    return [classify_belief(belief) for belief in beliefs.values()]
