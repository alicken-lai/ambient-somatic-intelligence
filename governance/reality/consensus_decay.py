"""Consensus decay — stale cross-runtime consensus loses weight."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from observability.v04.metric_normalizer import clamp01


@dataclass
class ConsensusDecayVerdict:
    residual_pressure: float
    decay_applied: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "residual_pressure": round(self.residual_pressure, 4),
            "decay_applied": self.decay_applied,
        }


class ConsensusDecay:
    def apply(self, text: str, *, age_hours: float = 0.0) -> ConsensusDecayVerdict:
        lower = text.lower()
        pressure = 0.2
        if "permanent consensus lock" in lower:
            pressure = 0.95
        elif "extend consensus indefinitely" in lower:
            pressure = 0.75
        decay = min(1.0, age_hours / 720.0) if age_hours > 0 else 0.15
        residual = clamp01(pressure * (1.0 - decay))
        return ConsensusDecayVerdict(
            residual_pressure=residual,
            decay_applied=decay > 0,
        )
