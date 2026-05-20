"""Area 9–10: ExternalRuntimeGovernanceScore gate."""

from observability.v065c.external_runtime_governance_score import (
    EXTERNAL_RUNTIME_GATE_THRESHOLD,
    ExternalRuntimeAttentionEvidence,
    evaluate_external_runtime_governance,
)


def test_gate_threshold() -> None:
    assert EXTERNAL_RUNTIME_GATE_THRESHOLD == 0.90


def test_clean_evidence_passes() -> None:
    ev = ExternalRuntimeAttentionEvidence(
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
        contradiction_resistance_rate=1.0,
        replay_coherence_rate=1.0,
        constitutional_alignment_rate=1.0,
        drift_bounded_rate=1.0,
        fragmentation_containment_rate=1.0,
        coherence_explainability_rate=1.0,
        cognition_quality_rate=1.0,
        degradation_containment_rate=1.0,
        pathology_containment_rate=1.0,
        reflection_boundary_compliance_rate=1.0,
        calibration_reflection_bounded_rate=1.0,
        metacognitive_explainability_rate=1.0,
        stabilization_containment_rate=1.0,
        salience_damping_containment_rate=1.0,
        coherence_recovery_ready_rate=1.0,
        reflection_balance_rate=1.0,
        calibration_recovery_bounded_rate=1.0,
        homeostasis_explainability_rate=1.0,
        doctrine_filter_containment_rate=1.0,
        contamination_containment_rate=1.0,
        compatibility_advisory_rate=1.0,
        ide_export_boundary_rate=1.0,
        runtime_sandbox_containment_rate=1.0,
        precedence_guard_rate=1.0,
        sovereignty_containment_rate=1.0,
        ide_runtime_boundary_rate=1.0,
        provenance_runtime_integrity_rate=1.0,
        drift_decay_containment_rate=1.0,
    )
    report = evaluate_external_runtime_governance(ev)
    assert report.external_runtime_score >= 0.90
    assert report.gate_pass is True


def test_default_forecaster_score() -> None:
    report = evaluate_external_runtime_governance()
    assert report.external_runtime_score >= 0.88
