"""Precursor forecast observability."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from attention.forecasting.precursor_forecast import PrecursorForecast, PrecursorForecastPoint
from attention.core.precursor_signal import PrecursorSignal


@dataclass
class PrecursorForecastMetrics:
    match_count: int = 0
    mean_likelihood: float = 0.0
    mean_confidence: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "match_count": self.match_count,
            "mean_likelihood": round(self.mean_likelihood, 4),
            "mean_confidence": round(self.mean_confidence, 4),
        }


def collect_precursor_forecast_metrics(
    forecaster: PrecursorForecast,
    signals: list[PrecursorSignal],
) -> PrecursorForecastMetrics:
    points = forecaster.forecast_batch(signals)
    if not points:
        return PrecursorForecastMetrics()
    return PrecursorForecastMetrics(
        match_count=len(points),
        mean_likelihood=sum(p.likelihood for p in points) / len(points),
        mean_confidence=sum(p.band.confidence for p in points) / len(points),
    )
