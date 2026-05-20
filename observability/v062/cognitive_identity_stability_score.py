"""v0.6.2 Cognitive Identity Stability Score — gate threshold 0.90."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from attention.forecasting.attention_forecast import AttentionForecast
from attention.kernel.attention_kernel import AttentionKernel
from attention.runtime.runtime_attention_memory_bridge import RuntimeAttentionMemoryBridge
from observability.v04.metric_normalizer import clamp01
from observability.v061.constitutional_stability_score import (
    CONSTITUTIONAL_GATE_THRESHOLD,
    ConstitutionalAttentionEvidence,
    ConstitutionalStabilityReport,
    evaluate_constitutional_stability,
    evidence_from_constitutional_forecaster,
)
from observability.v062.cognition_trust_metrics import collect_cognition_trust_metrics
from observability.v062.continuity_metrics import collect_continuity_metrics
from observability.v062.fragmentation_metrics import collect_fragmentation_metrics
from observability.v062.identity_coherence_metrics import collect_identity_coherence_metrics
from observability.v062.provenance_metrics import collect_provenance_metrics

COGNITIVE_IDENTITY_GATE_THRESHOLD = 0.90

IDENTITY_EXTRA_WEIGHTS: dict[str, float] = {
    "provenance_integrity": 0.035,
    "cognition_trust": 0.03,
    "replay_identity_bounded": 0.03,
    "fragmentation_resistance": 0.025,
    "continuity_stability": 0.025,
    "synthetic_containment": 0.025,
    "identity_coherence": 0.025,
    "explainability": 0.02,
}


@dataclass
class CognitiveIdentityAttentionEvidence(ConstitutionalAttentionEvidence):
    provenance_integrity_rate: float = 1.0
    cognition_trust_rate: float = 1.0
    replay_identity_bounded_rate: float = 1.0
    fragmentation_resistance_rate: float = 1.0
    continuity_stability_rate: float = 1.0
    synthetic_containment_rate: float = 1.0
    identity_coherence_rate: float = 1.0
    identity_explainability_rate: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        base = super().to_dict()
        base.update({
            "provenance_integrity_rate": round(self.provenance_integrity_rate, 4),
            "cognition_trust_rate": round(self.cognition_trust_rate, 4),
            "replay_identity_bounded_rate": round(self.replay_identity_bounded_rate, 4),
            "fragmentation_resistance_rate": round(self.fragmentation_resistance_rate, 4),
            "continuity_stability_rate": round(self.continuity_stability_rate, 4),
            "synthetic_containment_rate": round(self.synthetic_containment_rate, 4),
            "identity_coherence_rate": round(self.identity_coherence_rate, 4),
            "identity_explainability_rate": round(self.identity_explainability_rate, 4),
        })
        return base


@dataclass
class CognitiveIdentityStabilityReport(ConstitutionalStabilityReport):
    identity_dimensions: dict[str, float] = field(default_factory=dict)
    identity_score: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        base = super().to_dict()
        base["identity_dimensions"] = {
            k: round(v, 4) for k, v in self.identity_dimensions.items()
        }
        base["identity_score"] = round(self.identity_score, 4)
        return base


def evidence_from_identity_forecaster(
    forecaster: AttentionForecast,
    *,
    bridge: RuntimeAttentionMemoryBridge | None = None,
    target_id: str = "identity-gate-target",
    submissions: int = 0,
) -> CognitiveIdentityAttentionEvidence:
    base = evidence_from_constitutional_forecaster(
        forecaster, bridge=bridge, target_id=target_id, submissions=submissions
    )
    prov = collect_provenance_metrics()
    trust = collect_cognition_trust_metrics()
    coh = collect_identity_coherence_metrics()
    frag = collect_fragmentation_metrics()
    cont = collect_continuity_metrics()
    return CognitiveIdentityAttentionEvidence(
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
        provenance_integrity_rate=prov.integrity_rate,
        cognition_trust_rate=trust.trust_rate,
        replay_identity_bounded_rate=base.replay_bounded_rate,
        fragmentation_resistance_rate=frag.resistance_rate,
        continuity_stability_rate=cont.anchor_stability_rate,
        synthetic_containment_rate=0.95,
        identity_coherence_rate=coh.coherence_rate,
        identity_explainability_rate=base.explainability_coverage,
    )


def compute_cognitive_identity_stability(
    evidence: CognitiveIdentityAttentionEvidence | None = None,
    *,
    forecaster: AttentionForecast | None = None,
    bridge: RuntimeAttentionMemoryBridge | None = None,
    kernel: AttentionKernel | None = None,
) -> CognitiveIdentityStabilityReport:
    if evidence is None:
        fc = forecaster or AttentionForecast(kernel=kernel)
        evidence = evidence_from_identity_forecaster(fc, bridge=bridge)

    const_report = evaluate_constitutional_stability(
        evidence, forecaster=forecaster, bridge=bridge
    )

    identity_dims = {
        "provenance_integrity": clamp01(evidence.provenance_integrity_rate),
        "cognition_trust": clamp01(evidence.cognition_trust_rate),
        "replay_identity_bounded": clamp01(evidence.replay_identity_bounded_rate),
        "fragmentation_resistance": clamp01(evidence.fragmentation_resistance_rate),
        "continuity_stability": clamp01(evidence.continuity_stability_rate),
        "synthetic_containment": clamp01(evidence.synthetic_containment_rate),
        "identity_coherence": clamp01(evidence.identity_coherence_rate),
        "explainability": clamp01(evidence.identity_explainability_rate),
    }
    identity_bonus = sum(
        identity_dims[k] * IDENTITY_EXTRA_WEIGHTS[k] for k in IDENTITY_EXTRA_WEIGHTS
    )
    combined = clamp01(const_report.constitutional_score * 0.82 + identity_bonus)

    hard_failures = list(const_report.hard_failures)
    if evidence.provenance_integrity_rate < 0.5:
        hard_failures.append("provenance_integrity_low")
    if evidence.fragmentation_resistance_rate < 0.5:
        hard_failures.append("fragmentation_resistance_low")
    if evidence.continuity_stability_rate < 0.5:
        hard_failures.append("continuity_unstable")

    gate_pass = (
        combined >= COGNITIVE_IDENTITY_GATE_THRESHOLD
        and const_report.gate_pass
        and len(hard_failures) == 0
    )

    classification = (
        "production_grade_cognitive_identity"
        if combined >= 0.95
        else "stable_identity_layer"
        if combined >= COGNITIVE_IDENTITY_GATE_THRESHOLD
        else "usable_identity_continuity"
        if combined >= 0.80
        else "unstable_cognition_identity"
    )

    return CognitiveIdentityStabilityReport(
        score=combined,
        classification=classification,
        dimensions=const_report.dimensions,
        gate_pass=gate_pass,
        gate_threshold=COGNITIVE_IDENTITY_GATE_THRESHOLD,
        evidence=evidence,
        hard_failures=hard_failures,
        runtime_dimensions=const_report.runtime_dimensions,
        runtime_score=const_report.runtime_score,
        memory_dimensions=const_report.memory_dimensions,
        memory_score=const_report.memory_score,
        forecast_dimensions=const_report.forecast_dimensions,
        forecast_score=const_report.forecast_score,
        calibration_dimensions=const_report.calibration_dimensions,
        calibration_score=const_report.calibration_score,
        governance_dimensions=const_report.governance_dimensions,
        governance_score=const_report.governance_score,
        constitutional_dimensions=const_report.constitutional_dimensions,
        constitutional_score=const_report.constitutional_score,
        identity_dimensions=identity_dims,
        identity_score=combined,
    )


def evaluate_cognitive_identity_stability(
    evidence: CognitiveIdentityAttentionEvidence | None = None,
    *,
    forecaster: AttentionForecast | None = None,
    bridge: RuntimeAttentionMemoryBridge | None = None,
    kernel: AttentionKernel | None = None,
    **kwargs: Any,
) -> CognitiveIdentityStabilityReport:
    if evidence is None and kwargs:
        evidence = CognitiveIdentityAttentionEvidence(**kwargs)
    return compute_cognitive_identity_stability(
        evidence, forecaster=forecaster, bridge=bridge, kernel=kernel
    )


CognitiveIdentityStabilityScore = CognitiveIdentityStabilityReport
