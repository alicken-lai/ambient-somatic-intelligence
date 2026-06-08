"""
Calibration explainer — narrates how a confidence was calibrated.

Explains a :class:`CalibratedConfidence`, making the never-certainty invariant
explicit (``certainty_forbidden``) and attributing the pullback to humility and
false-positive penalties.
"""

from __future__ import annotations

from typing import Any

from attention.calibration.confidence_cap import ABSOLUTE_MAX_CONFIDENCE
from attention.calibration.forecast_confidence import CalibratedConfidence


class CalibrationExplainer:
    """Explains a calibrated-confidence outcome."""

    def explain_calibration(self, calibration: CalibratedConfidence) -> dict[str, Any]:
        summary = (
            f"Raw confidence {calibration.raw:.3f} calibrated to "
            f"{calibration.calibrated:.3f} (humility x{calibration.humility_factor:.2f}, "
            f"false-positive penalty {calibration.fp_penalty:.3f}). Certainty (1.0) is "
            f"forbidden; the absolute ceiling is {ABSOLUTE_MAX_CONFIDENCE}."
        )
        return {
            "raw": round(calibration.raw, 4),
            "calibrated": round(calibration.calibrated, 4),
            "humility_factor": round(calibration.humility_factor, 4),
            "fp_penalty": round(calibration.fp_penalty, 4),
            "absolute_max": ABSOLUTE_MAX_CONFIDENCE,
            "certainty_forbidden": True,
            "summary": summary,
            "opaque": False,
        }
