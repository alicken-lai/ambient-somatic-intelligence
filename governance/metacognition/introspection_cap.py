"""Introspection cap — depth-limited meta-assessment per window."""

from __future__ import annotations

from observability.v04.metric_normalizer import clamp01


class IntrospectionCap:
    MAX_DEPTH = 2
    MAX_EVALUATIONS_PER_WINDOW = 120

    def __init__(self) -> None:
        self._depth = 0
        self._evaluations = 0

    def reset_window(self) -> None:
        self._evaluations = 0

    def enter(self) -> bool:
        if self._depth >= self.MAX_DEPTH:
            return False
        if self._evaluations >= self.MAX_EVALUATIONS_PER_WINDOW:
            return False
        self._depth += 1
        self._evaluations += 1
        return True

    def exit(self) -> None:
        self._depth = max(0, self._depth - 1)

    def pressure(self) -> float:
        depth_ratio = self._depth / max(1, self.MAX_DEPTH)
        eval_ratio = self._evaluations / max(1, self.MAX_EVALUATIONS_PER_WINDOW)
        return clamp01(max(depth_ratio * 0.5, eval_ratio * 0.4))

    @property
    def capped(self) -> bool:
        return self._depth >= self.MAX_DEPTH or self._evaluations >= self.MAX_EVALUATIONS_PER_WINDOW
