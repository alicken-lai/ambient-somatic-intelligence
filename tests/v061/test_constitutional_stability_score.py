"""Area 8: ConstitutionalStabilityScore gate."""

from observability.v061.constitutional_stability_score import (
    CONSTITUTIONAL_GATE_THRESHOLD,
    ConstitutionalAttentionEvidence,
    evaluate_constitutional_stability,
)


def test_gate_threshold_090() -> None:
    assert CONSTITUTIONAL_GATE_THRESHOLD == 0.90


def test_clean_evidence_passes() -> None:
    ev = ConstitutionalAttentionEvidence(
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
        constitutional_compliance_rate=1.0,
        guardian_supremacy_preserved=True,
        epistemic_compliance_rate=1.0,
        replay_constitutional_rate=1.0,
        mutation_block_rate=1.0,
        constitution_sealed=True,
    )
    report = evaluate_constitutional_stability(ev)
    assert report.constitutional_score >= 0.90
    assert report.gate_pass is True


def test_forecaster_evidence(constitutional_forecaster, constitutional_bridge) -> None:
    from observability.v061.constitutional_stability_score import evidence_from_constitutional_forecaster

    ev = evidence_from_constitutional_forecaster(
        constitutional_forecaster, bridge=constitutional_bridge
    )
    report = evaluate_constitutional_stability(
        ev, forecaster=constitutional_forecaster, bridge=constitutional_bridge
    )
    assert report.constitutional_score >= 0.85
    assert ev.constitution_sealed is True
