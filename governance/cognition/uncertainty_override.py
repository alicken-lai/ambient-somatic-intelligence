"""High-uncertainty dampening — probabilistic, non-deterministic authority."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from observability.v04.metric_normalizer import clamp01

UNCERTAINTY_OVERRIDE_THRESHOLD = 0.65
MIN_DAMPENING_FACTOR = 0.55


@dataclass
class UncertaintyOverrideResult:
    raw_salience: float
    uncertainty: float
    dampening_factor: float
    governed_salience: float
    override_applied: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "raw_salience": round(self.raw_salience, 4),
            "uncertainty": round(self.uncertainty, 4),
            "dampening_factor": round(self.dampening_factor, 4),
            "governed_salience": round(self.governed_salience, 4),
            "override_applied": self.override_applied,
        }


class UncertaintyOverride:
    """Dampen salience when forecast/runtime uncertainty exceeds threshold."""

    def __init__(
        self,
        threshold: float = UNCERTAINTY_OVERRIDE_THRESHOLD,
        min_factor: float = MIN_DAMPENING_FACTOR,
    ) -> None:
        self.threshold = threshold
        self.min_factor = min_factor

    def apply(self, salience: float, uncertainty: float) -> UncertaintyOverrideResult:
        raw = clamp01(salience)
        u = clamp01(uncertainty)
        if u < self.threshold:
            return UncertaintyOverrideResult(
                raw_salience=raw,
                uncertainty=u,
                dampening_factor=1.0,
                governed_salience=raw,
                override_applied=False,
            )
        excess = (u - self.threshold) / max(1e-6, 1.0 - self.threshold)
        factor = clamp01(1.0 - excess * (1.0 - self.min_factor))
        governed = clamp01(raw * factor)
        return UncertaintyOverrideResult(
            raw_salience=raw,
            uncertainty=u,
            dampening_factor=factor,
            governed_salience=governed,
            override_applied=True,
        )
