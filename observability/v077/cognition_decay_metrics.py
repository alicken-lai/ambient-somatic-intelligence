"""Cognition decay metrics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from governance.agency.cognition_decay_governor import CognitionDecayGovernor


@dataclass
class CognitionDecayMetrics:
    decay_rate: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return {"decay_rate": round(self.decay_rate, 4)}


def collect_cognition_decay_metrics() -> CognitionDecayMetrics:
    g = CognitionDecayGovernor()
    fresh = g.govern(stale_hours=0.0)
    stale = g.govern(stale_hours=336.0)
    passed = 0
    if not fresh.decay_applied and fresh.decay_factor == 1.0:
        passed += 1
    if stale.decay_applied and stale.decay_factor < 1.0:
        passed += 1
    return CognitionDecayMetrics(decay_rate=passed / 2)
