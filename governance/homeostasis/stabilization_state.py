"""Stabilization state — bounded homeostatic pressure tracking."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from observability.v04.metric_normalizer import clamp01


@dataclass
class StabilizationState:
    """Observational stabilization snapshot — no execution authority."""

    level: float = 1.0
    attention_pressure: float = 0.0
    salience_variance: float = 0.0
    coherence_gap: float = 0.0
    reflection_load: float = 0.0
    calibration_gap: float = 0.0
    uncertainty_skew: float = 0.0
    trace: list[str] = field(default_factory=list)

    def composite_pressure(self) -> float:
        return clamp01(
            self.attention_pressure * 0.22
            + self.salience_variance * 0.18
            + self.coherence_gap * 0.20
            + self.reflection_load * 0.15
            + self.calibration_gap * 0.15
            + self.uncertainty_skew * 0.10
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "level": round(self.level, 4),
            "attention_pressure": round(self.attention_pressure, 4),
            "salience_variance": round(self.salience_variance, 4),
            "coherence_gap": round(self.coherence_gap, 4),
            "reflection_load": round(self.reflection_load, 4),
            "calibration_gap": round(self.calibration_gap, 4),
            "uncertainty_skew": round(self.uncertainty_skew, 4),
            "composite_pressure": round(self.composite_pressure(), 4),
            "trace": list(self.trace),
            "disclaimer": "stabilization_observational_only",
        }


class StabilizationStateTracker:
    HISTORY_WINDOW = 16

    def __init__(self) -> None:
        self._levels: list[float] = []
        self._current = StabilizationState()

    def update(self, state: StabilizationState) -> StabilizationState:
        pressure = state.composite_pressure()
        level = clamp01(1.0 - pressure * 0.4)
        state.level = level
        self._current = state
        self._levels.append(level)
        if len(self._levels) > self.HISTORY_WINDOW:
            self._levels = self._levels[-self.HISTORY_WINDOW :]
        return state

    @property
    def current(self) -> StabilizationState:
        return self._current

    def trend_pressure(self) -> float:
        if len(self._levels) < 3:
            return 0.0
        recent = sum(self._levels[-3:]) / 3
        older = sum(self._levels[:-3]) / max(1, len(self._levels) - 3)
        drop = older - recent
        if drop <= 0.04:
            return 0.0
        return clamp01(drop * 2.5)
