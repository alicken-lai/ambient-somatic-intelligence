"""Identity health scoring."""

from __future__ import annotations

from typing import Any


def compute_identity_health(*, coherence: dict[str, Any], continuity: dict[str, Any], drift: dict[str, Any], classifications: list[dict[str, Any]]) -> dict[str, object]:
    stable = continuity["continuity_metrics"]["stable_commitment_count"]
    changes = continuity["continuity_metrics"]["change_count"]
    experimental = sum(1 for item in classifications if item["classification"] == "Experimental Belief")
    score = float(coherence["coherence_score"])
    score += min(10.0, stable)
    score -= min(15.0, changes * 1.5)
    score -= min(10.0, experimental)
    if drift["drift_detected"]:
        score -= 20.0 if drift["severity"] == "high" else 8.0
    score = round(max(0.0, min(100.0, score)), 2)
    risk = "low" if score >= 75 else "medium" if score >= 50 else "high"
    return {"identity_health": score, "risk": risk}
