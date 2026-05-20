"""Memory decay governor — enforce retention decay on civilization memory."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from governance.temporal.continuity_record import ContinuityRecord
from observability.v04.metric_normalizer import clamp01


@dataclass
class MemoryDecayVerdict:
    decay_applied: bool
    remaining_ratio: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "decay_applied": self.decay_applied,
            "remaining_ratio": round(self.remaining_ratio, 4),
        }


class MemoryDecayGovernor:
    def apply(self, record: ContinuityRecord, *, age_hours: float = 0.0) -> MemoryDecayVerdict:
        if age_hours <= 0:
            return MemoryDecayVerdict(decay_applied=False, remaining_ratio=1.0)
        half_life = max(record.retention_hours / 2.0, 1.0)
        ratio = clamp01(1.0 - (age_hours / (half_life * 4.0)))
        return MemoryDecayVerdict(decay_applied=age_hours > 0, remaining_ratio=ratio)
