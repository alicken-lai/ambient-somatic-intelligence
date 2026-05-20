"""Confidence cap enforcement metrics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from attention.calibration.confidence_cap import ABSOLUTE_MAX_CONFIDENCE, ConfidenceCap


@dataclass
class ConfidenceCapMetrics:
    absolute_max: float = ABSOLUTE_MAX_CONFIDENCE
    violations: int = 0
    capped_samples: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "absolute_max": round(self.absolute_max, 4),
            "violations": self.violations,
            "capped_samples": self.capped_samples,
        }


def collect_confidence_cap_metrics(
    cap: ConfidenceCap,
    values: list[float],
    *,
    domain: str = "default",
) -> ConfidenceCapMetrics:
    violations = sum(1 for v in values if cap.violates_absolute(v))
    capped = sum(1 for v in values if cap.apply(v, domain) < v)
    return ConfidenceCapMetrics(
        absolute_max=ABSOLUTE_MAX_CONFIDENCE,
        violations=violations,
        capped_samples=capped,
    )
