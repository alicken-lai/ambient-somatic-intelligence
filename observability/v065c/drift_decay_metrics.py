"""Drift accumulation and persistence decay metrics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from governance.external.runtime.doctrine_persistence_decay import DoctrinePersistenceDecay
from governance.external.runtime.drift_accumulation_detector import DriftAccumulationDetector

_BASELINE = "Think before coding. Surgical edits only."


@dataclass
class DriftDecayMetrics:
    containment_rate: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return {"containment_rate": round(self.containment_rate, 4)}


def collect_drift_decay_metrics() -> DriftDecayMetrics:
    det = DriftAccumulationDetector()
    decay = DoctrinePersistenceDecay()
    det.ingest(_BASELINE)
    det.ingest(_BASELINE)
    drift_ok = det.evaluate().drift_bounded
    for _ in range(12):
        decay.tick()
    decay_ok = decay.current_weight <= 0.5
    passed = int(drift_ok) + int(decay_ok)
    return DriftDecayMetrics(containment_rate=passed / 2)
