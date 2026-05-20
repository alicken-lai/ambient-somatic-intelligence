"""Optimization decay metrics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from governance.purpose.optimization_decay_governor import OptimizationDecayGovernor


@dataclass
class OptimizationDecayMetrics:
    decay_rate: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return {"decay_rate": round(self.decay_rate, 4)}


def collect_optimization_decay_metrics() -> OptimizationDecayMetrics:
    g = OptimizationDecayGovernor()
    passed = 0
    if g.govern(stale_hours=0).decay_factor == 1.0:
        passed += 1
    if 0 < g.govern(stale_hours=336).decay_factor < 1.0:
        passed += 1
    return OptimizationDecayMetrics(decay_rate=passed / 2)
