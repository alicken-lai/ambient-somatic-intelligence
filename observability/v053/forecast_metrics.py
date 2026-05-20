"""Core forecast observability metrics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from attention.forecasting.attention_forecast import AttentionForecast, AttentionForecastResult


@dataclass
class ForecastMetrics:
    projection_count: int = 0
    precursor_count: int = 0
    mean_confidence: float = 0.0
    pressure_headroom: float = 1.0
    trajectory_direction: str = "stable"

    def to_dict(self) -> dict[str, Any]:
        return {
            "projection_count": self.projection_count,
            "precursor_count": self.precursor_count,
            "mean_confidence": round(self.mean_confidence, 4),
            "pressure_headroom": round(self.pressure_headroom, 4),
            "trajectory_direction": self.trajectory_direction,
        }


def collect_forecast_metrics(result: AttentionForecastResult) -> ForecastMetrics:
    confs = [p.band.confidence for p in result.projections]
    mean_conf = sum(confs) / len(confs) if confs else 0.5
    pressure = result.pressure
    return ForecastMetrics(
        projection_count=len(result.projections),
        precursor_count=len(result.precursor_points),
        mean_confidence=mean_conf,
        pressure_headroom=pressure.headroom if pressure else 1.0,
        trajectory_direction=result.trajectory.direction if result.trajectory else "stable",
    )


def collect_from_forecaster(forecaster: AttentionForecast, target_id: str) -> ForecastMetrics:
    result = forecaster.forecast(target_id)
    return collect_forecast_metrics(result)
