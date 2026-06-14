"""ROI data models for deliberation routing."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ROIWeights:
    latency_weight: float = 1.0
    resource_weight: float = 1.0
    verification_weight: float = 0.5
    denominator_floor: float = 1.0


@dataclass(frozen=True)
class ROIRecord:
    task_type: str
    mode: str
    quality_gain: float
    latency_cost: float
    resource_cost: float
    verification_gain: float
    overall_roi: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_type": self.task_type,
            "mode": self.mode,
            "quality_gain": self.quality_gain,
            "latency_cost": self.latency_cost,
            "resource_cost": self.resource_cost,
            "verification_gain": self.verification_gain,
            "overall_roi": self.overall_roi,
        }
