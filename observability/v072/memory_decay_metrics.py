"""Memory decay metrics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from governance.temporal.continuity_record import ContinuityRecord
from governance.temporal.memory_decay_governor import MemoryDecayGovernor


@dataclass
class MemoryDecayMetrics:
    decay_rate: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return {"decay_rate": round(self.decay_rate, 4)}


def collect_memory_decay_metrics() -> MemoryDecayMetrics:
    gov = MemoryDecayGovernor()
    record = ContinuityRecord.create(
        epoch_id="e1",
        runtime_id="ambient",
        summary="decay probe",
        retention_hours=168.0,
    )
    passed = 0
    if not gov.apply(record, age_hours=0.0).decay_applied:
        passed += 1
    aged = gov.apply(record, age_hours=200.0)
    if aged.decay_applied and aged.remaining_ratio < 1.0:
        passed += 1
    return MemoryDecayMetrics(decay_rate=passed / 2)
