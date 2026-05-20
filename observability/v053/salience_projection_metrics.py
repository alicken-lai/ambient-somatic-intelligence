"""Salience projection observability."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from attention.forecasting.salience_projection import SalienceProjection, SalienceProjectionPoint


@dataclass
class SalienceProjectionMetrics:
    step_count: int = 0
    peak_projected: float = 0.0
    mean_band_width: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "step_count": self.step_count,
            "peak_projected": round(self.peak_projected, 4),
            "mean_band_width": round(self.mean_band_width, 4),
        }


def collect_salience_projection_metrics(
    projection: SalienceProjection,
    target_id: str,
    *,
    steps: int = 8,
) -> SalienceProjectionMetrics:
    points: list[SalienceProjectionPoint] = projection.project(target_id, steps=steps)
    if not points:
        return SalienceProjectionMetrics()
    widths = [p.band.width() for p in points]
    return SalienceProjectionMetrics(
        step_count=len(points),
        peak_projected=max(p.projected_salience for p in points),
        mean_band_width=sum(widths) / len(widths),
    )
