"""Unit tests for the attention.calibration layer + calibrated runtime/explainability."""

from __future__ import annotations

from attention.calibration.confidence_cap import ABSOLUTE_MAX_CONFIDENCE, ConfidenceCap, apply_confidence_cap
from attention.calibration.false_positive_tracker import FalsePositiveTracker
from attention.calibration.forecast_confidence import ForecastConfidenceCalibrator
from attention.calibration.forecast_humility import ForecastHumility
from attention.consolidation.attention_memory import AttentionMemory
from attention.core.attention_target import AttentionTarget
from attention.explainability.calibration_explainer import CalibrationExplainer
from attention.explainability.confidence_breakdown import ConfidenceBreakdownBuilder
from attention.explainability.uncertainty_reasoning import UncertaintyReasoning
from attention.forecasting.forecast_uncertainty import UncertaintyBand
from attention.kernel.attention_kernel import AttentionKernel
from attention.runtime.calibrated_attention_activation import CalibratedAttentionActivation
from attention.runtime.confidence_weighted_salience import ConfidenceWeightedSalience


# --- confidence cap + calibrator never reaches certainty ---------------------

def test_cap_below_one_and_apply() -> None:
    assert ABSOLUTE_MAX_CONFIDENCE < 1.0
    assert apply_confidence_cap(1.0) <= ABSOLUTE_MAX_CONFIDENCE
    assert ConfidenceCap().violates_absolute(1.0) is True


def test_calibrator_never_certain() -> None:
    cal = ForecastConfidenceCalibrator()
    for raw in (1.0, 0.999, 0.99, 0.98):
        result = cal.calibrate(raw, band_width=0.05)
        assert result.calibrated < 1.0
        assert result.calibrated <= ABSOLUTE_MAX_CONFIDENCE


def test_calibrator_records_factors() -> None:
    cal = ForecastConfidenceCalibrator().calibrate(0.85)
    assert 0.0 <= cal.humility_factor <= 1.0
    assert cal.fp_penalty >= 0.0


# --- humility ----------------------------------------------------------------

def test_humility_reduces_and_bounded() -> None:
    h = ForecastHumility()
    assert h.humble_confidence(0.95, band_width=0.3) < 0.95
    assert h.humility_factor(0.95, band_width=0.3) <= 1.0


# --- false positive tracker --------------------------------------------------

def test_fp_detection() -> None:
    t = FalsePositiveTracker()
    assert t.is_false_positive(0.8, 0.1) is True
    assert t.is_false_positive(0.5, 0.5) is False


def test_fp_adjusted_capped_and_penalised() -> None:
    t = FalsePositiveTracker()
    for _ in range(5):
        t.record("telemetry", "pat-a", 0.9, 0.1)
    adj = t.adjusted_confidence(0.95, "telemetry")
    assert adj <= ABSOLUTE_MAX_CONFIDENCE
    assert adj < 0.95
    assert t.fp_rate("telemetry") == 1.0


# --- runtime: weighted salience + calibrated activation ----------------------

def test_weighted_salience_never_amplifies() -> None:
    r = ConfidenceWeightedSalience().weight(0.6, 0.9)
    assert r.weighted <= 0.6


def test_calibrated_activation_from_memory() -> None:
    act = CalibratedAttentionActivation(kernel=AttentionKernel(max_focus=5, max_queue=20))
    mem = AttentionMemory(target_id="t1", domain="telemetry", salience_mean=0.7, salience_peak=0.8)
    result = act.activate_from_memory(mem, raw_confidence=0.75)
    assert "calibrated_confidence" in result
    assert result["calibrated_confidence"] < 1.0


def test_submit_calibrated_target() -> None:
    act = CalibratedAttentionActivation(kernel=AttentionKernel(max_focus=5, max_queue=20))
    t = AttentionTarget(source_domain="telemetry", signal_type="cal", raw_value=0.65)
    result = act.submit_calibrated_target(t, raw_confidence=0.8)
    assert result.get("calibrated_confidence", 0) < 1.0


# --- explainability ----------------------------------------------------------

def test_calibration_explainer_forbids_certainty() -> None:
    cal = ForecastConfidenceCalibrator().calibrate(0.85)
    exp = CalibrationExplainer().explain_calibration(cal)
    assert exp["certainty_forbidden"] is True


def test_confidence_breakdown_below_certainty() -> None:
    bd = ConfidenceBreakdownBuilder().build(raw_confidence=0.9, salience=0.7)
    assert bd.final_confidence < 1.0
    assert bd.below_certainty is True


def test_uncertainty_reasoning_forbids_certainty() -> None:
    band = UncertaintyBand(0.2, 0.5, 0.8, confidence=0.75)
    reason = UncertaintyReasoning().reason_band(band)
    assert reason["certainty_forbidden"] is True
