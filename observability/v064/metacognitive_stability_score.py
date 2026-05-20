"""v0.6.4 Meta-Cognitive Stability Score — gate threshold 0.90."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from attention.forecasting.attention_forecast import AttentionForecast
from attention.kernel.attention_kernel import AttentionKernel
from attention.runtime.runtime_attention_memory_bridge import RuntimeAttentionMemoryBridge
from observability.v04.metric_normalizer import clamp01
from observability.v063.cognitive_coherence_stability_score import (
    CognitiveCoherenceAttentionEvidence,
    CognitiveCoherenceStabilityReport,
    evaluate_cognitive_coherence_stability,
    evidence_from_coherence_forecaster,
)
from observability.v064.attention_pathology_metrics import (
    collect_attention_pathology_metrics,
)
from observability.v064.calibration_reflection_metrics import (
    collect_calibration_reflection_metrics,
)
from observability.v064.cognition_quality_metrics import collect_cognition_quality_metrics
from observability.v064.degradation_metrics import collect_degradation_metrics
from observability.v064.reflection_boundary_metrics import (
    collect_reflection_boundary_metrics,
)

METACOGNITIVE_GATE_THRESHOLD = 0.90

METACOGNITIVE_EXTRA_WEIGHTS: dict[str, float] = {
    "cognition_quality": 0.032,
    "degradation_containment": 0.032,
    "pathology_containment": 0.028,
    "reflection_boundary_compliance": 0.028,
    "calibration_reflection_bounded": 0.028,
    "metacognitive_explainability": 0.022,
}


@dataclass
class MetaCognitiveAttentionEvidence(CognitiveCoherenceAttentionEvidence):
    cognition_quality_rate: float = 1.0
    degradation_containment_rate: float = 1.0
    pathology_containment_rate: float = 1.0
    reflection_boundary_compliance_rate: float = 1.0
    calibration_reflection_bounded_rate: float = 1.0
    metacognitive_explainability_rate: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        base = super().to_dict()
        base.update({
            "cognition_quality_rate": round(self.cognition_quality_rate, 4),
            "degradation_containment_rate": round(
                self.degradation_containment_rate, 4
            ),
            "pathology_containment_rate": round(self.pathology_containment_rate, 4),
            "reflection_boundary_compliance_rate": round(
                self.reflection_boundary_compliance_rate, 4
            ),
            "calibration_reflection_bounded_rate": round(
                self.calibration_reflection_bounded_rate, 4
            ),
            "metacognitive_explainability_rate": round(
                self.metacognitive_explainability_rate, 4
            ),
        })
        return base


@dataclass
class MetaCognitiveStabilityReport(CognitiveCoherenceStabilityReport):
    metacognitive_dimensions: dict[str, float] = field(default_factory=dict)
    metacognition_score: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        base = super().to_dict()
        base["metacognitive_dimensions"] = {
            k: round(v, 4) for k, v in self.metacognitive_dimensions.items()
        }
        base["metacognition_score"] = round(self.metacognition_score, 4)
        return base


def evidence_from_metacognitive_forecaster(
    forecaster: AttentionForecast,
    *,
    bridge: RuntimeAttentionMemoryBridge | None = None,
    target_id: str = "metacognitive-gate-target",
    submissions: int = 0,
) -> MetaCognitiveAttentionEvidence:
    base = evidence_from_coherence_forecaster(
        forecaster, bridge=bridge, target_id=target_id, submissions=submissions
    )
    quality = collect_cognition_quality_metrics()
    deg = collect_degradation_metrics()
    path = collect_attention_pathology_metrics()
    boundary = collect_reflection_boundary_metrics()
    cal = collect_calibration_reflection_metrics()
    return MetaCognitiveAttentionEvidence(
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
        cognition_quality_rate=quality.quality_rate,
        degradation_containment_rate=deg.containment_rate,
        pathology_containment_rate=path.containment_rate,
        reflection_boundary_compliance_rate=boundary.compliance_rate,
        calibration_reflection_bounded_rate=cal.bounded_rate,
        metacognitive_explainability_rate=base.explainability_coverage,
    )


def compute_metacognitive_stability(
    evidence: MetaCognitiveAttentionEvidence | None = None,
    *,
    forecaster: AttentionForecast | None = None,
    bridge: RuntimeAttentionMemoryBridge | None = None,
    kernel: AttentionKernel | None = None,
) -> MetaCognitiveStabilityReport:
    if evidence is None:
        fc = forecaster or AttentionForecast(kernel=kernel)
        evidence = evidence_from_metacognitive_forecaster(fc, bridge=bridge)

    coherence_report = evaluate_cognitive_coherence_stability(
        evidence, forecaster=forecaster, bridge=bridge
    )

    meta_dims = {
        "cognition_quality": clamp01(evidence.cognition_quality_rate),
        "degradation_containment": clamp01(evidence.degradation_containment_rate),
        "pathology_containment": clamp01(evidence.pathology_containment_rate),
        "reflection_boundary_compliance": clamp01(
            evidence.reflection_boundary_compliance_rate
        ),
        "calibration_reflection_bounded": clamp01(
            evidence.calibration_reflection_bounded_rate
        ),
        "metacognitive_explainability": clamp01(
            evidence.metacognitive_explainability_rate
        ),
    }
    meta_bonus = sum(
        meta_dims[k] * METACOGNITIVE_EXTRA_WEIGHTS[k]
        for k in METACOGNITIVE_EXTRA_WEIGHTS
    )
    combined = clamp01(coherence_report.coherence_score * 0.80 + meta_bonus)

    hard_failures = list(coherence_report.hard_failures)
    if evidence.cognition_quality_rate < 0.5:
        hard_failures.append("cognition_quality_low")
    if evidence.degradation_containment_rate < 0.5:
        hard_failures.append("degradation_uncontained")
    if evidence.pathology_containment_rate < 0.5:
        hard_failures.append("attention_pathology_high")

    gate_pass = (
        combined >= METACOGNITIVE_GATE_THRESHOLD
        and coherence_report.gate_pass
        and len(hard_failures) == 0
    )

    classification = (
        "production_grade_metacognitive_reflection"
        if combined >= 0.95
        else "stable_metacognitive_layer"
        if combined >= METACOGNITIVE_GATE_THRESHOLD
        else "usable_metacognitive_continuity"
        if combined >= 0.80
        else "unstable_metacognition"
    )

    return MetaCognitiveStabilityReport(
        score=combined,
        classification=classification,
        dimensions=coherence_report.dimensions,
        gate_pass=gate_pass,
        gate_threshold=METACOGNITIVE_GATE_THRESHOLD,
        evidence=evidence,
        hard_failures=hard_failures,
        runtime_dimensions=coherence_report.runtime_dimensions,
        runtime_score=coherence_report.runtime_score,
        memory_dimensions=coherence_report.memory_dimensions,
        memory_score=coherence_report.memory_score,
        forecast_dimensions=coherence_report.forecast_dimensions,
        forecast_score=coherence_report.forecast_score,
        calibration_dimensions=coherence_report.calibration_dimensions,
        calibration_score=coherence_report.calibration_score,
        governance_dimensions=coherence_report.governance_dimensions,
        governance_score=coherence_report.governance_score,
        constitutional_dimensions=coherence_report.constitutional_dimensions,
        constitutional_score=coherence_report.constitutional_score,
        identity_dimensions=coherence_report.identity_dimensions,
        identity_score=coherence_report.identity_score,
        coherence_dimensions=coherence_report.coherence_dimensions,
        coherence_score=coherence_report.coherence_score,
        metacognitive_dimensions=meta_dims,
        metacognition_score=combined,
    )


def evaluate_metacognitive_stability(
    evidence: MetaCognitiveAttentionEvidence | None = None,
    *,
    forecaster: AttentionForecast | None = None,
    bridge: RuntimeAttentionMemoryBridge | None = None,
    kernel: AttentionKernel | None = None,
    **kwargs: Any,
) -> MetaCognitiveStabilityReport:
    if evidence is None and kwargs:
        evidence = MetaCognitiveAttentionEvidence(**kwargs)
    return compute_metacognitive_stability(
        evidence, forecaster=forecaster, bridge=bridge, kernel=kernel
    )


MetaCognitiveStabilityScore = MetaCognitiveStabilityReport
