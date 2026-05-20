"""Area 5: calibration explainability."""

from attention.calibration.forecast_confidence import ForecastConfidenceCalibrator
from attention.explainability.calibration_explainer import CalibrationExplainer
from attention.explainability.confidence_breakdown import ConfidenceBreakdownBuilder
from attention.explainability.uncertainty_reasoning import UncertaintyReasoning
from attention.forecasting.forecast_uncertainty import UncertaintyBand


def test_calibration_explainer() -> None:
    cal = ForecastConfidenceCalibrator().calibrate(0.85)
    exp = CalibrationExplainer().explain_calibration(cal)
    assert exp["certainty_forbidden"] is True


def test_confidence_breakdown() -> None:
    bd = ConfidenceBreakdownBuilder().build(raw_confidence=0.9, salience=0.7)
    assert bd.final_confidence < 1.0
    assert bd.below_certainty is True


def test_uncertainty_reasoning() -> None:
    band = UncertaintyBand(0.2, 0.5, 0.8, confidence=0.75)
    reason = UncertaintyReasoning().reason_band(band)
    assert reason["certainty_forbidden"] is True
