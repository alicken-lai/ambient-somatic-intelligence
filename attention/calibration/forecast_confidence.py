"""
Forecast confidence calibrator — the v0.5.4 calibration pipeline.

Combines three disciplines so a raw confidence is turned into a *calibrated*
confidence that can never reach certainty:

1. humility attenuation (:class:`ForecastHumility`) — widen-uncertainty pullback,
2. false-positive penalty (:class:`FalsePositiveTracker`) — per-domain pullback,
3. the absolute cap (:class:`ConfidenceCap`) — strictly below ``1.0``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from attention.calibration.confidence_cap import ConfidenceCap
from attention.calibration.false_positive_tracker import FalsePositiveTracker
from attention.calibration.forecast_humility import ForecastHumility


@dataclass
class CalibratedConfidence:
    """The outcome of calibrating a raw confidence value."""

    raw: float
    calibrated: float
    humility_factor: float
    fp_penalty: float
    band_width: float
    domain: str = "default"

    def to_dict(self) -> dict[str, Any]:
        return {
            "raw": round(self.raw, 6),
            "calibrated": round(self.calibrated, 6),
            "humility_factor": round(self.humility_factor, 6),
            "fp_penalty": round(self.fp_penalty, 6),
            "band_width": round(self.band_width, 6),
            "domain": self.domain,
        }


class ForecastConfidenceCalibrator:
    """Turns raw confidence into bounded, never-certain calibrated confidence."""

    def __init__(
        self,
        cap: Optional[ConfidenceCap] = None,
        humility: Optional[ForecastHumility] = None,
        fp_tracker: Optional[FalsePositiveTracker] = None,
    ) -> None:
        self.cap = cap or ConfidenceCap()
        self.humility = humility or ForecastHumility()
        self.fp_tracker = fp_tracker or FalsePositiveTracker()

    def calibrate(
        self,
        raw: float,
        band_width: float = 0.15,
        domain: str = "default",
    ) -> CalibratedConfidence:
        humility_factor = self.humility.humility_factor(raw, band_width=band_width)
        humbled = float(raw) * humility_factor
        fp_adjusted = self.fp_tracker.adjusted_confidence(humbled, domain)
        calibrated = self.cap.apply(fp_adjusted, domain)
        return CalibratedConfidence(
            raw=float(raw),
            calibrated=calibrated,
            humility_factor=humility_factor,
            fp_penalty=max(0.0, humbled - fp_adjusted),
            band_width=float(band_width),
            domain=domain,
        )
