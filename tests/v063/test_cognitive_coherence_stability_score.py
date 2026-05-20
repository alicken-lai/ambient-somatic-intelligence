"""Area 9–10: CognitiveCoherenceStabilityScore gate + simulations."""

from pathlib import Path

from observability.v063.cognitive_coherence_stability_score import (
    COGNITIVE_COHERENCE_GATE_THRESHOLD,
    CognitiveCoherenceAttentionEvidence,
    evaluate_cognitive_coherence_stability,
    evidence_from_coherence_forecaster,
)
from v063_runtime.simulations import WINDOWS, run_all_windows, write_timeseries


def test_gate_threshold_090() -> None:
    assert COGNITIVE_COHERENCE_GATE_THRESHOLD == 0.90


def test_clean_evidence_passes() -> None:
    ev = CognitiveCoherenceAttentionEvidence(
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
    )
    report = evaluate_cognitive_coherence_stability(ev)
    assert report.coherence_score >= 0.90
    assert report.gate_pass is True


def test_forecaster_evidence(coherence_forecaster, coherence_bridge) -> None:
    ev = evidence_from_coherence_forecaster(
        coherence_forecaster, bridge=coherence_bridge
    )
    report = evaluate_cognitive_coherence_stability(
        ev, forecaster=coherence_forecaster, bridge=coherence_bridge
    )
    assert report.coherence_score >= 0.85


def test_windows_include_180d() -> None:
    assert "180d" in WINDOWS


def test_run_all_windows_gate() -> None:
    data = run_all_windows()
    for w in data["windows"].values():
        assert w["coherence_score"] >= 0.85


def test_write_timeseries(tmp_path: Path) -> None:
    out = tmp_path / "long_horizon_coherence_timeseries.json"
    data = write_timeseries(out)
    assert out.is_file()
    assert "windows" in data
