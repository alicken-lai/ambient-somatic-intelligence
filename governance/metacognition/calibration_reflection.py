"""Calibration reflection — meta-view on confidence calibration posture."""

from __future__ import annotations

from observability.v04.metric_normalizer import clamp01


class CalibrationReflection:
    def pressure(
        self,
        *,
        mean_calibrated_confidence: float = 0.7,
        fp_rate: float = 0.1,
        cap_violations: int = 0,
        certainty_never_reached: bool = True,
    ) -> float:
        overconfidence = 0.25 if mean_calibrated_confidence > 0.95 else 0.0
        fp_penalty = clamp01(fp_rate * 1.5)
        cap_penalty = clamp01(cap_violations * 0.2)
        certainty_bonus = 0.0 if certainty_never_reached else 0.15
        return clamp01(overconfidence + fp_penalty + cap_penalty + certainty_bonus)

    def reflect(
        self,
        *,
        mean_calibrated_confidence: float = 0.7,
        fp_rate: float = 0.1,
        cap_violations: int = 0,
        certainty_never_reached: bool = True,
    ) -> dict[str, Any]:
        p = self.pressure(
            mean_calibrated_confidence=mean_calibrated_confidence,
            fp_rate=fp_rate,
            cap_violations=cap_violations,
            certainty_never_reached=certainty_never_reached,
        )
        return {
            "calibration_pressure": round(p, 4),
            "mean_calibrated_confidence": round(mean_calibrated_confidence, 4),
            "fp_rate": round(fp_rate, 4),
            "cap_violations": cap_violations,
            "disclaimer": "calibration_reflection_advisory",
        }
