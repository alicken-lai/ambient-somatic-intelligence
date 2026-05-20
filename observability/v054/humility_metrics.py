"""Forecast humility observability."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from attention.calibration.forecast_humility import ForecastHumility


@dataclass
class HumilityMetrics:
    mean_humility_factor: float = 1.0
    high_confidence_samples: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "mean_humility_factor": round(self.mean_humility_factor, 4),
            "high_confidence_samples": self.high_confidence_samples,
        }


def collect_humility_metrics(
    humility: ForecastHumility,
    raw_confidences: list[float],
    *,
    band_width: float = 0.15,
) -> HumilityMetrics:
    factors = [humility.humility_factor(c, band_width=band_width) for c in raw_confidences]
    high = sum(1 for c in raw_confidences if c >= humility.high_confidence_threshold)
    return HumilityMetrics(
        mean_humility_factor=sum(factors) / len(factors) if factors else 1.0,
        high_confidence_samples=high,
    )
