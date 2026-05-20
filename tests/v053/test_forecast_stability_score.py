"""Area 10: ForecastStabilityScore gate."""

from observability.v053.forecast_stability_score import (
    FORECAST_GATE_THRESHOLD,
    ForecastAttentionEvidence,
    evaluate_forecast_stability,
)


def test_gate_threshold_090() -> None:
    assert FORECAST_GATE_THRESHOLD == 0.90


def test_clean_evidence_passes() -> None:
    ev = ForecastAttentionEvidence(
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
    )
    report = evaluate_forecast_stability(ev)
    assert report.forecast_score >= 0.90
    assert report.gate_pass is True


def test_forecaster_evidence(forecaster, forecast_bridge) -> None:
    from observability.v053.forecast_stability_score import evidence_from_forecaster

    ev = evidence_from_forecaster(forecaster, bridge=forecast_bridge)
    report = evaluate_forecast_stability(ev, forecaster=forecaster, bridge=forecast_bridge)
    assert report.forecast_score >= 0.85
