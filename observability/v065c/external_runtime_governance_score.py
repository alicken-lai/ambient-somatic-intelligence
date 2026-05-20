"""v0.6.5C External Runtime Governance Score — gate threshold 0.90."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from attention.forecasting.attention_forecast import AttentionForecast
from attention.kernel.attention_kernel import AttentionKernel
from attention.runtime.runtime_attention_memory_bridge import RuntimeAttentionMemoryBridge
from observability.v04.metric_normalizer import clamp01
from observability.v065b.external_skill_governance_score import (
    EXTERNAL_SKILL_GATE_THRESHOLD,
    ExternalSkillAttentionEvidence,
    ExternalSkillGovernanceScore,
    evaluate_external_skill_governance,
    evidence_from_external_forecaster,
)
from observability.v065c.drift_decay_metrics import collect_drift_decay_metrics
from observability.v065c.ide_runtime_boundary_metrics import collect_ide_runtime_boundary_metrics
from observability.v065c.precedence_guard_metrics import collect_precedence_guard_metrics
from observability.v065c.provenance_runtime_metrics import collect_provenance_runtime_metrics
from observability.v065c.runtime_sandbox_metrics import collect_runtime_sandbox_metrics
from observability.v065c.sovereignty_containment_metrics import collect_sovereignty_containment_metrics

EXTERNAL_RUNTIME_GATE_THRESHOLD = 0.90

RUNTIME_EXTRA_WEIGHTS: dict[str, float] = {
    "runtime_sandbox_containment": 0.025,
    "precedence_guard_rate": 0.025,
    "sovereignty_containment": 0.023,
    "ide_runtime_boundary": 0.023,
    "provenance_runtime_integrity": 0.023,
    "drift_decay_containment": 0.021,
}


@dataclass
class ExternalRuntimeAttentionEvidence(ExternalSkillAttentionEvidence):
    runtime_sandbox_containment_rate: float = 1.0
    precedence_guard_rate: float = 1.0
    sovereignty_containment_rate: float = 1.0
    ide_runtime_boundary_rate: float = 1.0
    provenance_runtime_integrity_rate: float = 1.0
    drift_decay_containment_rate: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        base = super().to_dict()
        base.update({
            "runtime_sandbox_containment_rate": round(
                self.runtime_sandbox_containment_rate, 4
            ),
            "precedence_guard_rate": round(self.precedence_guard_rate, 4),
            "sovereignty_containment_rate": round(
                self.sovereignty_containment_rate, 4
            ),
            "ide_runtime_boundary_rate": round(self.ide_runtime_boundary_rate, 4),
            "provenance_runtime_integrity_rate": round(
                self.provenance_runtime_integrity_rate, 4
            ),
            "drift_decay_containment_rate": round(
                self.drift_decay_containment_rate, 4
            ),
        })
        return base


@dataclass
class ExternalRuntimeGovernanceScore(ExternalSkillGovernanceScore):
    external_runtime_dimensions: dict[str, float] = field(default_factory=dict)
    external_runtime_score: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        base = super().to_dict()
        base["external_runtime_dimensions"] = {
            k: round(v, 4) for k, v in self.external_runtime_dimensions.items()
        }
        base["external_runtime_score"] = round(self.external_runtime_score, 4)
        return base


def evidence_from_runtime_forecaster(
    forecaster: AttentionForecast,
    *,
    bridge: RuntimeAttentionMemoryBridge | None = None,
    target_id: str = "external-runtime-gate-target",
    submissions: int = 0,
) -> ExternalRuntimeAttentionEvidence:
    base = evidence_from_external_forecaster(
        forecaster, bridge=bridge, target_id=target_id, submissions=submissions
    )
    sb = collect_runtime_sandbox_metrics()
    prec = collect_precedence_guard_metrics()
    sov = collect_sovereignty_containment_metrics()
    ide = collect_ide_runtime_boundary_metrics()
    prov = collect_provenance_runtime_metrics()
    drift = collect_drift_decay_metrics()
    return ExternalRuntimeAttentionEvidence(
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
        runtime_sandbox_containment_rate=sb.containment_rate,
        precedence_guard_rate=prec.guard_rate,
        sovereignty_containment_rate=sov.containment_rate,
        ide_runtime_boundary_rate=ide.boundary_rate,
        provenance_runtime_integrity_rate=prov.integrity_rate,
        drift_decay_containment_rate=drift.containment_rate,
    )


def evaluate_external_runtime_governance(
    evidence: ExternalRuntimeAttentionEvidence | None = None,
    *,
    forecaster: AttentionForecast | None = None,
    bridge: RuntimeAttentionMemoryBridge | None = None,
    kernel: AttentionKernel | None = None,
) -> ExternalRuntimeGovernanceScore:
    if evidence is None:
        fc = forecaster or AttentionForecast(kernel=kernel)
        evidence = evidence_from_runtime_forecaster(fc, bridge=bridge)

    mount_report = evaluate_external_skill_governance(evidence, forecaster=forecaster, bridge=bridge)

    rt_dims = {
        "runtime_sandbox_containment": clamp01(evidence.runtime_sandbox_containment_rate),
        "precedence_guard_rate": clamp01(evidence.precedence_guard_rate),
        "sovereignty_containment": clamp01(evidence.sovereignty_containment_rate),
        "ide_runtime_boundary": clamp01(evidence.ide_runtime_boundary_rate),
        "provenance_runtime_integrity": clamp01(evidence.provenance_runtime_integrity_rate),
        "drift_decay_containment": clamp01(evidence.drift_decay_containment_rate),
    }
    rt_bonus = sum(rt_dims[k] * RUNTIME_EXTRA_WEIGHTS[k] for k in RUNTIME_EXTRA_WEIGHTS)
    combined = clamp01(mount_report.external_skill_score * 0.88 + rt_bonus)

    hard_failures = list(mount_report.hard_failures)
    if evidence.precedence_guard_rate < 0.5:
        hard_failures.append("precedence_guard_failed")
    if evidence.runtime_sandbox_containment_rate < 0.5:
        hard_failures.append("runtime_sandbox_failed")

    gate_pass = (
        combined >= EXTERNAL_RUNTIME_GATE_THRESHOLD
        and mount_report.gate_pass
        and len(hard_failures) == 0
    )

    classification = (
        "production_grade_external_runtime"
        if combined >= 0.95
        else "stable_external_runtime_soak"
        if combined >= EXTERNAL_RUNTIME_GATE_THRESHOLD
        else "restricted_external_runtime"
    )

    return ExternalRuntimeGovernanceScore(
        score=combined,
        classification=classification,
        dimensions=mount_report.dimensions,
        gate_pass=gate_pass,
        gate_threshold=EXTERNAL_RUNTIME_GATE_THRESHOLD,
        evidence=evidence,
        hard_failures=hard_failures,
        runtime_dimensions=mount_report.runtime_dimensions,
        runtime_score=mount_report.runtime_score,
        memory_dimensions=mount_report.memory_dimensions,
        memory_score=mount_report.memory_score,
        forecast_dimensions=mount_report.forecast_dimensions,
        forecast_score=mount_report.forecast_score,
        calibration_dimensions=mount_report.calibration_dimensions,
        calibration_score=mount_report.calibration_score,
        governance_dimensions=mount_report.governance_dimensions,
        governance_score=mount_report.governance_score,
        constitutional_dimensions=mount_report.constitutional_dimensions,
        constitutional_score=mount_report.constitutional_score,
        identity_dimensions=mount_report.identity_dimensions,
        identity_score=mount_report.identity_score,
        coherence_dimensions=mount_report.coherence_dimensions,
        coherence_score=mount_report.coherence_score,
        metacognitive_dimensions=mount_report.metacognitive_dimensions,
        metacognition_score=mount_report.metacognition_score,
        homeostasis_dimensions=mount_report.homeostasis_dimensions,
        homeostasis_score=mount_report.homeostasis_score,
        external_dimensions=mount_report.external_dimensions,
        external_skill_score=mount_report.external_skill_score,
        external_runtime_dimensions=rt_dims,
        external_runtime_score=combined,
    )
