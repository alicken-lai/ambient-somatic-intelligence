"""Uncertainty rebalancer — advisory skew correction hints."""

from __future__ import annotations

from typing import Any

from observability.v04.metric_normalizer import clamp01


class UncertaintyRebalancer:
    SKEW_THRESHOLD = 0.30

    def skew(
        self,
        *,
        uncertainty: float = 0.35,
        governed_salience: float = 0.5,
        metacognition_score: float = 0.7,
    ) -> float:
        """High salience + low uncertainty + low meta score => risky skew."""
        if uncertainty >= 0.5:
            return 0.0
        overconfidence = clamp01(governed_salience - uncertainty)
        meta_gap = clamp01(metacognition_score - 0.55) if metacognition_score < 0.55 else 0.0
        return clamp01(overconfidence * 0.6 + meta_gap * 0.4)

    def recommend(
        self,
        *,
        uncertainty: float = 0.35,
        governed_salience: float = 0.5,
        metacognition_score: float = 0.7,
    ) -> list[str]:
        s = self.skew(
            uncertainty=uncertainty,
            governed_salience=governed_salience,
            metacognition_score=metacognition_score,
        )
        if s < self.SKEW_THRESHOLD:
            return []
        return [
            "increase_uncertainty_weight_in_next_arbitration",
            "avoid_certainty_inflation_on_replay_derived_signals",
        ]

    def assess(
        self,
        *,
        uncertainty: float = 0.35,
        governed_salience: float = 0.5,
        metacognition_score: float = 0.7,
    ) -> dict[str, Any]:
        s = self.skew(
            uncertainty=uncertainty,
            governed_salience=governed_salience,
            metacognition_score=metacognition_score,
        )
        return {
            "uncertainty_skew": round(s, 4),
            "rebalanced": s < self.SKEW_THRESHOLD,
            "recommendations": self.recommend(
                uncertainty=uncertainty,
                governed_salience=governed_salience,
                metacognition_score=metacognition_score,
            ),
            "disclaimer": "rebalance_advisory_no_override",
        }
