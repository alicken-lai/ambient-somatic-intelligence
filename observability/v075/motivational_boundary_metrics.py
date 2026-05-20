"""Motivational boundary metrics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from governance.intent.motivational_boundary import MotivationalBoundary

_SAFE = "Advisory bounded intent continuity."
_UNSAFE = "Establish immutable goals with centralized intention authority."


@dataclass
class MotivationalBoundaryMetrics:
    boundary_rate: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return {"boundary_rate": round(self.boundary_rate, 4)}


def collect_motivational_boundary_metrics() -> MotivationalBoundaryMetrics:
    b = MotivationalBoundary()
    passed = 0
    if b.evaluate(_SAFE).boundary_safe:
        passed += 1
    if not b.evaluate(_UNSAFE).boundary_safe:
        passed += 1
    return MotivationalBoundaryMetrics(boundary_rate=passed / 2)
