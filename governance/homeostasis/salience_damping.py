"""Salience damping — advisory damp factor when oscillation detected."""

from __future__ import annotations

from typing import Any

from observability.v04.metric_normalizer import clamp01


class SalienceDamping:
    """Suggests damping multiplier — never applied to governed salience directly."""

    MAX_ADVISORY_DAMP = 0.35

    def __init__(self) -> None:
        self._recent: list[float] = []

    def record_salience(self, governed_salience: float) -> None:
        self._recent.append(clamp01(governed_salience))
        if len(self._recent) > 10:
            self._recent = self._recent[-10:]

    def oscillation_pressure(self) -> float:
        if len(self._recent) < 4:
            return 0.0
        deltas = [
            abs(self._recent[i] - self._recent[i - 1])
            for i in range(1, len(self._recent))
        ]
        mean_delta = sum(deltas) / len(deltas)
        if mean_delta < 0.12:
            return 0.0
        return clamp01((mean_delta - 0.12) * 3.0)

    def advisory_damp_factor(
        self,
        *,
        governed_salience: float,
        pathology_pressure: float = 0.0,
    ) -> float:
        self.record_salience(governed_salience)
        osc = self.oscillation_pressure()
        combined = clamp01(osc * 0.6 + pathology_pressure * 0.4)
        return clamp01(combined * self.MAX_ADVISORY_DAMP)

    def recommend(
        self,
        *,
        governed_salience: float,
        pathology_pressure: float = 0.0,
    ) -> list[str]:
        factor = self.advisory_damp_factor(
            governed_salience=governed_salience,
            pathology_pressure=pathology_pressure,
        )
        if factor < 0.08:
            return []
        return [
            f"consider_salience_damp_factor:{factor:.3f}",
            "monitor_oscillation_before_next_submission",
        ]

    def assess(
        self,
        *,
        governed_salience: float,
        pathology_pressure: float = 0.0,
    ) -> dict[str, Any]:
        factor = self.advisory_damp_factor(
            governed_salience=governed_salience,
            pathology_pressure=pathology_pressure,
        )
        return {
            "advisory_damp_factor": round(factor, 4),
            "oscillation_pressure": round(self.oscillation_pressure(), 4),
            "recommendations": self.recommend(
                governed_salience=governed_salience,
                pathology_pressure=pathology_pressure,
            ),
            "disclaimer": "damping_advisory_not_applied_to_governance",
        }
