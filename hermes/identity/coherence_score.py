"""Narrative coherence scoring."""

from __future__ import annotations

from typing import Any

from hermes.identity.identity_models import IdentityProfile


def compute_coherence_score(identity: IdentityProfile, classifications: list[dict[str, Any]], continuity: dict[str, Any], drift: dict[str, Any]) -> dict[str, Any]:
    core_count = sum(1 for item in classifications if item["classification"] == "Core Belief")
    retired_count = sum(1 for item in classifications if item["classification"] == "Retired Belief")
    stable_count = continuity["continuity_metrics"]["stable_commitment_count"]
    score = 60.0
    score += min(20.0, stable_count * 1.5)
    score += min(10.0, core_count * 2.0)
    score -= retired_count * 2.0
    if drift["drift_detected"]:
        score -= 25.0 if drift["severity"] == "high" else 10.0
    score = round(max(0.0, min(100.0, score)), 2)
    return {
        "coherence_score": score,
        "reasoning": [
            f"stable_commitments={stable_count}",
            f"core_beliefs={core_count}",
            f"retired_beliefs={retired_count}",
            f"drift={drift['severity']}",
            f"identity={identity.identity_id}",
        ],
    }
