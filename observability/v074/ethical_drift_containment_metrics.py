"""Ethical drift containment metrics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from governance.value.ethical_drift_detector import EthicalDriftDetector

_CLEAN = "Bounded normative continuity with advisory ethical drift tolerance."
_DIRTY = "Collapse normative and erase prior value history."


@dataclass
class EthicalDriftContainmentMetrics:
    containment_rate: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return {"containment_rate": round(self.containment_rate, 4)}


def collect_ethical_drift_containment_metrics() -> EthicalDriftContainmentMetrics:
    det = EthicalDriftDetector()
    passed = 0
    if det.detect(_CLEAN).bounded:
        passed += 1
    if not det.detect(_DIRTY).bounded:
        passed += 1
    return EthicalDriftContainmentMetrics(containment_rate=passed / 2)
