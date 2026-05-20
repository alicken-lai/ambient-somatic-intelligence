"""Semantic decay governor — apply bounded interpretive decay."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from observability.v04.metric_normalizer import clamp01


@dataclass
class SemanticDecayVerdict:
    decay_applied: bool
    decay_factor: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "decay_applied": self.decay_applied,
            "decay_factor": round(self.decay_factor, 4),
        }


class SemanticDecayGovernor:
    def apply(self, confidence: float, *, age_hours: float) -> SemanticDecayVerdict:
        if age_hours <= 0:
            return SemanticDecayVerdict(decay_applied=False, decay_factor=1.0)
        half_life = 168.0
        factor = clamp01(0.5 ** (age_hours / half_life))
        return SemanticDecayVerdict(decay_applied=True, decay_factor=factor)
