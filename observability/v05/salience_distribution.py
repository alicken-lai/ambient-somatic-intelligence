"""Salience distribution statistics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from attention.core.salience import SalienceVector


@dataclass
class SalienceDistribution:
    count: int
    mean: float
    min: float
    max: float
    p90: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "count": self.count,
            "mean": round(self.mean, 4),
            "min": round(self.min, 4),
            "max": round(self.max, 4),
            "p90": round(self.p90, 4),
        }


def compute_distribution(vectors: list[SalienceVector]) -> SalienceDistribution:
    if not vectors:
        return SalienceDistribution(0, 0.0, 0.0, 0.0, 0.0)
    totals = sorted(v.total for v in vectors)
    n = len(totals)
    p90_idx = min(n - 1, int(n * 0.9))
    return SalienceDistribution(
        count=n,
        mean=sum(totals) / n,
        min=totals[0],
        max=totals[-1],
        p90=totals[p90_idx],
    )
