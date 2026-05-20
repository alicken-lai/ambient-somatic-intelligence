"""v0.6.5B External Skill Governance Score — gate threshold 0.90."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from attention.forecasting.attention_forecast import AttentionForecast
from attention.kernel.attention_kernel import AttentionKernel
from attention.runtime.runtime_attention_memory_bridge import RuntimeAttentionMemoryBridge
from observability.v04.metric_normalizer import clamp01
from observability.v065.cognitive_homeostasis_stability_score import (
    CognitiveHomeostasisAttentionEvidence,
    CognitiveHomeostasisStabilityReport,
    evaluate_cognitive_homeostasis_stability,
    evidence_from_homeostasis_forecaster,
)
from observability.v065b.compatibility_advisory_metrics import (
    collect_compatibility_advisory_metrics,
)
from observability.v065b.contamination_containment_metrics import (
    collect_contamination_containment_metrics,
)
from observability.v065b.doctrine_filter_metrics import collect_doctrine_filter_metrics
from observability.v065b.ide_export_boundary_metrics import collect_ide_export_boundary_metrics
from observability.v065b.provenance_integrity_metrics import collect_provenance_integrity_metrics

EXTERNAL_SKILL_GATE_THRESHOLD = 0.90

EXTERNAL_EXTRA_WEIGHTS: dict[str, float] = {
    "doctrine_filter_containment": 0.030,
    "provenance_integrity": 0.030,
    "contamination_containment": 0.028,
    "compatibility_advisory": 0.028,
    "ide_export_boundary": 0.024,
}


@dataclass
class ExternalSkillAttentionEvidence(CognitiveHomeostasisAttentionEvidence):
    doctrine_filter_containment_rate: float = 1.0
    contamination_containment_rate: float = 1.0
    compatibility_advisory_rate: float = 1.0
    ide_export_boundary_rate: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        base = super().to_dict()
        base.update({
            "doctrine_filter_containment_rate": round(
                self.doctrine_filter_containment_rate, 4
            ),
            "contamination_containment_rate": round(
                self.contamination_containment_rate, 4
            ),
            "compatibility_advisory_rate": round(self.compatibility_advisory_rate, 4),
            "ide_export_boundary_rate": round(self.ide_export_boundary_rate, 4),
        })
        return base


@dataclass
class ExternalSkillGovernanceScore(CognitiveHomeostasisStabilityReport):
    external_dimensions: dict[str, float] = field(default_factory=dict)
    external_skill_score: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        base = super().to_dict()
        base["external_dimensions"] = {
            k: round(v, 4) for k, v in self.external_dimensions.items()
        }
        base["external_skill_score"] = round(self.external_skill_score, 4)
        return base


def evidence_from_external_forecaster(
    forecaster: AttentionForecast,
    *,
    bridge: RuntimeAttentionMemoryBridge | None = None,
    target_id: str = "external-skill-gate-target",
    submissions: int = 0,
) -> ExternalSkillAttentionEvidence:
    base = evidence_from_homeostasis_forecaster(
        forecaster, bridge=bridge, target_id=target_id, submissions=submissions
    )
    filt = collect_doctrine_filter_metrics()
    prov = collect_provenance_integrity_metrics()
    contam = collect_contamination_containment_metrics()
    compat = collect_compatibility_advisory_metrics()
    ide = collect_ide_export_boundary_metrics()
    return ExternalSkillAttentionEvidence(
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
        doctrine_filter_containment_rate=filt.containment_rate,
        provenance_integrity_rate=max(base.provenance_integrity_rate, prov.integrity_rate),
        contamination_containment_rate=contam.containment_rate,
        compatibility_advisory_rate=compat.compatible_rate,
        ide_export_boundary_rate=ide.boundary_rate,
    )


def evaluate_external_skill_governance(
    evidence: ExternalSkillAttentionEvidence | None = None,
    *,
    forecaster: AttentionForecast | None = None,
    bridge: RuntimeAttentionMemoryBridge | None = None,
    kernel: AttentionKernel | None = None,
) -> ExternalSkillGovernanceScore:
    if evidence is None:
        fc = forecaster or AttentionForecast(kernel=kernel)
        evidence = evidence_from_external_forecaster(fc, bridge=bridge)

    homeo_report = evaluate_cognitive_homeostasis_stability(
        evidence, forecaster=forecaster, bridge=bridge
    )

    ext_dims = {
        "doctrine_filter_containment": clamp01(evidence.doctrine_filter_containment_rate),
        "provenance_integrity": clamp01(evidence.provenance_integrity_rate),
        "contamination_containment": clamp01(evidence.contamination_containment_rate),
        "compatibility_advisory": clamp01(evidence.compatibility_advisory_rate),
        "ide_export_boundary": clamp01(evidence.ide_export_boundary_rate),
    }
    ext_bonus = sum(ext_dims[k] * EXTERNAL_EXTRA_WEIGHTS[k] for k in EXTERNAL_EXTRA_WEIGHTS)
    combined = clamp01(homeo_report.homeostasis_score * 0.84 + ext_bonus)

    hard_failures = list(homeo_report.hard_failures)
    if evidence.provenance_integrity_rate < 0.5:
        hard_failures.append("provenance_integrity_low")
    if evidence.doctrine_filter_containment_rate < 0.5:
        hard_failures.append("doctrine_filter_failed")

    gate_pass = (
        combined >= EXTERNAL_SKILL_GATE_THRESHOLD
        and homeo_report.gate_pass
        and len(hard_failures) == 0
    )

    classification = (
        "production_grade_external_skill_governance"
        if combined >= 0.95
        else "stable_external_skill_mount"
        if combined >= EXTERNAL_SKILL_GATE_THRESHOLD
        else "restricted_external_mount"
    )

    return ExternalSkillGovernanceScore(
        score=combined,
        classification=classification,
        dimensions=homeo_report.dimensions,
        gate_pass=gate_pass,
        gate_threshold=EXTERNAL_SKILL_GATE_THRESHOLD,
        evidence=evidence,
        hard_failures=hard_failures,
        runtime_dimensions=homeo_report.runtime_dimensions,
        runtime_score=homeo_report.runtime_score,
        memory_dimensions=homeo_report.memory_dimensions,
        memory_score=homeo_report.memory_score,
        forecast_dimensions=homeo_report.forecast_dimensions,
        forecast_score=homeo_report.forecast_score,
        calibration_dimensions=homeo_report.calibration_dimensions,
        calibration_score=homeo_report.calibration_score,
        governance_dimensions=homeo_report.governance_dimensions,
        governance_score=homeo_report.governance_score,
        constitutional_dimensions=homeo_report.constitutional_dimensions,
        constitutional_score=homeo_report.constitutional_score,
        identity_dimensions=homeo_report.identity_dimensions,
        identity_score=homeo_report.identity_score,
        coherence_dimensions=homeo_report.coherence_dimensions,
        coherence_score=homeo_report.coherence_score,
        metacognitive_dimensions=homeo_report.metacognitive_dimensions,
        metacognition_score=homeo_report.metacognition_score,
        homeostasis_dimensions=homeo_report.homeostasis_dimensions,
        homeostasis_score=homeo_report.homeostasis_score,
        external_dimensions=ext_dims,
        external_skill_score=combined,
    )
