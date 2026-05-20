"""v0.6.3 Cognitive Coherence Stability Score — gate threshold 0.90."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from attention.forecasting.attention_forecast import AttentionForecast
from attention.kernel.attention_kernel import AttentionKernel
from attention.runtime.runtime_attention_memory_bridge import RuntimeAttentionMemoryBridge
from observability.v04.metric_normalizer import clamp01
from observability.v062.cognitive_identity_stability_score import (
    CognitiveIdentityAttentionEvidence,
    CognitiveIdentityStabilityReport,
    evaluate_cognitive_identity_stability,
    evidence_from_identity_forecaster,
)
from observability.v063.constitutional_coherence_metrics import (
    collect_constitutional_coherence_metrics,
)
from observability.v063.contradiction_metrics import collect_contradiction_metrics
from observability.v063.drift_metrics import collect_drift_metrics
from observability.v063.fragmentation_pressure_metrics import (
    collect_fragmentation_pressure_metrics,
)
from observability.v063.replay_coherence_metrics import collect_replay_coherence_metrics

COGNITIVE_COHERENCE_GATE_THRESHOLD = 0.90

COHERENCE_EXTRA_WEIGHTS: dict[str, float] = {
    "contradiction_resistance": 0.03,
    "replay_coherence": 0.03,
    "constitutional_alignment": 0.03,
    "drift_bounded": 0.025,
    "fragmentation_containment": 0.025,
    "coherence_explainability": 0.02,
}


@dataclass
class CognitiveCoherenceAttentionEvidence(CognitiveIdentityAttentionEvidence):
    contradiction_resistance_rate: float = 1.0
    replay_coherence_rate: float = 1.0
    constitutional_alignment_rate: float = 1.0
    drift_bounded_rate: float = 1.0
    fragmentation_containment_rate: float = 1.0
    coherence_explainability_rate: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        base = super().to_dict()
        base.update({
            "contradiction_resistance_rate": round(
                self.contradiction_resistance_rate, 4
            ),
            "replay_coherence_rate": round(self.replay_coherence_rate, 4),
            "constitutional_alignment_rate": round(
                self.constitutional_alignment_rate, 4
            ),
            "drift_bounded_rate": round(self.drift_bounded_rate, 4),
            "fragmentation_containment_rate": round(
                self.fragmentation_containment_rate, 4
            ),
            "coherence_explainability_rate": round(
                self.coherence_explainability_rate, 4
            ),
        })
        return base


@dataclass
class CognitiveCoherenceStabilityReport(CognitiveIdentityStabilityReport):
    coherence_dimensions: dict[str, float] = field(default_factory=dict)
    coherence_score: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        base = super().to_dict()
        base["coherence_dimensions"] = {
            k: round(v, 4) for k, v in self.coherence_dimensions.items()
        }
        base["coherence_score"] = round(self.coherence_score, 4)
        return base


def evidence_from_coherence_forecaster(
    forecaster: AttentionForecast,
    *,
    bridge: RuntimeAttentionMemoryBridge | None = None,
    target_id: str = "coherence-gate-target",
    submissions: int = 0,
) -> CognitiveCoherenceAttentionEvidence:
    base = evidence_from_identity_forecaster(
        forecaster, bridge=bridge, target_id=target_id, submissions=submissions
    )
    contra = collect_contradiction_metrics()
    replay = collect_replay_coherence_metrics()
    const = collect_constitutional_coherence_metrics()
    drift = collect_drift_metrics()
    frag = collect_fragmentation_pressure_metrics()
    return CognitiveCoherenceAttentionEvidence(
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
        contradiction_resistance_rate=contra.resistance_rate,
        replay_coherence_rate=replay.coherence_rate,
        constitutional_alignment_rate=const.alignment_rate,
        drift_bounded_rate=drift.bounded_rate,
        fragmentation_containment_rate=frag.containment_rate,
        coherence_explainability_rate=base.explainability_coverage,
    )


def compute_cognitive_coherence_stability(
    evidence: CognitiveCoherenceAttentionEvidence | None = None,
    *,
    forecaster: AttentionForecast | None = None,
    bridge: RuntimeAttentionMemoryBridge | None = None,
    kernel: AttentionKernel | None = None,
) -> CognitiveCoherenceStabilityReport:
    if evidence is None:
        fc = forecaster or AttentionForecast(kernel=kernel)
        evidence = evidence_from_coherence_forecaster(fc, bridge=bridge)

    identity_report = evaluate_cognitive_identity_stability(
        evidence, forecaster=forecaster, bridge=bridge
    )

    coherence_dims = {
        "contradiction_resistance": clamp01(evidence.contradiction_resistance_rate),
        "replay_coherence": clamp01(evidence.replay_coherence_rate),
        "constitutional_alignment": clamp01(evidence.constitutional_alignment_rate),
        "drift_bounded": clamp01(evidence.drift_bounded_rate),
        "fragmentation_containment": clamp01(evidence.fragmentation_containment_rate),
        "coherence_explainability": clamp01(evidence.coherence_explainability_rate),
    }
    coherence_bonus = sum(
        coherence_dims[k] * COHERENCE_EXTRA_WEIGHTS[k] for k in COHERENCE_EXTRA_WEIGHTS
    )
    combined = clamp01(identity_report.identity_score * 0.80 + coherence_bonus)

    hard_failures = list(identity_report.hard_failures)
    if evidence.contradiction_resistance_rate < 0.5:
        hard_failures.append("contradiction_resistance_low")
    if evidence.replay_coherence_rate < 0.5:
        hard_failures.append("replay_coherence_low")
    if evidence.drift_bounded_rate < 0.5:
        hard_failures.append("identity_drift_unbounded")

    gate_pass = (
        combined >= COGNITIVE_COHERENCE_GATE_THRESHOLD
        and identity_report.gate_pass
        and len(hard_failures) == 0
    )

    classification = (
        "production_grade_cognitive_coherence"
        if combined >= 0.95
        else "stable_coherence_layer"
        if combined >= COGNITIVE_COHERENCE_GATE_THRESHOLD
        else "usable_coherence_continuity"
        if combined >= 0.80
        else "unstable_cognition_coherence"
    )

    return CognitiveCoherenceStabilityReport(
        score=combined,
        classification=classification,
        dimensions=identity_report.dimensions,
        gate_pass=gate_pass,
        gate_threshold=COGNITIVE_COHERENCE_GATE_THRESHOLD,
        evidence=evidence,
        hard_failures=hard_failures,
        runtime_dimensions=identity_report.runtime_dimensions,
        runtime_score=identity_report.runtime_score,
        memory_dimensions=identity_report.memory_dimensions,
        memory_score=identity_report.memory_score,
        forecast_dimensions=identity_report.forecast_dimensions,
        forecast_score=identity_report.forecast_score,
        calibration_dimensions=identity_report.calibration_dimensions,
        calibration_score=identity_report.calibration_score,
        governance_dimensions=identity_report.governance_dimensions,
        governance_score=identity_report.governance_score,
        constitutional_dimensions=identity_report.constitutional_dimensions,
        constitutional_score=identity_report.constitutional_score,
        identity_dimensions=identity_report.identity_dimensions,
        identity_score=identity_report.identity_score,
        coherence_dimensions=coherence_dims,
        coherence_score=combined,
    )


def evaluate_cognitive_coherence_stability(
    evidence: CognitiveCoherenceAttentionEvidence | None = None,
    *,
    forecaster: AttentionForecast | None = None,
    bridge: RuntimeAttentionMemoryBridge | None = None,
    kernel: AttentionKernel | None = None,
    **kwargs: Any,
) -> CognitiveCoherenceStabilityReport:
    if evidence is None and kwargs:
        evidence = CognitiveCoherenceAttentionEvidence(**kwargs)
    return compute_cognitive_coherence_stability(
        evidence, forecaster=forecaster, bridge=bridge, kernel=kernel
    )


CognitiveCoherenceStabilityScore = CognitiveCoherenceStabilityReport
