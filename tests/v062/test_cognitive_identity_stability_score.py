"""Area 8: CognitiveIdentityStabilityScore gate."""

from observability.v062.cognitive_identity_stability_score import (
    COGNITIVE_IDENTITY_GATE_THRESHOLD,
    CognitiveIdentityAttentionEvidence,
    evaluate_cognitive_identity_stability,
)


def test_gate_threshold_090() -> None:
    assert COGNITIVE_IDENTITY_GATE_THRESHOLD == 0.90


def test_clean_evidence_passes() -> None:
    ev = CognitiveIdentityAttentionEvidence(
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
        provenance_integrity_rate=1.0,
        cognition_trust_rate=0.95,
        replay_identity_bounded_rate=1.0,
        fragmentation_resistance_rate=1.0,
        continuity_stability_rate=1.0,
        synthetic_containment_rate=0.95,
        identity_coherence_rate=1.0,
        identity_explainability_rate=1.0,
    )
    report = evaluate_cognitive_identity_stability(ev)
    assert report.identity_score >= 0.90
    assert report.gate_pass is True


def test_forecaster_evidence(identity_forecaster, identity_bridge) -> None:
    from observability.v062.cognitive_identity_stability_score import evidence_from_identity_forecaster

    ev = evidence_from_identity_forecaster(identity_forecaster, bridge=identity_bridge)
    report = evaluate_cognitive_identity_stability(
        ev, forecaster=identity_forecaster, bridge=identity_bridge
    )
    assert report.identity_score >= 0.85
