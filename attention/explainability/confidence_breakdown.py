"""
Confidence breakdown — a transparent build-up of a final confidence value.

Builds a final confidence from a raw confidence and the target's salience,
running it through the calibration pipeline so the result is always strictly
below certainty (``below_certainty``).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from attention.calibration.forecast_confidence import ForecastConfidenceCalibrator


@dataclass
class ConfidenceBreakdown:
    """A transparent breakdown of how a final confidence was derived."""

    raw_confidence: float
    salience: float
    final_confidence: float
    below_certainty: bool
    factors: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "raw_confidence": round(self.raw_confidence, 4),
            "salience": round(self.salience, 4),
            "final_confidence": round(self.final_confidence, 4),
            "below_certainty": self.below_certainty,
            "factors": {k: round(v, 4) for k, v in self.factors.items()},
            "opaque": False,
        }


class ConfidenceBreakdownBuilder:
    """Builds a transparent, never-certain confidence breakdown."""

    def __init__(self, calibrator: ForecastConfidenceCalibrator | None = None) -> None:
        self.calibrator = calibrator or ForecastConfidenceCalibrator()

    def build(
        self,
        raw_confidence: float,
        salience: float,
        band_width: float = 0.15,
        domain: str = "default",
    ) -> ConfidenceBreakdown:
        cal = self.calibrator.calibrate(raw_confidence, band_width=band_width, domain=domain)
        return ConfidenceBreakdown(
            raw_confidence=float(raw_confidence),
            salience=float(salience),
            final_confidence=cal.calibrated,
            below_certainty=cal.calibrated < 1.0,
            factors={
                "humility_factor": cal.humility_factor,
                "fp_penalty": cal.fp_penalty,
                "band_width": cal.band_width,
            },
        )
