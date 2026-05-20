"""v0.6.5 Cognitive Homeostasis Stability Score — gate threshold 0.90."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from attention.forecasting.attention_forecast import AttentionForecast
from attention.kernel.attention_kernel import AttentionKernel
from attention.runtime.runtime_attention_memory_bridge import RuntimeAttentionMemoryBridge
from observability.v04.metric_normalizer import clamp01
from observability.v064.metacognitive_stability_score import (
    MetaCognitiveAttentionEvidence,
    MetaCognitiveStabilityReport,
    evaluate_metacognitive_stability,
    evidence_from_metacognitive_forecaster,
)
from observability.v065.calibration_recovery_metrics import (
    collect_calibration_recovery_metrics,
)
from observability.v065.coherence_recovery_metrics import collect_coherence_recovery_metrics
from observability.v065.reflection_balance_metrics import collect_reflection_balance_metrics
from observability.v065.salience_damping_metrics import collect_salience_damping_metrics
from observability.v065.stabilization_metrics import collect_stabilization_metrics

COGNITIVE_HOMEOSTASIS_GATE_THRESHOLD = 0.90

HOMEOSTASIS_EXTRA_WEIGHTS: dict[str, float] = {
    "stabilization_containment": 0.034,
    "salience_damping_containment": 0.034,
    "coherence_recovery_ready": 0.030,
    "reflection_balance": 0.030,
    "calibration_recovery_bounded": 0.030,
    "homeostasis_explainability": 0.025,
}


@dataclass
class CognitiveHomeostasisAttentionEvidence(MetaCognitiveAttentionEvidence):
    stabilization_containment_rate: float = 1.0
    salience_damping_containment_rate: float = 1.0
    coherence_recovery_ready_rate: float = 1.0
    reflection_balance_rate: float = 1.0
    calibration_recovery_bounded_rate: float = 1.0
    homeostasis_explainability_rate: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        base = super().to_dict()
        base.update({
            "stabilization_containment_rate": round(
                self.stabilization_containment_rate, 4
            ),
            "salience_damping_containment_rate": round(
                self.salience_damping_containment_rate, 4
            ),
            "coherence_recovery_ready_rate": round(
                self.coherence_recovery_ready_rate, 4
            ),
            "reflection_balance_rate": round(self.reflection_balance_rate, 4),
            "calibration_recovery_bounded_rate": round(
                self.calibration_recovery_bounded_rate, 4
            ),
            "homeostasis_explainability_rate": round(
                self.homeostasis_explainability_rate, 4
            ),
        })
        return base


@dataclass
class CognitiveHomeostasisStabilityReport(MetaCognitiveStabilityReport):
    homeostasis_dimensions: dict[str, float] = field(default_factory=dict)
    homeostasis_score: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        base = super().to_dict()
        base["homeostasis_dimensions"] = {
            k: round(v, 4) for k, v in self.homeostasis_dimensions.items()
        }
        base["homeostasis_score"] = round(self.homeostasis_score, 4)
        return base


def evidence_from_homeostasis_forecaster(
    forecaster: AttentionForecast,
    *,
    bridge: RuntimeAttentionMemoryBridge | None = None,
    target_id: str = "homeostasis-gate-target",
    submissions: int = 0,
) -> CognitiveHomeostasisAttentionEvidence:
    base = evidence_from_metacognitive_forecaster(
        forecaster, bridge=bridge, target_id=target_id, submissions=submissions
    )
    stab = collect_stabilization_metrics()
    damp = collect_salience_damping_metrics()
    coh = collect_coherence_recovery_metrics()
    refl = collect_reflection_balance_metrics()
    cal = collect_calibration_recovery_metrics()
    return CognitiveHomeostasisAttentionEvidence(
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
        provenance_integrity_rate=base.provenance_integrity_rate,
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
        stabilization_containment_rate=stab.containment_rate,
        salience_damping_containment_rate=damp.containment_rate,
        coherence_recovery_ready_rate=coh.recovery_ready_rate,
        reflection_balance_rate=refl.balance_rate,
        calibration_recovery_bounded_rate=cal.bounded_rate,
        homeostasis_explainability_rate=base.explainability_coverage,
    )


def compute_cognitive_homeostasis_stability(
    evidence: CognitiveHomeostasisAttentionEvidence | None = None,
    *,
    forecaster: AttentionForecast | None = None,
    bridge: RuntimeAttentionMemoryBridge | None = None,
    kernel: AttentionKernel | None = None,
) -> CognitiveHomeostasisStabilityReport:
    if evidence is None:
        fc = forecaster or AttentionForecast(kernel=kernel)
        evidence = evidence_from_homeostasis_forecaster(fc, bridge=bridge)

    meta_report = evaluate_metacognitive_stability(
        evidence, forecaster=forecaster, bridge=bridge
    )

    homeo_dims = {
        "stabilization_containment": clamp01(evidence.stabilization_containment_rate),
        "salience_damping_containment": clamp01(
            evidence.salience_damping_containment_rate
        ),
        "coherence_recovery_ready": clamp01(evidence.coherence_recovery_ready_rate),
        "reflection_balance": clamp01(evidence.reflection_balance_rate),
        "calibration_recovery_bounded": clamp01(
            evidence.calibration_recovery_bounded_rate
        ),
        "homeostasis_explainability": clamp01(evidence.homeostasis_explainability_rate),
    }
    homeo_bonus = sum(
        homeo_dims[k] * HOMEOSTASIS_EXTRA_WEIGHTS[k] for k in HOMEOSTASIS_EXTRA_WEIGHTS
    )
    combined = clamp01(meta_report.metacognition_score * 0.80 + homeo_bonus)

    hard_failures = list(meta_report.hard_failures)
    if evidence.stabilization_containment_rate < 0.5:
        hard_failures.append("stabilization_uncontained")
    if evidence.salience_damping_containment_rate < 0.5:
        hard_failures.append("salience_oscillation_high")
    if evidence.coherence_recovery_ready_rate < 0.5:
        hard_failures.append("coherence_recovery_unready")

    gate_pass = (
        combined >= COGNITIVE_HOMEOSTASIS_GATE_THRESHOLD
        and meta_report.gate_pass
        and len(hard_failures) == 0
    )

    classification = (
        "production_grade_cognitive_homeostasis"
        if combined >= 0.95
        else "stable_homeostatic_layer"
        if combined >= COGNITIVE_HOMEOSTASIS_GATE_THRESHOLD
        else "usable_homeostatic_continuity"
        if combined >= 0.80
        else "unstable_homeostasis"
    )

    return CognitiveHomeostasisStabilityReport(
        score=combined,
        classification=classification,
        dimensions=meta_report.dimensions,
        gate_pass=gate_pass,
        gate_threshold=COGNITIVE_HOMEOSTASIS_GATE_THRESHOLD,
        evidence=evidence,
        hard_failures=hard_failures,
        runtime_dimensions=meta_report.runtime_dimensions,
        runtime_score=meta_report.runtime_score,
        memory_dimensions=meta_report.memory_dimensions,
        memory_score=meta_report.memory_score,
        forecast_dimensions=meta_report.forecast_dimensions,
        forecast_score=meta_report.forecast_score,
        calibration_dimensions=meta_report.calibration_dimensions,
        calibration_score=meta_report.calibration_score,
        governance_dimensions=meta_report.governance_dimensions,
        governance_score=meta_report.governance_score,
        constitutional_dimensions=meta_report.constitutional_dimensions,
        constitutional_score=meta_report.constitutional_score,
        identity_dimensions=meta_report.identity_dimensions,
        identity_score=meta_report.identity_score,
        coherence_dimensions=meta_report.coherence_dimensions,
        coherence_score=meta_report.coherence_score,
        metacognitive_dimensions=meta_report.metacognitive_dimensions,
        metacognition_score=meta_report.metacognition_score,
        homeostasis_dimensions=homeo_dims,
        homeostasis_score=combined,
    )


def evaluate_cognitive_homeostasis_stability(
    evidence: CognitiveHomeostasisAttentionEvidence | None = None,
    *,
    forecaster: AttentionForecast | None = None,
    bridge: RuntimeAttentionMemoryBridge | None = None,
    kernel: AttentionKernel | None = None,
    **kwargs: Any,
) -> CognitiveHomeostasisStabilityReport:
    if evidence is None and kwargs:
        evidence = CognitiveHomeostasisAttentionEvidence(**kwargs)
    return compute_cognitive_homeostasis_stability(
        evidence, forecaster=forecaster, bridge=bridge, kernel=kernel
    )


CognitiveHomeostasisStabilityScore = CognitiveHomeostasisStabilityReport
