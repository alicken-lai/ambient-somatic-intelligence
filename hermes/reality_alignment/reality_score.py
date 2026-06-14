"""Reality score computation."""

from __future__ import annotations

from statistics import mean
from typing import Any

from hermes.reality_alignment.reality_models import RealityObservation, RealityTarget


def compute_reality_score(target: RealityTarget, observations: list[RealityObservation] | None = None) -> dict[str, Any]:
    observations = observations or []
    if observations:
        external = [item.agreement for item in observations if item.source_type == "external"]
        agreement = mean([item.agreement for item in observations])
        verification = mean([1.0 if item.verification_success else 0.0 for item in observations])
        outcome = mean([item.outcome_quality for item in observations])
        external_agreement = mean(external) if external else agreement * 0.85
    else:
        agreement = target.verification_success
        verification = target.verification_success
        outcome = target.outcome_quality or target.historical_quality
        external_agreement = 0.0

    score = (
        agreement * 30.0
        + external_agreement * 25.0
        + verification * 25.0
        + outcome * 20.0
    )
    score = round(max(0.0, min(100.0, score)), 2)
    confidence = round(min(1.0, max(0.0, (target.confidence * 0.45) + (score / 100.0 * 0.55))), 4)
    reasoning = [
        f"belief_accuracy={agreement:.2f}",
        f"external_agreement={external_agreement:.2f}",
        f"verification_success={verification:.2f}",
        f"historical_outcome_quality={outcome:.2f}",
    ]
    if not observations:
        reasoning.append("no external observations available; score uses internal verification and outcome signals only")
    return {"reality_score": score, "confidence": confidence, "reasoning": reasoning}
