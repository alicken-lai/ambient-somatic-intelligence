"""v0.7.0 Cognitive Civilization Stability Score — gate threshold 0.90."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from attention.forecasting.attention_forecast import AttentionForecast
from attention.kernel.attention_kernel import AttentionKernel
from attention.runtime.runtime_attention_memory_bridge import RuntimeAttentionMemoryBridge
from observability.v04.metric_normalizer import clamp01
from observability.v065c.external_runtime_governance_score import (
    EXTERNAL_RUNTIME_GATE_THRESHOLD,
    ExternalRuntimeAttentionEvidence,
    ExternalRuntimeGovernanceScore,
    evaluate_external_runtime_governance,
    evidence_from_runtime_forecaster,
)
from observability.v070.diplomacy_boundary_metrics import collect_diplomacy_boundary_metrics
from observability.v070.federation_stability_metrics import collect_federation_stability_metrics
from observability.v070.non_interference_metrics import collect_non_interference_metrics
from observability.v070.provenance_exchange_metrics import collect_provenance_exchange_metrics
from observability.v070.sovereignty_alignment_metrics import collect_sovereignty_alignment_metrics
from observability.v070.treaty_integrity_metrics import collect_treaty_integrity_metrics

CIVILIZATION_GATE_THRESHOLD = 0.90

# Align with v065c external-runtime parent retention (0.88). Using 0.86 here
# double-compressed the civilization horizon and capped default scores ~0.940.
CIVILIZATION_PARENT_RETENTION = 0.88

CIVILIZATION_EXTRA_WEIGHTS: dict[str, float] = {
    "diplomacy_boundary": 0.024,
    "treaty_integrity": 0.024,
    "federation_stability": 0.022,
    "non_interference": 0.022,
    "provenance_exchange": 0.022,
    "sovereignty_alignment": 0.021,
}


@dataclass
class CognitiveCivilizationAttentionEvidence(ExternalRuntimeAttentionEvidence):
    diplomacy_boundary_rate: float = 1.0
    treaty_integrity_rate: float = 1.0
    federation_stability_rate: float = 1.0
    non_interference_rate: float = 1.0
    provenance_exchange_rate: float = 1.0
    sovereignty_alignment_rate: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        base = super().to_dict()
        base.update({
            "diplomacy_boundary_rate": round(self.diplomacy_boundary_rate, 4),
            "treaty_integrity_rate": round(self.treaty_integrity_rate, 4),
            "federation_stability_rate": round(self.federation_stability_rate, 4),
            "non_interference_rate": round(self.non_interference_rate, 4),
            "provenance_exchange_rate": round(self.provenance_exchange_rate, 4),
            "sovereignty_alignment_rate": round(self.sovereignty_alignment_rate, 4),
        })
        return base


@dataclass
class CognitiveCivilizationStabilityScore(ExternalRuntimeGovernanceScore):
    civilization_dimensions: dict[str, float] = field(default_factory=dict)
    civilization_score: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        base = super().to_dict()
        base["civilization_dimensions"] = {
            k: round(v, 4) for k, v in self.civilization_dimensions.items()
        }
        base["civilization_score"] = round(self.civilization_score, 4)
        return base


def evidence_from_civilization_forecaster(
    forecaster: AttentionForecast,
    *,
    bridge: RuntimeAttentionMemoryBridge | None = None,
    target_id: str = "civilization-gate-target",
    submissions: int = 0,
) -> CognitiveCivilizationAttentionEvidence:
    base = evidence_from_runtime_forecaster(
        forecaster, bridge=bridge, target_id=target_id, submissions=submissions
    )
    dip = collect_diplomacy_boundary_metrics()
    treaty = collect_treaty_integrity_metrics()
    fed = collect_federation_stability_metrics()
    ni = collect_non_interference_metrics()
    pe = collect_provenance_exchange_metrics()
    align = collect_sovereignty_alignment_metrics()
    return CognitiveCivilizationAttentionEvidence(
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
        diplomacy_boundary_rate=dip.boundary_rate,
        treaty_integrity_rate=treaty.integrity_rate,
        federation_stability_rate=fed.stability_rate,
        non_interference_rate=ni.respect_rate,
        provenance_exchange_rate=pe.exchange_rate,
        sovereignty_alignment_rate=align.alignment_rate,
    )


def evaluate_cognitive_civilization_stability(
    evidence: CognitiveCivilizationAttentionEvidence | None = None,
    *,
    forecaster: AttentionForecast | None = None,
    bridge: RuntimeAttentionMemoryBridge | None = None,
    kernel: AttentionKernel | None = None,
) -> CognitiveCivilizationStabilityScore:
    if evidence is None:
        fc = forecaster or AttentionForecast(kernel=kernel)
        evidence = evidence_from_civilization_forecaster(fc, bridge=bridge)

    runtime_report = evaluate_external_runtime_governance(evidence, forecaster=forecaster, bridge=bridge)

    civ_dims = {
        "diplomacy_boundary": clamp01(evidence.diplomacy_boundary_rate),
        "treaty_integrity": clamp01(evidence.treaty_integrity_rate),
        "federation_stability": clamp01(evidence.federation_stability_rate),
        "non_interference": clamp01(evidence.non_interference_rate),
        "provenance_exchange": clamp01(evidence.provenance_exchange_rate),
        "sovereignty_alignment": clamp01(evidence.sovereignty_alignment_rate),
    }
    civ_bonus = sum(civ_dims[k] * CIVILIZATION_EXTRA_WEIGHTS[k] for k in CIVILIZATION_EXTRA_WEIGHTS)
    combined = clamp01(
        runtime_report.external_runtime_score * CIVILIZATION_PARENT_RETENTION + civ_bonus
    )

    hard_failures = list(runtime_report.hard_failures)
    if evidence.diplomacy_boundary_rate < 0.5:
        hard_failures.append("diplomacy_boundary_failed")
    if evidence.non_interference_rate < 0.5:
        hard_failures.append("non_interference_failed")
    if not evidence.guardian_supremacy_preserved:
        hard_failures.append("guardian_supremacy_at_risk")

    gate_pass = (
        combined >= CIVILIZATION_GATE_THRESHOLD
        and runtime_report.gate_pass
        and len(hard_failures) == 0
    )

    classification = (
        "production_grade_cognitive_civilization"
        if combined >= 0.95
        else "stable_cognitive_civilization"
        if combined >= CIVILIZATION_GATE_THRESHOLD
        else "restricted_cognitive_civilization"
    )

    return CognitiveCivilizationStabilityScore(
        score=combined,
        classification=classification,
        dimensions=runtime_report.dimensions,
        gate_pass=gate_pass,
        gate_threshold=CIVILIZATION_GATE_THRESHOLD,
        evidence=evidence,
        hard_failures=hard_failures,
        runtime_dimensions=runtime_report.runtime_dimensions,
        runtime_score=runtime_report.runtime_score,
        memory_dimensions=runtime_report.memory_dimensions,
        memory_score=runtime_report.memory_score,
        forecast_dimensions=runtime_report.forecast_dimensions,
        forecast_score=runtime_report.forecast_score,
        calibration_dimensions=runtime_report.calibration_dimensions,
        calibration_score=runtime_report.calibration_score,
        governance_dimensions=runtime_report.governance_dimensions,
        governance_score=runtime_report.governance_score,
        constitutional_dimensions=runtime_report.constitutional_dimensions,
        constitutional_score=runtime_report.constitutional_score,
        identity_dimensions=runtime_report.identity_dimensions,
        identity_score=runtime_report.identity_score,
        coherence_dimensions=runtime_report.coherence_dimensions,
        coherence_score=runtime_report.coherence_score,
        metacognitive_dimensions=runtime_report.metacognitive_dimensions,
        metacognition_score=runtime_report.metacognition_score,
        homeostasis_dimensions=runtime_report.homeostasis_dimensions,
        homeostasis_score=runtime_report.homeostasis_score,
        external_dimensions=runtime_report.external_dimensions,
        external_skill_score=runtime_report.external_skill_score,
        external_runtime_dimensions=runtime_report.external_runtime_dimensions,
        external_runtime_score=runtime_report.external_runtime_score,
        civilization_dimensions=civ_dims,
        civilization_score=combined,
    )
