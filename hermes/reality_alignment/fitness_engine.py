"""Fitness scoring for beliefs, playbooks, skills, and strategies."""

from __future__ import annotations

from statistics import mean
from typing import Any

from hermes.reality_alignment.reality_models import FitnessResult, RealityTarget


class FitnessEngine:
    def score(self, target: RealityTarget, outcome_history: list[dict[str, Any]] | None = None) -> FitnessResult:
        outcome_history = outcome_history or []
        if outcome_history:
            qualities = [float(item.get("quality", 0.0)) for item in outcome_history]
            rois = [float(item.get("roi", 0.0)) for item in outcome_history]
            success = [1.0 if item.get("success", False) else 0.0 for item in outcome_history]
            score = (mean(qualities) * 45.0) + (mean(success) * 35.0) + (max(0.0, mean(rois)) * 20.0)
            trend = _trend(qualities)
            reasoning = ["fitness uses observed outcome history"]
        else:
            score = (target.outcome_quality * 45.0) + (target.historical_quality * 30.0) + (target.verification_success * 25.0)
            trend = "stable"
            reasoning = ["fitness uses current target outcome, historical quality, and verification signals"]
        return FitnessResult(
            target_id=target.target_id,
            target_type=target.target_type,
            fitness_score=round(max(0.0, min(100.0, score)), 2),
            trend=trend,
            reasoning=reasoning,
        )


def _trend(values: list[float]) -> str:
    if len(values) < 2:
        return "stable"
    delta = values[-1] - values[0]
    if delta > 0.05:
        return "improving"
    if delta < -0.05:
        return "declining"
    return "stable"
