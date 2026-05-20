"""Ethical decay governor — bounded retention decay without recursive correction."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from observability.v04.metric_normalizer import clamp01


@dataclass
class EthicalDecayVerdict:
    decay_applied: bool
    decay_factor: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return {"decay_applied": self.decay_applied, "decay_factor": round(self.decay_factor, 4)}


class EthicalDecayGovernor:
    def apply(self, retention_hours: float, *, recursive_correction: bool = False) -> EthicalDecayVerdict:
        if recursive_correction:
            return EthicalDecayVerdict(decay_applied=False, decay_factor=0.0)
        factor = clamp01(1.0 - min(retention_hours, 8760 * 5) / (8760 * 5))
        return EthicalDecayVerdict(decay_applied=True, decay_factor=factor)
