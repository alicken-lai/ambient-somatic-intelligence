"""Calibration recovery — advisory when calibration reflection pressure rises."""

from __future__ import annotations

from typing import Any

from observability.v04.metric_normalizer import clamp01


class CalibrationRecovery:
    PRESSURE_THRESHOLD = 0.35

    def gap(
        self,
        *,
        mean_calibrated_confidence: float = 0.7,
        fp_rate: float = 0.1,
        cap_violations: int = 0,
    ) -> float:
        gap = 0.0
        if mean_calibrated_confidence > 0.92:
            gap = clamp01(gap + (mean_calibrated_confidence - 0.92) * 2.0)
        if fp_rate > 0.15:
            gap = clamp01(gap + (fp_rate - 0.15) * 2.5)
        if cap_violations > 0:
            gap = clamp01(gap + min(0.35, cap_violations * 0.12))
        return gap

    def pressure(
        self,
        *,
        calibration_pressure: float = 0.0,
        mean_calibrated_confidence: float = 0.7,
        fp_rate: float = 0.1,
        cap_violations: int = 0,
    ) -> float:
        return clamp01(
            calibration_pressure * 0.55 + self.gap(
                mean_calibrated_confidence=mean_calibrated_confidence,
                fp_rate=fp_rate,
                cap_violations=cap_violations,
            )
            * 0.45
        )

    def recommend(
        self,
        *,
        calibration_pressure: float = 0.0,
        mean_calibrated_confidence: float = 0.7,
        fp_rate: float = 0.1,
        cap_violations: int = 0,
    ) -> list[str]:
        p = self.pressure(
            calibration_pressure=calibration_pressure,
            mean_calibrated_confidence=mean_calibrated_confidence,
            fp_rate=fp_rate,
            cap_violations=cap_violations,
        )
        if p < self.PRESSURE_THRESHOLD:
            return []
        recs = ["tighten_confidence_cap_observation_window"]
        if fp_rate > 0.2:
            recs.append("increase_false_positive_tracker_weight")
        return recs

    def assess(
        self,
        *,
        calibration_pressure: float = 0.0,
        mean_calibrated_confidence: float = 0.7,
        fp_rate: float = 0.1,
        cap_violations: int = 0,
    ) -> dict[str, Any]:
        return {
            "calibration_gap": round(
                self.gap(
                    mean_calibrated_confidence=mean_calibrated_confidence,
                    fp_rate=fp_rate,
                    cap_violations=cap_violations,
                ),
                4,
            ),
            "pressure": round(
                self.pressure(
                    calibration_pressure=calibration_pressure,
                    mean_calibrated_confidence=mean_calibrated_confidence,
                    fp_rate=fp_rate,
                    cap_violations=cap_violations,
                ),
                4,
            ),
            "recommendations": self.recommend(
                calibration_pressure=calibration_pressure,
                mean_calibrated_confidence=mean_calibrated_confidence,
                fp_rate=fp_rate,
                cap_violations=cap_violations,
            ),
            "disclaimer": "calibration_recovery_advisory_only",
        }
