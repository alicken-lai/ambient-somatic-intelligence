"""Area 8: CognitiveGovernanceStabilityScore gate."""

from observability.v060.cognitive_governance_stability_score import (
    COGNITIVE_GOVERNANCE_GATE_THRESHOLD,
    CognitiveGovernanceAttentionEvidence,
    evaluate_cognitive_governance_stability,
)


def test_gate_threshold_090() -> None:
    assert COGNITIVE_GOVERNANCE_GATE_THRESHOLD == 0.90


def test_clean_evidence_passes() -> None:
    ev = CognitiveGovernanceAttentionEvidence(
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
        arbitration_fairness=0.9,
        sovereignty_compliance_rate=1.0,
        uncertainty_override_rate=0.1,
        replay_bounded_rate=1.0,
        governance_loop_detected=False,
        autonomous_execution_blocked=True,
    )
    report = evaluate_cognitive_governance_stability(ev)
    assert report.governance_score >= 0.90
    assert report.gate_pass is True


def test_forecaster_evidence(governed_forecaster, governance_bridge) -> None:
    from observability.v060.cognitive_governance_stability_score import evidence_from_governed_forecaster

    ev = evidence_from_governed_forecaster(governed_forecaster, bridge=governance_bridge)
    report = evaluate_cognitive_governance_stability(
        ev, forecaster=governed_forecaster, bridge=governance_bridge
    )
    assert report.governance_score >= 0.85
    assert ev.governance_loop_detected is False
