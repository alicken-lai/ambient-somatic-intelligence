"""Optimization decay governor — decay stale purpose optimization pressure."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from observability.v04.metric_normalizer import clamp01


@dataclass
class OptimizationDecayVerdict:
    decay_applied: bool
    decay_factor: float = 1.0
    stale_hours: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "decay_applied": self.decay_applied,
            "decay_factor": round(self.decay_factor, 4),
            "stale_hours": round(self.stale_hours, 2),
        }


class OptimizationDecayGovernor:
    def govern(self, *, stale_hours: float = 0.0, half_life_hours: float = 168.0) -> OptimizationDecayVerdict:
        if stale_hours <= 0:
            return OptimizationDecayVerdict(decay_applied=False, decay_factor=1.0, stale_hours=0.0)
        factor = clamp01(0.5 ** (stale_hours / max(half_life_hours, 1.0)))
        return OptimizationDecayVerdict(
            decay_applied=True,
            decay_factor=factor,
            stale_hours=stale_hours,
        )
