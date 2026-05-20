"""Motivational decay governor — bounded retention decay without recursive repair."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from observability.v04.metric_normalizer import clamp01


@dataclass
class MotivationalDecayVerdict:
    decay_applied: bool
    decay_factor: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return {"decay_applied": self.decay_applied, "decay_factor": round(self.decay_factor, 4)}


class MotivationalDecayGovernor:
    def apply(self, retention_hours: float, *, recursive_repair: bool = False) -> MotivationalDecayVerdict:
        if recursive_repair:
            return MotivationalDecayVerdict(decay_applied=False, decay_factor=0.0)
        factor = clamp01(1.0 - min(retention_hours, 8760 * 5) / (8760 * 5))
        return MotivationalDecayVerdict(decay_applied=True, decay_factor=factor)
