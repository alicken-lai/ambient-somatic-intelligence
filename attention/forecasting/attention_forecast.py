"""
Attention forecast — the unified forecasting facade.

Ties together salience projection, trajectory estimation, precursor forecasting,
and pressure forecasting for a target over a chosen :class:`ForecastWindow`.
Every result is explicitly labelled a *probabilistic projection, not a
prediction* via :data:`FORECAST_DISCLAIMER`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from attention.consolidation.attention_memory_store import AttentionMemoryStore
from attention.consolidation.precursor_memory import PrecursorMemory
from attention.consolidation.salience_history import SalienceHistory
from attention.core.attention_target import AttentionTarget
from attention.forecasting.forecast_uncertainty import ForecastUncertainty
from attention.forecasting.forecast_window import FORECAST_WINDOWS
from attention.forecasting.precursor_forecast import PrecursorForecast, PrecursorForecastPoint
from attention.forecasting.salience_pressure_forecast import (
    PressureForecast,
    SaliencePressureForecast,
)
from attention.forecasting.salience_projection import SalienceProjection, SalienceProjectionPoint
from attention.forecasting.trajectory_estimator import TrajectoryEstimate, TrajectoryEstimator
from attention.kernel.attention_kernel import AttentionKernel

FORECAST_DISCLAIMER: str = "probabilistic_projection_not_prediction"


@dataclass
class AttentionForecastResult:
    """The unified forecast for a single target over one window."""

    target_id: str
    window: str
    projections: list[SalienceProjectionPoint] = field(default_factory=list)
    precursor_points: list[PrecursorForecastPoint] = field(default_factory=list)
    pressure: Optional[PressureForecast] = None
    trajectory: Optional[TrajectoryEstimate] = None
    disclaimer: str = FORECAST_DISCLAIMER

    def to_dict(self) -> dict[str, Any]:
        return {
            "target_id": self.target_id,
            "window": self.window,
            "projections": [p.to_dict() for p in self.projections],
            "precursor_points": [p.to_dict() for p in self.precursor_points],
            "pressure": self.pressure.to_dict() if self.pressure else None,
            "trajectory": self.trajectory.to_dict() if self.trajectory else None,
            "disclaimer": self.disclaimer,
        }


class AttentionForecast:
    """Unified probabilistic forecasting facade over the attention layer."""

    def __init__(
        self,
        kernel: Optional[AttentionKernel] = None,
        store: Optional[AttentionMemoryStore] = None,
        precursor_memory: Optional[PrecursorMemory] = None,
        history: Optional[SalienceHistory] = None,
        uncertainty: Optional[ForecastUncertainty] = None,
    ) -> None:
        self.kernel = kernel if kernel is not None else AttentionKernel()
        self.store = store if store is not None else AttentionMemoryStore()
        self.precursor_memory = precursor_memory
        self.uncertainty = uncertainty or ForecastUncertainty()
        self.history = history or SalienceHistory()

        self.projection = SalienceProjection(self.history, self.uncertainty)
        self.precursor_forecast = PrecursorForecast(self.precursor_memory, self.uncertainty)
        self.pressure_forecast = SaliencePressureForecast(self.kernel, self.uncertainty)
        self.trajectory_estimator = TrajectoryEstimator(self.uncertainty)

    def ingest(self, target: AttentionTarget) -> dict[str, Any]:
        """Record a target's salience so it can be projected later."""
        salience = target.salience or self.kernel.engine.compute(target)
        self.history.record(target.target_id, salience.total)
        return {"target_id": target.target_id, "salience": round(salience.total, 4)}

    def forecast(self, target_id: str, window: str = "24h") -> AttentionForecastResult:
        win = FORECAST_WINDOWS.get(window, FORECAST_WINDOWS["24h"])
        projections = self.projection.project(target_id, steps=win.steps)
        series = self.history.series(target_id)
        trajectory = self.trajectory_estimator.estimate(series, horizon_factor=float(win.steps))
        pressure = self.pressure_forecast.forecast(target_id, horizon_factor=float(win.steps))
        return AttentionForecastResult(
            target_id=target_id,
            window=win.name,
            projections=projections,
            precursor_points=[],
            pressure=pressure,
            trajectory=trajectory,
        )

    def forecast_all_windows(self, target_id: str) -> dict[str, AttentionForecastResult]:
        return {name: self.forecast(target_id, name) for name in FORECAST_WINDOWS}
