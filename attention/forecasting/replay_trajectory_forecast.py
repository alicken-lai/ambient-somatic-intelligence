"""
Replay trajectory forecast — replays recorded history to estimate a trajectory.

Replays a target's recorded :class:`SalienceHistory` and produces a single
:class:`TrajectoryEstimate` for the requested :class:`ForecastWindow`, reporting
how deep the replay went (number of historical samples).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from attention.consolidation.salience_history import SalienceHistory
from attention.forecasting.forecast_window import ForecastWindow
from attention.forecasting.trajectory_estimator import TrajectoryEstimate, TrajectoryEstimator


@dataclass
class ReplayTrajectoryResult:
    """Outcome of replaying a target's history for one window."""

    target_id: str
    window: str
    replay_depth: int
    estimates: list[TrajectoryEstimate] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "target_id": self.target_id,
            "window": self.window,
            "replay_depth": self.replay_depth,
            "estimates": [e.to_dict() for e in self.estimates],
        }


class ReplayTrajectoryForecast:
    """Replays history into a bounded trajectory estimate per window."""

    def __init__(
        self,
        history: SalienceHistory,
        estimator: TrajectoryEstimator | None = None,
    ) -> None:
        self.history = history
        self.estimator = estimator or TrajectoryEstimator()

    def forecast(self, target_id: str, window: ForecastWindow) -> ReplayTrajectoryResult:
        series = self.history.series(target_id)
        estimate = self.estimator.estimate(series, horizon_factor=float(window.steps))
        return ReplayTrajectoryResult(
            target_id=target_id,
            window=window.name,
            replay_depth=len(series),
            estimates=[estimate],
        )
