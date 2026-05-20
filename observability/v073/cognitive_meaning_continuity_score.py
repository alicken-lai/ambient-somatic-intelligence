"""v0.7.3 Cognitive Meaning Continuity Score — gate threshold 0.90."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from attention.forecasting.attention_forecast import AttentionForecast
from attention.kernel.attention_kernel import AttentionKernel
from attention.runtime.runtime_attention_memory_bridge import RuntimeAttentionMemoryBridge
from observability.v04.metric_normalizer import clamp01
from observability.v072.cognitive_temporal_continuity_score import (
    TEMPORAL_CONTINUITY_GATE_THRESHOLD,
    CognitiveTemporalContinuityAttentionEvidence,
    CognitiveTemporalContinuityScore,
    evaluate_cognitive_temporal_continuity,
    evidence_from_temporal_forecaster,
)
from observability.v073.drift_containment_metrics import collect_drift_containment_metrics
from observability.v073.lineage_integrity_metrics import collect_lineage_integrity_metrics
from observability.v073.meaning_decay_metrics import collect_meaning_decay_metrics
from observability.v073.meaning_integrity_metrics import collect_meaning_integrity_metrics
from observability.v073.ontology_boundary_metrics import collect_ontology_boundary_metrics
from observability.v073.semantic_provenance_metrics import collect_semantic_provenance_metrics

MEANING_CONTINUITY_GATE_THRESHOLD = 0.90

MEANING_EXTRA_WEIGHTS: dict[str, float] = {
    "drift_containment": 0.024,
    "ontology_boundary": 0.022,
    "lineage_integrity": 0.022,
    "meaning_decay": 0.022,
    "semantic_provenance": 0.022,
    "meaning_integrity": 0.021,
}


@dataclass
class CognitiveMeaningContinuityAttentionEvidence(CognitiveTemporalContinuityAttentionEvidence):
    drift_containment_rate: float = 1.0
    ontology_boundary_rate: float = 1.0
    meaning_lineage_integrity_rate: float = 1.0
    meaning_decay_rate: float = 1.0
    semantic_provenance_rate: float = 1.0
    meaning_integrity_rate: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        base = super().to_dict()
        base.update({
            "drift_containment_rate": round(self.drift_containment_rate, 4),
            "ontology_boundary_rate": round(self.ontology_boundary_rate, 4),
            "meaning_lineage_integrity_rate": round(self.meaning_lineage_integrity_rate, 4),
            "meaning_decay_rate": round(self.meaning_decay_rate, 4),
            "semantic_provenance_rate": round(self.semantic_provenance_rate, 4),
            "meaning_integrity_rate": round(self.meaning_integrity_rate, 4),
        })
        return base


@dataclass
class CognitiveMeaningContinuityScore(CognitiveTemporalContinuityScore):
    meaning_dimensions: dict[str, float] = field(default_factory=dict)
    meaning_continuity_score: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        base = super().to_dict()
        base["meaning_dimensions"] = {
            k: round(v, 4) for k, v in self.meaning_dimensions.items()
        }
        base["meaning_continuity_score"] = round(self.meaning_continuity_score, 4)
        return base


def evidence_from_meaning_forecaster(
    forecaster: AttentionForecast,
    *,
    bridge: RuntimeAttentionMemoryBridge | None = None,
    target_id: str = "meaning-gate-target",
    submissions: int = 0,
) -> CognitiveMeaningContinuityAttentionEvidence:
    base = evidence_from_temporal_forecaster(
        forecaster, bridge=bridge, target_id=target_id, submissions=submissions
    )
    drift = collect_drift_containment_metrics()
    boundary = collect_ontology_boundary_metrics()
    lineage = collect_lineage_integrity_metrics()
    decay = collect_meaning_decay_metrics()
    prov = collect_semantic_provenance_metrics()
    integrity = collect_meaning_integrity_metrics()
    return CognitiveMeaningContinuityAttentionEvidence(
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
        epoch_fragmentation_containment_rate=base.epoch_fragmentation_containment_rate,
        epoch_boundary_rate=base.epoch_boundary_rate,
        lineage_integrity_rate=base.lineage_integrity_rate,
        memory_decay_rate=base.memory_decay_rate,
        temporal_provenance_rate=base.temporal_provenance_rate,
        continuity_integrity_rate=base.continuity_integrity_rate,
        drift_containment_rate=drift.containment_rate,
        ontology_boundary_rate=boundary.boundary_rate,
        meaning_lineage_integrity_rate=lineage.integrity_rate,
        meaning_decay_rate=decay.decay_rate,
        semantic_provenance_rate=prov.provenance_rate,
        meaning_integrity_rate=integrity.integrity_rate,
    )


def evaluate_cognitive_meaning_continuity(
    evidence: CognitiveMeaningContinuityAttentionEvidence | None = None,
    *,
    forecaster: AttentionForecast | None = None,
    bridge: RuntimeAttentionMemoryBridge | None = None,
    kernel: AttentionKernel | None = None,
) -> CognitiveMeaningContinuityScore:
    if evidence is None:
        fc = forecaster or AttentionForecast(kernel=kernel)
        evidence = evidence_from_meaning_forecaster(fc, bridge=bridge)

    temporal_report = evaluate_cognitive_temporal_continuity(evidence, forecaster=forecaster, bridge=bridge)

    meaning_dims = {
        "drift_containment": clamp01(evidence.drift_containment_rate),
        "ontology_boundary": clamp01(evidence.ontology_boundary_rate),
        "lineage_integrity": clamp01(evidence.meaning_lineage_integrity_rate),
        "meaning_decay": clamp01(evidence.meaning_decay_rate),
        "semantic_provenance": clamp01(evidence.semantic_provenance_rate),
        "meaning_integrity": clamp01(evidence.meaning_integrity_rate),
    }
    meaning_bonus = sum(
        meaning_dims[k] * MEANING_EXTRA_WEIGHTS[k] for k in MEANING_EXTRA_WEIGHTS
    )
    combined = clamp01(temporal_report.temporal_continuity_score * 0.86 + meaning_bonus)

    hard_failures = list(temporal_report.hard_failures)
    if evidence.drift_containment_rate < 0.5:
        hard_failures.append("drift_containment_failed")
    if evidence.ontology_boundary_rate < 0.5:
        hard_failures.append("ontology_boundary_failed")
    if not evidence.guardian_supremacy_preserved:
        hard_failures.append("guardian_supremacy_at_risk")

    gate_pass = (
        combined >= MEANING_CONTINUITY_GATE_THRESHOLD
        and temporal_report.gate_pass
        and len(hard_failures) == 0
    )

    classification = (
        "production_grade_cognitive_meaning_continuity"
        if combined >= 0.95
        else "stable_cognitive_meaning_continuity"
        if combined >= MEANING_CONTINUITY_GATE_THRESHOLD
        else "restricted_cognitive_meaning_continuity"
    )

    return CognitiveMeaningContinuityScore(
        score=combined,
        classification=classification,
        dimensions=temporal_report.dimensions,
        gate_pass=gate_pass,
        gate_threshold=MEANING_CONTINUITY_GATE_THRESHOLD,
        evidence=evidence,
        hard_failures=hard_failures,
        runtime_dimensions=temporal_report.runtime_dimensions,
        runtime_score=temporal_report.runtime_score,
        memory_dimensions=temporal_report.memory_dimensions,
        memory_score=temporal_report.memory_score,
        forecast_dimensions=temporal_report.forecast_dimensions,
        forecast_score=temporal_report.forecast_score,
        calibration_dimensions=temporal_report.calibration_dimensions,
        calibration_score=temporal_report.calibration_score,
        governance_dimensions=temporal_report.governance_dimensions,
        governance_score=temporal_report.governance_score,
        constitutional_dimensions=temporal_report.constitutional_dimensions,
        constitutional_score=temporal_report.constitutional_score,
        identity_dimensions=temporal_report.identity_dimensions,
        identity_score=temporal_report.identity_score,
        coherence_dimensions=temporal_report.coherence_dimensions,
        coherence_score=temporal_report.coherence_score,
        metacognitive_dimensions=temporal_report.metacognitive_dimensions,
        metacognition_score=temporal_report.metacognition_score,
        homeostasis_dimensions=temporal_report.homeostasis_dimensions,
        homeostasis_score=temporal_report.homeostasis_score,
        external_dimensions=temporal_report.external_dimensions,
        external_skill_score=temporal_report.external_skill_score,
        external_runtime_dimensions=temporal_report.external_runtime_dimensions,
        external_runtime_score=temporal_report.external_runtime_score,
        civilization_dimensions=temporal_report.civilization_dimensions,
        civilization_score=temporal_report.civilization_score,
        reality_dimensions=temporal_report.reality_dimensions,
        reality_alignment_score=temporal_report.reality_alignment_score,
        temporal_dimensions=temporal_report.temporal_dimensions,
        temporal_continuity_score=temporal_report.temporal_continuity_score,
        meaning_dimensions=meaning_dims,
        meaning_continuity_score=combined,
    )
