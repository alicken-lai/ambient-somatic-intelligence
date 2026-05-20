"""Area 1: calibration core — cap, forecast confidence, humility."""

from attention.calibration.confidence_cap import ABSOLUTE_MAX_CONFIDENCE, apply_confidence_cap
from attention.calibration.forecast_confidence import ForecastConfidenceCalibrator
from attention.calibration.forecast_humility import ForecastHumility


def test_absolute_max_below_certainty() -> None:
    assert ABSOLUTE_MAX_CONFIDENCE < 1.0


def test_apply_cap_never_one() -> None:
    assert apply_confidence_cap(1.0) <= ABSOLUTE_MAX_CONFIDENCE
    assert apply_confidence_cap(0.995) <= ABSOLUTE_MAX_CONFIDENCE


def test_calibrator_high_raw_stays_capped() -> None:
    cal = ForecastConfidenceCalibrator()
    result = cal.calibrate(0.98, band_width=0.1)
    assert result.calibrated <= ABSOLUTE_MAX_CONFIDENCE
    assert result.calibrated < 1.0


def test_humility_reduces_high_confidence() -> None:
    h = ForecastHumility()
    humble = h.humble_confidence(0.95, band_width=0.3)
    assert humble < 0.95
