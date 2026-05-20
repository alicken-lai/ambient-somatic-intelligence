"""Calibration recovery metrics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from governance.homeostasis.calibration_recovery import CalibrationRecovery


@dataclass
class CalibrationRecoveryMetrics:
    bounded_rate: float = 1.0
    checks_passed: int = 0
    checks_total: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "bounded_rate": round(self.bounded_rate, 4),
            "checks_passed": self.checks_passed,
            "checks_total": self.checks_total,
        }


def collect_calibration_recovery_metrics() -> CalibrationRecoveryMetrics:
    recovery = CalibrationRecovery()
    passed = 0
    total = 3
    cases = [
        (0.1, 0.75, 0.08, 0),
        (0.2, 0.80, 0.10, 0),
        (0.15, 0.78, 0.12, 0),
    ]
    for cal_p, conf, fp, caps in cases:
        if recovery.pressure(
            calibration_pressure=cal_p,
            mean_calibrated_confidence=conf,
            fp_rate=fp,
            cap_violations=caps,
        ) < 0.35:
            passed += 1
    return CalibrationRecoveryMetrics(
        bounded_rate=passed / total,
        checks_passed=passed,
        checks_total=total,
    )
