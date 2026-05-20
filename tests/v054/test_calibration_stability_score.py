"""Area 8: CalibrationStabilityScore gate."""

from attention.calibration.confidence_cap import ABSOLUTE_MAX_CONFIDENCE
from observability.v054.calibration_stability_score import (
    CALIBRATION_GATE_THRESHOLD,
    CalibrationAttentionEvidence,
    evaluate_calibration_stability,
)


def test_gate_threshold_090() -> None:
    assert CALIBRATION_GATE_THRESHOLD == 0.90


def test_clean_evidence_passes() -> None:
    ev = CalibrationAttentionEvidence(
        explainability_coverage=1.0,
        competition_fairness=0.88,
        adapter_ok=True,
        pressure_composite=0.2,
        store_fill_ratio=0.1,
        trace_coverage=0.2,
        background_stability=0.95,
        reinforcement_bounded=True,
        mean_projection_confidence=0.92,
        mean_band_width=0.1,
        precursor_forecast_rate=0.5,
        forecast_pressure_headroom=0.85,
        no_recursive_amplification=True,
        mean_calibrated_confidence=0.88,
        fp_rate=0.05,
        humility_factor_mean=0.92,
        cap_violations=0,
        certainty_never_reached=True,
    )
    report = evaluate_calibration_stability(ev)
    assert report.calibration_score >= 0.90
    assert report.gate_pass is True
    assert ev.mean_calibrated_confidence <= ABSOLUTE_MAX_CONFIDENCE


def test_forecaster_evidence(calibrated_forecaster, calibration_bridge) -> None:
    from observability.v054.calibration_stability_score import evidence_from_calibrated_forecaster

    ev = evidence_from_calibrated_forecaster(calibrated_forecaster, bridge=calibration_bridge)
    report = evaluate_calibration_stability(
        ev, forecaster=calibrated_forecaster, bridge=calibration_bridge
    )
    assert report.calibration_score >= 0.85
    assert ev.mean_calibrated_confidence < 1.0
