"""v0.7.2 Cognitive Temporal Continuity Score — gate threshold 0.90."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from attention.forecasting.attention_forecast import AttentionForecast
from attention.kernel.attention_kernel import AttentionKernel
from attention.runtime.runtime_attention_memory_bridge import RuntimeAttentionMemoryBridge
from observability.v04.metric_normalizer import clamp01
from observability.v071.cognitive_reality_alignment_score import (
    REALITY_ALIGNMENT_GATE_THRESHOLD,
    CognitiveRealityAlignmentAttentionEvidence,
    CognitiveRealityAlignmentScore,
    evaluate_cognitive_reality_alignment,
    evidence_from_reality_forecaster,
)
from observability.v072.continuity_integrity_metrics import collect_continuity_integrity_metrics
from observability.v072.epoch_boundary_metrics import collect_epoch_boundary_metrics
from observability.v072.fragmentation_containment_metrics import collect_fragmentation_containment_metrics
from observability.v072.lineage_integrity_metrics import collect_lineage_integrity_metrics
from observability.v072.memory_decay_metrics import collect_memory_decay_metrics
from observability.v072.temporal_provenance_metrics import collect_temporal_provenance_metrics

TEMPORAL_CONTINUITY_GATE_THRESHOLD = 0.90

TEMPORAL_EXTRA_WEIGHTS: dict[str, float] = {
    "fragmentation_containment": 0.024,
    "epoch_boundary": 0.022,
    "lineage_integrity": 0.022,
    "memory_decay": 0.022,
    "temporal_provenance": 0.022,
    "continuity_integrity": 0.021,
}


@dataclass
class CognitiveTemporalContinuityAttentionEvidence(CognitiveRealityAlignmentAttentionEvidence):
    epoch_fragmentation_containment_rate: float = 1.0
    epoch_boundary_rate: float = 1.0
    lineage_integrity_rate: float = 1.0
    memory_decay_rate: float = 1.0
    temporal_provenance_rate: float = 1.0
    continuity_integrity_rate: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        base = super().to_dict()
        base.update({
            "epoch_fragmentation_containment_rate": round(
                self.epoch_fragmentation_containment_rate, 4
            ),
            "epoch_boundary_rate": round(self.epoch_boundary_rate, 4),
            "lineage_integrity_rate": round(self.lineage_integrity_rate, 4),
            "memory_decay_rate": round(self.memory_decay_rate, 4),
            "temporal_provenance_rate": round(self.temporal_provenance_rate, 4),
            "continuity_integrity_rate": round(self.continuity_integrity_rate, 4),
        })
        return base


@dataclass
class CognitiveTemporalContinuityScore(CognitiveRealityAlignmentScore):
    temporal_dimensions: dict[str, float] = field(default_factory=dict)
    temporal_continuity_score: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        base = super().to_dict()
        base["temporal_dimensions"] = {
            k: round(v, 4) for k, v in self.temporal_dimensions.items()
        }
        base["temporal_continuity_score"] = round(self.temporal_continuity_score, 4)
        return base


def evidence_from_temporal_forecaster(
    forecaster: AttentionForecast,
    *,
    bridge: RuntimeAttentionMemoryBridge | None = None,
    target_id: str = "temporal-gate-target",
    submissions: int = 0,
) -> CognitiveTemporalContinuityAttentionEvidence:
    base = evidence_from_reality_forecaster(
        forecaster, bridge=bridge, target_id=target_id, submissions=submissions
    )
    frag = collect_fragmentation_containment_metrics()
    epoch = collect_epoch_boundary_metrics()
    lineage = collect_lineage_integrity_metrics()
    decay = collect_memory_decay_metrics()
    prov = collect_temporal_provenance_metrics()
    integrity = collect_continuity_integrity_metrics()
    return CognitiveTemporalContinuityAttentionEvidence(
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
        divergence_containment_rate=base.divergence_containment_rate,
        bounded_consensus_rate=base.bounded_consensus_rate,
        truth_boundary_rate=base.truth_boundary_rate,
        replay_alignment_rate=base.replay_alignment_rate,
        contamination_guard_rate=base.contamination_guard_rate,
        reality_integrity_rate=base.reality_integrity_rate,
        epoch_fragmentation_containment_rate=frag.containment_rate,
        epoch_boundary_rate=epoch.boundary_rate,
        lineage_integrity_rate=lineage.integrity_rate,
        memory_decay_rate=decay.decay_rate,
        temporal_provenance_rate=prov.provenance_rate,
        continuity_integrity_rate=integrity.integrity_rate,
    )


def evaluate_cognitive_temporal_continuity(
    evidence: CognitiveTemporalContinuityAttentionEvidence | None = None,
    *,
    forecaster: AttentionForecast | None = None,
    bridge: RuntimeAttentionMemoryBridge | None = None,
    kernel: AttentionKernel | None = None,
) -> CognitiveTemporalContinuityScore:
    if evidence is None:
        fc = forecaster or AttentionForecast(kernel=kernel)
        evidence = evidence_from_temporal_forecaster(fc, bridge=bridge)

    reality_report = evaluate_cognitive_reality_alignment(evidence, forecaster=forecaster, bridge=bridge)

    temporal_dims = {
        "fragmentation_containment": clamp01(evidence.epoch_fragmentation_containment_rate),
        "epoch_boundary": clamp01(evidence.epoch_boundary_rate),
        "lineage_integrity": clamp01(evidence.lineage_integrity_rate),
        "memory_decay": clamp01(evidence.memory_decay_rate),
        "temporal_provenance": clamp01(evidence.temporal_provenance_rate),
        "continuity_integrity": clamp01(evidence.continuity_integrity_rate),
    }
    temporal_bonus = sum(
        temporal_dims[k] * TEMPORAL_EXTRA_WEIGHTS[k] for k in TEMPORAL_EXTRA_WEIGHTS
    )
    combined = clamp01(reality_report.reality_alignment_score * 0.86 + temporal_bonus)

    hard_failures = list(reality_report.hard_failures)
    if evidence.epoch_fragmentation_containment_rate < 0.5:
        hard_failures.append("epoch_fragmentation_containment_failed")
    if evidence.epoch_boundary_rate < 0.5:
        hard_failures.append("epoch_boundary_failed")
    if not evidence.guardian_supremacy_preserved:
        hard_failures.append("guardian_supremacy_at_risk")

    gate_pass = (
        combined >= TEMPORAL_CONTINUITY_GATE_THRESHOLD
        and reality_report.gate_pass
        and len(hard_failures) == 0
    )

    classification = (
        "production_grade_cognitive_temporal_continuity"
        if combined >= 0.95
        else "stable_cognitive_temporal_continuity"
        if combined >= TEMPORAL_CONTINUITY_GATE_THRESHOLD
        else "restricted_cognitive_temporal_continuity"
    )

    return CognitiveTemporalContinuityScore(
        score=combined,
        classification=classification,
        dimensions=reality_report.dimensions,
        gate_pass=gate_pass,
        gate_threshold=TEMPORAL_CONTINUITY_GATE_THRESHOLD,
        evidence=evidence,
        hard_failures=hard_failures,
        runtime_dimensions=reality_report.runtime_dimensions,
        runtime_score=reality_report.runtime_score,
        memory_dimensions=reality_report.memory_dimensions,
        memory_score=reality_report.memory_score,
        forecast_dimensions=reality_report.forecast_dimensions,
        forecast_score=reality_report.forecast_score,
        calibration_dimensions=reality_report.calibration_dimensions,
        calibration_score=reality_report.calibration_score,
        governance_dimensions=reality_report.governance_dimensions,
        governance_score=reality_report.governance_score,
        constitutional_dimensions=reality_report.constitutional_dimensions,
        constitutional_score=reality_report.constitutional_score,
        identity_dimensions=reality_report.identity_dimensions,
        identity_score=reality_report.identity_score,
        coherence_dimensions=reality_report.coherence_dimensions,
        coherence_score=reality_report.coherence_score,
        metacognitive_dimensions=reality_report.metacognitive_dimensions,
        metacognition_score=reality_report.metacognition_score,
        homeostasis_dimensions=reality_report.homeostasis_dimensions,
        homeostasis_score=reality_report.homeostasis_score,
        external_dimensions=reality_report.external_dimensions,
        external_skill_score=reality_report.external_skill_score,
        external_runtime_dimensions=reality_report.external_runtime_dimensions,
        external_runtime_score=reality_report.external_runtime_score,
        civilization_dimensions=reality_report.civilization_dimensions,
        civilization_score=reality_report.civilization_score,
        reality_dimensions=reality_report.reality_dimensions,
        reality_alignment_score=reality_report.reality_alignment_score,
        temporal_dimensions=temporal_dims,
        temporal_continuity_score=combined,
    )
