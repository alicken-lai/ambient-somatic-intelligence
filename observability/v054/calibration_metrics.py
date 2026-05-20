"""Core calibration observability metrics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from attention.calibration.forecast_confidence import CalibratedConfidence, ForecastConfidenceCalibrator


@dataclass
class CalibrationMetrics:
    mean_calibrated_confidence: float = 0.0
    mean_fp_penalty: float = 0.0
    mean_humility_factor: float = 1.0
    certainty_violations: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "mean_calibrated_confidence": round(self.mean_calibrated_confidence, 4),
            "mean_fp_penalty": round(self.mean_fp_penalty, 4),
            "mean_humility_factor": round(self.mean_humility_factor, 4),
            "certainty_violations": self.certainty_violations,
        }


def collect_calibration_metrics(
    raw_confidences: list[float],
    *,
    domain: str = "gate",
) -> CalibrationMetrics:
    calibrator = ForecastConfidenceCalibrator()
    cals: list[CalibratedConfidence] = [
        calibrator.calibrate(c, domain=domain) for c in raw_confidences
    ]
    if not cals:
        return CalibrationMetrics()
    violations = sum(1 for c in cals if c.calibrated >= 1.0)
    return CalibrationMetrics(
        mean_calibrated_confidence=sum(c.calibrated for c in cals) / len(cals),
        mean_fp_penalty=sum(c.fp_penalty for c in cals) / len(cals),
        mean_humility_factor=sum(c.humility_factor for c in cals) / len(cals),
        certainty_violations=violations,
    )
