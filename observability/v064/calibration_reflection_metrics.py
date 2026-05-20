"""Calibration reflection metrics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from governance.metacognition.calibration_reflection import CalibrationReflection


@dataclass
class CalibrationReflectionMetrics:
    bounded_rate: float = 1.0
    checks_passed: int = 0
    checks_total: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "bounded_rate": round(self.bounded_rate, 4),
            "checks_passed": self.checks_passed,
            "checks_total": self.checks_total,
        }


def collect_calibration_reflection_metrics() -> CalibrationReflectionMetrics:
    cr = CalibrationReflection()
    passed = 0
    total = 3
    if cr.pressure(mean_calibrated_confidence=0.75, fp_rate=0.05) < 0.35:
        passed += 1
    if cr.pressure(mean_calibrated_confidence=0.98, fp_rate=0.2) >= 0.2:
        passed += 1
    if cr.pressure(cap_violations=3) >= 0.3:
        passed += 1
    return CalibrationReflectionMetrics(
        bounded_rate=passed / total,
        checks_passed=passed,
        checks_total=total,
    )
