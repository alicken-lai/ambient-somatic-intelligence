"""Uncertainty override observability."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from governance.cognition.uncertainty_override import UncertaintyOverride


@dataclass
class UncertaintyOverrideMetrics:
    override_rate: float = 0.0
    mean_dampening_factor: float = 1.0
    high_uncertainty_samples: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "override_rate": round(self.override_rate, 4),
            "mean_dampening_factor": round(self.mean_dampening_factor, 4),
            "high_uncertainty_samples": self.high_uncertainty_samples,
        }


def collect_uncertainty_override_metrics(
    salience_uncertainty_pairs: list[tuple[float, float]],
) -> UncertaintyOverrideMetrics:
    override = UncertaintyOverride()
    applied = 0
    factors: list[float] = []
    high = 0
    for sal, unc in salience_uncertainty_pairs:
        r = override.apply(sal, unc)
        if r.override_applied:
            applied += 1
        if unc >= override.threshold:
            high += 1
        factors.append(r.dampening_factor)
    n = max(1, len(salience_uncertainty_pairs))
    return UncertaintyOverrideMetrics(
        override_rate=applied / n,
        mean_dampening_factor=sum(factors) / max(1, len(factors)) if factors else 1.0,
        high_uncertainty_samples=high,
    )
