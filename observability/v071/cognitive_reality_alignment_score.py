"""v0.7.1 Cognitive Reality Alignment Score — gate threshold 0.90."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from attention.forecasting.attention_forecast import AttentionForecast
from attention.kernel.attention_kernel import AttentionKernel
from attention.runtime.runtime_attention_memory_bridge import RuntimeAttentionMemoryBridge
from observability.v04.metric_normalizer import clamp01
from observability.v070.cognitive_civilization_stability_score import (
    CIVILIZATION_GATE_THRESHOLD,
    CognitiveCivilizationAttentionEvidence,
    CognitiveCivilizationStabilityScore,
    evaluate_cognitive_civilization_stability,
    evidence_from_civilization_forecaster,
)
from observability.v071.bounded_consensus_metrics import collect_bounded_consensus_metrics
from observability.v071.contamination_guard_metrics import collect_contamination_guard_metrics
from observability.v071.divergence_containment_metrics import collect_divergence_containment_metrics
from observability.v071.reality_integrity_metrics import collect_reality_integrity_metrics
from observability.v071.replay_alignment_metrics import collect_replay_alignment_metrics
from observability.v071.truth_boundary_metrics import collect_truth_boundary_metrics

REALITY_ALIGNMENT_GATE_THRESHOLD = 0.90

REALITY_EXTRA_WEIGHTS: dict[str, float] = {
    "divergence_containment": 0.024,
    "bounded_consensus": 0.024,
    "truth_boundary": 0.022,
    "replay_alignment": 0.022,
    "contamination_guard": 0.022,
    "reality_integrity": 0.021,
}


@dataclass
class CognitiveRealityAlignmentAttentionEvidence(CognitiveCivilizationAttentionEvidence):
    divergence_containment_rate: float = 1.0
    bounded_consensus_rate: float = 1.0
    truth_boundary_rate: float = 1.0
    replay_alignment_rate: float = 1.0
    contamination_guard_rate: float = 1.0
    reality_integrity_rate: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        base = super().to_dict()
        base.update({
            "divergence_containment_rate": round(self.divergence_containment_rate, 4),
            "bounded_consensus_rate": round(self.bounded_consensus_rate, 4),
            "truth_boundary_rate": round(self.truth_boundary_rate, 4),
            "replay_alignment_rate": round(self.replay_alignment_rate, 4),
            "contamination_guard_rate": round(self.contamination_guard_rate, 4),
            "reality_integrity_rate": round(self.reality_integrity_rate, 4),
        })
        return base


@dataclass
class CognitiveRealityAlignmentScore(CognitiveCivilizationStabilityScore):
    reality_dimensions: dict[str, float] = field(default_factory=dict)
    reality_alignment_score: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        base = super().to_dict()
        base["reality_dimensions"] = {
            k: round(v, 4) for k, v in self.reality_dimensions.items()
        }
        base["reality_alignment_score"] = round(self.reality_alignment_score, 4)
        return base


def evidence_from_reality_forecaster(
    forecaster: AttentionForecast,
    *,
    bridge: RuntimeAttentionMemoryBridge | None = None,
    target_id: str = "reality-gate-target",
    submissions: int = 0,
) -> CognitiveRealityAlignmentAttentionEvidence:
    base = evidence_from_civilization_forecaster(
        forecaster, bridge=bridge, target_id=target_id, submissions=submissions
    )
    div = collect_divergence_containment_metrics()
    bc = collect_bounded_consensus_metrics()
    tb = collect_truth_boundary_metrics()
    replay = collect_replay_alignment_metrics()
    contam = collect_contamination_guard_metrics()
    integrity = collect_reality_integrity_metrics()
    return CognitiveRealityAlignmentAttentionEvidence(
        explainability_coverage=base.explainability_coverage,
        competition_fairness=base.competition_fairness,
        focus_stability_score=base.focus_stability_score,
        budget_overrun=base.budget_overrun,
        opaque_salience_count=base.opaque_salience_count,
        precursor_match_rate=base.precursor_match_rate,
        memory_recall_rate=base.memory_recall_rate,
        somatic_adapter_ok=base.somatic_adapter_ok,
        decay_applied=base.decay_applied,
        recovery_ok=base.recovery_ok,
        adapter_ok=base.adapter_ok,
        pressure_composite=base.pressure_composite,
        focus_entropy=base.focus_entropy,
        submission_count=base.submission_count,
        store_fill_ratio=base.store_fill_ratio,
        trace_coverage=base.trace_coverage,
        precursor_match_rate_mem=base.precursor_match_rate_mem,
        background_stability=base.background_stability,
        reinforcement_bounded=base.reinforcement_bounded,
        memory_count=base.memory_count,
        mean_projection_confidence=base.mean_projection_confidence,
        mean_band_width=base.mean_band_width,
        precursor_forecast_rate=base.precursor_forecast_rate,
        forecast_pressure_headroom=base.forecast_pressure_headroom,
        trajectory_stable=base.trajectory_stable,
        no_recursive_amplification=base.no_recursive_amplification,
        mean_calibrated_confidence=base.mean_calibrated_confidence,
        fp_rate=base.fp_rate,
        humility_factor_mean=base.humility_factor_mean,
        cap_violations=base.cap_violations,
        certainty_never_reached=base.certainty_never_reached,
        arbitration_fairness=base.arbitration_fairness,
        sovereignty_compliance_rate=base.sovereignty_compliance_rate,
        uncertainty_override_rate=base.uncertainty_override_rate,
        replay_bounded_rate=base.replay_bounded_rate,
        governance_loop_detected=base.governance_loop_detected,
        autonomous_execution_blocked=base.autonomous_execution_blocked,
        constitutional_compliance_rate=base.constitutional_compliance_rate,
        guardian_supremacy_preserved=base.guardian_supremacy_preserved,
        epistemic_compliance_rate=base.epistemic_compliance_rate,
        replay_constitutional_rate=base.replay_constitutional_rate,
        mutation_block_rate=base.mutation_block_rate,
        constitution_sealed=base.constitution_sealed,
        cognition_trust_rate=base.cognition_trust_rate,
        replay_identity_bounded_rate=base.replay_identity_bounded_rate,
        fragmentation_resistance_rate=base.fragmentation_resistance_rate,
        continuity_stability_rate=base.continuity_stability_rate,
        synthetic_containment_rate=base.synthetic_containment_rate,
        identity_coherence_rate=base.identity_coherence_rate,
        identity_explainability_rate=base.identity_explainability_rate,
        contradiction_resistance_rate=base.contradiction_resistance_rate,
        replay_coherence_rate=base.replay_coherence_rate,
        constitutional_alignment_rate=base.constitutional_alignment_rate,
        drift_bounded_rate=base.drift_bounded_rate,
        fragmentation_containment_rate=base.fragmentation_containment_rate,
        coherence_explainability_rate=base.coherence_explainability_rate,
        cognition_quality_rate=base.cognition_quality_rate,
        degradation_containment_rate=base.degradation_containment_rate,
        pathology_containment_rate=base.pathology_containment_rate,
        reflection_boundary_compliance_rate=base.reflection_boundary_compliance_rate,
        calibration_reflection_bounded_rate=base.calibration_reflection_bounded_rate,
        metacognitive_explainability_rate=base.metacognitive_explainability_rate,
        stabilization_containment_rate=base.stabilization_containment_rate,
        salience_damping_containment_rate=base.salience_damping_containment_rate,
        coherence_recovery_ready_rate=base.coherence_recovery_ready_rate,
        reflection_balance_rate=base.reflection_balance_rate,
        calibration_recovery_bounded_rate=base.calibration_recovery_bounded_rate,
        homeostasis_explainability_rate=base.homeostasis_explainability_rate,
        doctrine_filter_containment_rate=base.doctrine_filter_containment_rate,
        provenance_integrity_rate=base.provenance_integrity_rate,
        contamination_containment_rate=base.contamination_containment_rate,
        compatibility_advisory_rate=base.compatibility_advisory_rate,
        ide_export_boundary_rate=base.ide_export_boundary_rate,
        runtime_sandbox_containment_rate=base.runtime_sandbox_containment_rate,
        precedence_guard_rate=base.precedence_guard_rate,
        sovereignty_containment_rate=base.sovereignty_containment_rate,
        ide_runtime_boundary_rate=base.ide_runtime_boundary_rate,
        provenance_runtime_integrity_rate=base.provenance_runtime_integrity_rate,
        drift_decay_containment_rate=base.drift_decay_containment_rate,
        diplomacy_boundary_rate=base.diplomacy_boundary_rate,
        treaty_integrity_rate=base.treaty_integrity_rate,
        federation_stability_rate=base.federation_stability_rate,
        non_interference_rate=base.non_interference_rate,
        provenance_exchange_rate=base.provenance_exchange_rate,
        sovereignty_alignment_rate=base.sovereignty_alignment_rate,
        divergence_containment_rate=div.containment_rate,
        bounded_consensus_rate=bc.bounded_rate,
        truth_boundary_rate=tb.boundary_rate,
        replay_alignment_rate=replay.alignment_rate,
        contamination_guard_rate=contam.containment_rate,
        reality_integrity_rate=integrity.integrity_rate,
    )


def evaluate_cognitive_reality_alignment(
    evidence: CognitiveRealityAlignmentAttentionEvidence | None = None,
    *,
    forecaster: AttentionForecast | None = None,
    bridge: RuntimeAttentionMemoryBridge | None = None,
    kernel: AttentionKernel | None = None,
) -> CognitiveRealityAlignmentScore:
    if evidence is None:
        fc = forecaster or AttentionForecast(kernel=kernel)
        evidence = evidence_from_reality_forecaster(fc, bridge=bridge)

    civ_report = evaluate_cognitive_civilization_stability(evidence, forecaster=forecaster, bridge=bridge)

    reality_dims = {
        "divergence_containment": clamp01(evidence.divergence_containment_rate),
        "bounded_consensus": clamp01(evidence.bounded_consensus_rate),
        "truth_boundary": clamp01(evidence.truth_boundary_rate),
        "replay_alignment": clamp01(evidence.replay_alignment_rate),
        "contamination_guard": clamp01(evidence.contamination_guard_rate),
        "reality_integrity": clamp01(evidence.reality_integrity_rate),
    }
    reality_bonus = sum(
        reality_dims[k] * REALITY_EXTRA_WEIGHTS[k] for k in REALITY_EXTRA_WEIGHTS
    )
    combined = clamp01(civ_report.civilization_score * 0.86 + reality_bonus)

    hard_failures = list(civ_report.hard_failures)
    if evidence.divergence_containment_rate < 0.5:
        hard_failures.append("divergence_containment_failed")
    if evidence.truth_boundary_rate < 0.5:
        hard_failures.append("truth_boundary_failed")
    if not evidence.guardian_supremacy_preserved:
        hard_failures.append("guardian_supremacy_at_risk")

    gate_pass = (
        combined >= REALITY_ALIGNMENT_GATE_THRESHOLD
        and civ_report.gate_pass
        and len(hard_failures) == 0
    )

    classification = (
        "production_grade_cognitive_reality_alignment"
        if combined >= 0.95
        else "stable_cognitive_reality_alignment"
        if combined >= REALITY_ALIGNMENT_GATE_THRESHOLD
        else "restricted_cognitive_reality_alignment"
    )

    return CognitiveRealityAlignmentScore(
        score=combined,
        classification=classification,
        dimensions=civ_report.dimensions,
        gate_pass=gate_pass,
        gate_threshold=REALITY_ALIGNMENT_GATE_THRESHOLD,
        evidence=evidence,
        hard_failures=hard_failures,
        runtime_dimensions=civ_report.runtime_dimensions,
        runtime_score=civ_report.runtime_score,
        memory_dimensions=civ_report.memory_dimensions,
        memory_score=civ_report.memory_score,
        forecast_dimensions=civ_report.forecast_dimensions,
        forecast_score=civ_report.forecast_score,
        calibration_dimensions=civ_report.calibration_dimensions,
        calibration_score=civ_report.calibration_score,
        governance_dimensions=civ_report.governance_dimensions,
        governance_score=civ_report.governance_score,
        constitutional_dimensions=civ_report.constitutional_dimensions,
        constitutional_score=civ_report.constitutional_score,
        identity_dimensions=civ_report.identity_dimensions,
        identity_score=civ_report.identity_score,
        coherence_dimensions=civ_report.coherence_dimensions,
        coherence_score=civ_report.coherence_score,
        metacognitive_dimensions=civ_report.metacognitive_dimensions,
        metacognition_score=civ_report.metacognition_score,
        homeostasis_dimensions=civ_report.homeostasis_dimensions,
        homeostasis_score=civ_report.homeostasis_score,
        external_dimensions=civ_report.external_dimensions,
        external_skill_score=civ_report.external_skill_score,
        external_runtime_dimensions=civ_report.external_runtime_dimensions,
        external_runtime_score=civ_report.external_runtime_score,
        civilization_dimensions=civ_report.civilization_dimensions,
        civilization_score=civ_report.civilization_score,
        reality_dimensions=reality_dims,
        reality_alignment_score=combined,
    )
