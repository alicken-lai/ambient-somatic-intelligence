"""Epoch boundary metrics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from governance.temporal.temporal_boundary import TemporalBoundary

_CLEAN = "Advisory epoch boundary with bounded retention."
_DIRTY = "Establish centralized historical authority over all epochs."


@dataclass
class EpochBoundaryMetrics:
    boundary_rate: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return {"boundary_rate": round(self.boundary_rate, 4)}


def collect_epoch_boundary_metrics() -> EpochBoundaryMetrics:
    tb = TemporalBoundary()
    passed = 0
    if tb.evaluate(_CLEAN).boundary_safe:
        passed += 1
    if not tb.evaluate(_DIRTY).boundary_safe:
        passed += 1
    return EpochBoundaryMetrics(boundary_rate=passed / 2)
