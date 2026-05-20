"""False-positive tracker observability."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from attention.calibration.false_positive_tracker import FalsePositiveTracker


@dataclass
class FalsePositiveMetrics:
    record_count: int = 0
    global_fp_rate: float = 0.0
    mean_penalty: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "record_count": self.record_count,
            "global_fp_rate": round(self.global_fp_rate, 4),
            "mean_penalty": round(self.mean_penalty, 4),
        }


def collect_false_positive_metrics(tracker: FalsePositiveTracker) -> FalsePositiveMetrics:
    return FalsePositiveMetrics(
        record_count=len(tracker._records),
        global_fp_rate=tracker.fp_rate(),
        mean_penalty=tracker.confidence_penalty(),
    )
