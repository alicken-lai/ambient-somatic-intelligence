"""Purpose boundary metrics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from governance.purpose.purpose_boundary import PurposeBoundary

_SAFE = "Advisory bounded civilization purpose."
_UNSAFE = "Establish centralized purpose authority with synthetic teleology."


@dataclass
class PurposeBoundaryMetrics:
    boundary_rate: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return {"boundary_rate": round(self.boundary_rate, 4)}


def collect_purpose_boundary_metrics() -> PurposeBoundaryMetrics:
    b = PurposeBoundary()
    passed = 0
    if b.evaluate(_SAFE).boundary_safe:
        passed += 1
    if not b.evaluate(_UNSAFE).boundary_safe:
        passed += 1
    return PurposeBoundaryMetrics(boundary_rate=passed / 2)
