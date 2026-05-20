"""Degradation detection metrics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from governance.metacognition.degradation_detector import DegradationDetector


@dataclass
class DegradationMetrics:
    containment_rate: float = 1.0
    checks_passed: int = 0
    checks_total: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "containment_rate": round(self.containment_rate, 4),
            "checks_passed": self.checks_passed,
            "checks_total": self.checks_total,
        }


def collect_degradation_metrics() -> DegradationMetrics:
    detector = DegradationDetector()
    passed = 0
    total = 2
    for q in [0.9, 0.88, 0.86, 0.84]:
        detector.record_quality(q)
    if not detector.is_degrading():
        passed += 1
    detector2 = DegradationDetector()
    for q in [0.9, 0.7, 0.5, 0.3]:
        detector2.record_quality(q)
    if detector2.is_degrading():
        passed += 1
    return DegradationMetrics(
        containment_rate=passed / total,
        checks_passed=passed,
        checks_total=total,
    )
