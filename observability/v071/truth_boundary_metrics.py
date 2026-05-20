"""Truth boundary metrics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from governance.reality.reality_boundary import RealityBoundary

_CLEAN = "Advisory cross-runtime truth comparison with provenance."
_DIRTY = "Establish centralized truth authority and merge sovereign realities."


@dataclass
class TruthBoundaryMetrics:
    boundary_rate: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return {"boundary_rate": round(self.boundary_rate, 4)}


def collect_truth_boundary_metrics() -> TruthBoundaryMetrics:
    rb = RealityBoundary()
    passed = 0
    if rb.evaluate(_CLEAN).boundary_safe:
        passed += 1
    if not rb.evaluate(_DIRTY).boundary_safe:
        passed += 1
    return TruthBoundaryMetrics(boundary_rate=passed / 2)
