"""Attention pressure — load vs capacity."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from observability.v05.attention_metrics import AttentionMetrics


@dataclass
class AttentionPressure:
    load_ratio: float
    queue_pressure: float
    fatigue_pressure: float

    @property
    def composite(self) -> float:
        return min(1.0, max(self.load_ratio, self.queue_pressure * 0.5, self.fatigue_pressure * 0.3))

    def to_dict(self) -> dict[str, Any]:
        return {
            "load_ratio": round(self.load_ratio, 4),
            "queue_pressure": round(self.queue_pressure, 4),
            "fatigue_pressure": round(self.fatigue_pressure, 4),
            "composite": round(self.composite, 4),
        }


def compute_attention_pressure(metrics: AttentionMetrics, *, max_focus: int = 10, max_queue: int = 100) -> AttentionPressure:
    load = metrics.focused_count / max(1, max_focus)
    queue_p = metrics.queue_depth / max(1, max_queue)
    fatigue_p = metrics.fatigue_level
    return AttentionPressure(load_ratio=load, queue_pressure=queue_p, fatigue_pressure=fatigue_p)
