"""Trajectory forecast metrics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from attention.forecasting.trajectory_estimator import TrajectoryEstimate


@dataclass
class TrajectoryMetrics:
    direction: str = "stable"
    slope: float = 0.0
    terminal_confidence: float = 0.0
    sample_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "direction": self.direction,
            "slope": round(self.slope, 4),
            "terminal_confidence": round(self.terminal_confidence, 4),
            "sample_count": self.sample_count,
        }


def collect_trajectory_metrics(estimate: TrajectoryEstimate) -> TrajectoryMetrics:
    return TrajectoryMetrics(
        direction=estimate.direction,
        slope=estimate.slope,
        terminal_confidence=estimate.terminal_band.confidence,
        sample_count=estimate.sample_count,
    )
