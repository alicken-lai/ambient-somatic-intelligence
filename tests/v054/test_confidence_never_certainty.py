"""Area 9: invariant — confidence never reaches 1.0."""

from attention.calibration.confidence_cap import ABSOLUTE_MAX_CONFIDENCE, ConfidenceCap, apply_confidence_cap
from attention.calibration.forecast_confidence import ForecastConfidenceCalibrator


def test_cap_violates_at_one() -> None:
    cap = ConfidenceCap()
    assert cap.violates_absolute(1.0) is True


def test_calibrator_extreme_inputs() -> None:
    cal = ForecastConfidenceCalibrator()
    for raw in (1.0, 0.999, 0.99, 0.98):
        result = cal.calibrate(raw, band_width=0.05)
        assert result.calibrated < 1.0
        assert result.calibrated <= ABSOLUTE_MAX_CONFIDENCE


def test_apply_cap_extreme() -> None:
    for v in (1.0, 1.5, 0.9999):
        assert apply_confidence_cap(v) < 1.0
