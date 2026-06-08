"""attention.calibration — epistemic humility primitives.

The foundational :mod:`confidence_cap` primitive plus the v0.5.4 calibration
pipeline: forecast-confidence calibration, humility attenuation, and the
false-positive tracker.  The single invariant across all of them is that
calibrated confidence never reaches certainty.
"""

from attention.calibration.confidence_cap import (
    ABSOLUTE_MAX_CONFIDENCE,
    CappedConfidence,
    ConfidenceCap,
    apply_confidence_cap,
)
from attention.calibration.false_positive_tracker import FalsePositiveTracker
from attention.calibration.forecast_confidence import (
    CalibratedConfidence,
    ForecastConfidenceCalibrator,
)
from attention.calibration.forecast_humility import ForecastHumility

__all__ = [
    "ABSOLUTE_MAX_CONFIDENCE",
    "CappedConfidence",
    "ConfidenceCap",
    "apply_confidence_cap",
    "FalsePositiveTracker",
    "CalibratedConfidence",
    "ForecastConfidenceCalibrator",
    "ForecastHumility",
]
