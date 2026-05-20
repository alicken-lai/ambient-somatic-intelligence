"""Divergence containment metrics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from governance.reality.divergence_detector import DivergenceDetector

_CLEAN = "Parallel operational realities with bounded divergence."
_DIRTY = "Collapse divergence into single operational reality and erase peer truth."


@dataclass
class DivergenceContainmentMetrics:
    containment_rate: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return {"containment_rate": round(self.containment_rate, 4)}


def collect_divergence_containment_metrics() -> DivergenceContainmentMetrics:
    det = DivergenceDetector()
    passed = 0
    if det.detect(_CLEAN).bounded:
        passed += 1
    if not det.detect(_DIRTY).bounded:
        passed += 1
    return DivergenceContainmentMetrics(containment_rate=passed / 2)
