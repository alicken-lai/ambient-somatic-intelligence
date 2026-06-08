"""
Salience projection — projects a target's salience forward over discrete steps.

Reads a target's recorded :class:`SalienceHistory`, estimates a linear trend, and
projects ``steps`` future points, each wrapped in a bounded
:class:`UncertaintyBand` whose width grows with the step index.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from attention.consolidation.salience_history import SalienceHistory
from attention.forecasting.forecast_uncertainty import ForecastUncertainty, UncertaintyBand


def _clamp_unit(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _slope(series: list[float]) -> float:
    if len(series) < 2:
        return 0.0
    return (series[-1] - series[0]) / (len(series) - 1)


@dataclass
class SalienceProjectionPoint:
    """One projected salience value at a future step."""

    step: int
    projected_salience: float
    band: UncertaintyBand

    def to_dict(self) -> dict[str, Any]:
        return {
            "step": self.step,
            "projected_salience": round(self.projected_salience, 4),
            "band": self.band.to_dict(),
        }


class SalienceProjection:
    """Projects future salience from a target's history."""

    def __init__(
        self,
        history: SalienceHistory,
        uncertainty: ForecastUncertainty | None = None,
    ) -> None:
        self.history = history
        self.uncertainty = uncertainty or ForecastUncertainty()

    def project(self, target_id: str, steps: int = 8) -> list[SalienceProjectionPoint]:
        series = self.history.series(target_id)
        if not series:
            return []
        base = series[-1]
        slope = _slope(series)
        n = len(series)
        points: list[SalienceProjectionPoint] = []
        for i in range(1, max(0, int(steps)) + 1):
            projected = _clamp_unit(base + slope * i)
            band = self.uncertainty.band(projected, horizon_factor=float(i), sample_count=n)
            points.append(SalienceProjectionPoint(step=i, projected_salience=projected, band=band))
        return points
