"""Degradation detector — declining quality / rising pathology pressure."""

from __future__ import annotations

from observability.v04.metric_normalizer import clamp01


class DegradationDetector:
    DEGRADATION_WINDOW = 12

    def __init__(self) -> None:
        self._history: list[float] = []

    def record_quality(self, quality_score: float) -> None:
        self._history.append(clamp01(quality_score))
        if len(self._history) > self.DEGRADATION_WINDOW:
            self._history = self._history[-self.DEGRADATION_WINDOW:]

    def pressure(self) -> float:
        if len(self._history) < 3:
            return 0.0
        recent = self._history[-3:]
        older = self._history[:-3] if len(self._history) > 3 else self._history[:1]
        recent_mean = sum(recent) / len(recent)
        older_mean = sum(older) / len(older) if older else recent_mean
        drop = older_mean - recent_mean
        if drop <= 0.05:
            return 0.0
        return clamp01(drop * 2.0)

    def is_degrading(self) -> bool:
        return self.pressure() >= 0.35
