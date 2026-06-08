"""
Trajectory estimator — summarises the direction of a salience series.

Estimates a linear slope over a series and classifies the trajectory as
``rising`` / ``falling`` / ``stable``, attaching a bounded terminal
:class:`UncertaintyBand` for the projected end value.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from attention.forecasting.forecast_uncertainty import ForecastUncertainty, UncertaintyBand


def _clamp_unit(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _slope(series: list[float]) -> float:
    if len(series) < 2:
        return 0.0
    return (series[-1] - series[0]) / (len(series) - 1)


@dataclass
class TrajectoryEstimate:
    """A summarised salience trajectory."""

    direction: str
    slope: float
    terminal_band: UncertaintyBand
    sample_count: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "direction": self.direction,
            "slope": round(self.slope, 4),
            "terminal_band": self.terminal_band.to_dict(),
            "sample_count": self.sample_count,
        }


class TrajectoryEstimator:
    """Estimates the direction and terminal band of a salience series."""

    def __init__(
        self,
        uncertainty: ForecastUncertainty | None = None,
        flat_threshold: float = 0.01,
    ) -> None:
        self.uncertainty = uncertainty or ForecastUncertainty()
        self.flat_threshold = abs(float(flat_threshold))

    def estimate(self, series: list[float], horizon_factor: float = 1.0) -> TrajectoryEstimate:
        n = len(series)
        if n == 0:
            band = self.uncertainty.band(0.0, horizon_factor=horizon_factor, sample_count=1)
            return TrajectoryEstimate("stable", 0.0, band, 0)

        slope = _slope(series)
        terminal_value = _clamp_unit(series[-1] + slope * horizon_factor)
        band = self.uncertainty.band(terminal_value, horizon_factor=horizon_factor, sample_count=n)

        if slope > self.flat_threshold:
            direction = "rising"
        elif slope < -self.flat_threshold:
            direction = "falling"
        else:
            direction = "stable"

        return TrajectoryEstimate(direction, slope, band, n)
