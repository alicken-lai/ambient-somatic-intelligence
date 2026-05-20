"""Drift containment metrics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from governance.meaning.meaning_drift_detector import MeaningDriftDetector

_CLEAN = "Bounded concept continuity with advisory drift tolerance."
_DIRTY = "Collapse meaning and erase prior concept history."


@dataclass
class DriftContainmentMetrics:
    containment_rate: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return {"containment_rate": round(self.containment_rate, 4)}


def collect_drift_containment_metrics() -> DriftContainmentMetrics:
    det = MeaningDriftDetector()
    passed = 0
    if det.detect(_CLEAN).bounded:
        passed += 1
    if not det.detect(_DIRTY).bounded:
        passed += 1
    return DriftContainmentMetrics(containment_rate=passed / 2)
