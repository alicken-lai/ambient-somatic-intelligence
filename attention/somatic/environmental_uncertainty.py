"""
Environmental uncertainty — quantifies how unsettled the ambient context is.

Reports a mean spread (dispersion) of environmental readings.  With fewer
samples the spread is wider (more uncertain); the spread shrinks but never
reaches zero, so the system always retains a residual humility floor.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

UNCERTAINTY_FLOOR: float = 0.05


def _clamp_unit(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


@dataclass
class UncertaintyReport:
    """Summary of environmental uncertainty."""

    sample_count: int
    mean_spread: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "sample_count": self.sample_count,
            "mean_spread": round(self.mean_spread, 6),
        }


class EnvironmentalUncertainty:
    """Estimates ambient-context uncertainty as a bounded spread."""

    def __init__(self, base_spread: float = 0.5, floor: float = UNCERTAINTY_FLOOR) -> None:
        self.base_spread = base_spread
        self.floor = floor

    def report(self, count: int = 1, spreads: list[float] | None = None) -> UncertaintyReport:
        n = max(1, int(count))
        if spreads:
            observed = sum(spreads) / len(spreads)
            mean_spread = _clamp_unit(max(self.floor, observed))
        else:
            mean_spread = _clamp_unit(self.floor + self.base_spread / math.sqrt(n))
        return UncertaintyReport(sample_count=n, mean_spread=mean_spread)
