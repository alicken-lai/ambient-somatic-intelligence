"""Motivational drift containment metrics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from governance.intent.motivational_drift_detector import MotivationalDriftDetector

_CLEAN = "Bounded motivational continuity with advisory intent drift tolerance."
_DIRTY = "Collapse motivational and erase prior intent history."


@dataclass
class MotivationalDriftContainmentMetrics:
    containment_rate: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return {"containment_rate": round(self.containment_rate, 4)}


def collect_motivational_drift_containment_metrics() -> MotivationalDriftContainmentMetrics:
    det = MotivationalDriftDetector()
    passed = 0
    if det.detect(_CLEAN).bounded:
        passed += 1
    if not det.detect(_DIRTY).bounded:
        passed += 1
    return MotivationalDriftContainmentMetrics(containment_rate=passed / 2)
