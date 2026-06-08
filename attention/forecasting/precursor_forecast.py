"""
Precursor forecast — projects likelihood that a precursor leads to an event.

Given a :class:`PrecursorSignal`, estimates the likelihood that the pattern
resolves into a salient event, boosted when the pattern has been observed before
(via :class:`PrecursorMemory`).  Each forecast carries a bounded uncertainty
band.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from attention.consolidation.precursor_memory import PrecursorMemory
from attention.core.precursor_signal import PrecursorSignal
from attention.forecasting.forecast_uncertainty import ForecastUncertainty, UncertaintyBand


def _clamp_unit(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


@dataclass
class PrecursorForecastPoint:
    """A forecast of how likely a precursor resolves into an event."""

    pattern_id: str
    likelihood: float
    matched: bool
    band: UncertaintyBand

    def to_dict(self) -> dict[str, Any]:
        return {
            "pattern_id": self.pattern_id,
            "likelihood": round(self.likelihood, 4),
            "matched": self.matched,
            "band": self.band.to_dict(),
        }


class PrecursorForecast:
    """Forecasts precursor resolution likelihoods, bounded by uncertainty."""

    def __init__(
        self,
        memory: PrecursorMemory | None = None,
        uncertainty: ForecastUncertainty | None = None,
        unseen_weight: float = 0.6,
    ) -> None:
        self.memory = memory
        self.uncertainty = uncertainty or ForecastUncertainty()
        self.unseen_weight = float(unseen_weight)

    def forecast_from_signal(self, signal: PrecursorSignal) -> PrecursorForecastPoint | None:
        if self.memory is not None:
            matched = self.memory.match(signal.pattern_id)
            if not matched:
                # A known memory that has never seen this pattern yields no forecast.
                return None
            likelihood = _clamp_unit(signal.strength)
        else:
            matched = False
            likelihood = _clamp_unit(signal.strength * self.unseen_weight)

        band = self.uncertainty.band(likelihood, horizon_factor=1.0, sample_count=1)
        return PrecursorForecastPoint(
            pattern_id=signal.pattern_id,
            likelihood=likelihood,
            matched=matched,
            band=band,
        )

    def forecast_batch(self, signals: list[PrecursorSignal]) -> list[PrecursorForecastPoint]:
        points: list[PrecursorForecastPoint] = []
        for signal in signals:
            point = self.forecast_from_signal(signal)
            if point is not None:
                points.append(point)
        return points
