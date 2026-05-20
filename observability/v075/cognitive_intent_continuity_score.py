"""v0.7.5 Cognitive Intent Continuity Score — gate threshold 0.90."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from attention.forecasting.attention_forecast import AttentionForecast
from attention.kernel.attention_kernel import AttentionKernel
from attention.runtime.runtime_attention_memory_bridge import RuntimeAttentionMemoryBridge
from observability.v04.metric_normalizer import clamp01
from observability.v074.cognitive_value_continuity_score import (
    VALUE_CONTINUITY_GATE_THRESHOLD,
    CognitiveValueContinuityAttentionEvidence,
    CognitiveValueContinuityScore,
    evaluate_cognitive_value_continuity,
    evidence_from_value_forecaster,
)
from observability.v075.intent_decay_metrics import collect_intent_decay_metrics
from observability.v075.intent_lineage_integrity_metrics import collect_intent_lineage_integrity_metrics
from observability.v075.intent_provenance_metrics import collect_intent_provenance_metrics
from observability.v075.motivational_boundary_metrics import collect_motivational_boundary_metrics
from observability.v075.motivational_drift_containment_metrics import (
    collect_motivational_drift_containment_metrics,
)
from observability.v075.motivational_integrity_metrics import collect_motivational_integrity_metrics

INTENT_CONTINUITY_GATE_THRESHOLD = 0.90

INTENT_EXTRA_WEIGHTS: dict[str, float] = {
    "motivational_drift_containment": 0.024,
    "motivational_boundary": 0.022,
    "intent_lineage_integrity": 0.022,
    "intent_decay": 0.022,
    "intent_provenance": 0.022,
    "motivational_integrity": 0.021,
}


@dataclass
class CognitiveIntentContinuityAttentionEvidence(CognitiveValueContinuityAttentionEvidence):
    motivational_drift_containment_rate: float = 1.0
    motivational_boundary_rate: float = 1.0
    intent_lineage_integrity_rate: float = 1.0
    intent_decay_rate: float = 1.0
    intent_provenance_rate: float = 1.0
    motivational_integrity_rate: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        base = super().to_dict()
        base.update({
            "motivational_drift_containment_rate": round(self.motivational_drift_containment_rate, 4),
            "motivational_boundary_rate": round(self.motivational_boundary_rate, 4),
            "intent_lineage_integrity_rate": round(self.intent_lineage_integrity_rate, 4),
            "intent_decay_rate": round(self.intent_decay_rate, 4),
            "intent_provenance_rate": round(self.intent_provenance_rate, 4),
            "motivational_integrity_rate": round(self.motivational_integrity_rate, 4),
        })
        return base


@dataclass
class CognitiveIntentContinuityScore(CognitiveValueContinuityScore):
    intent_dimensions: dict[str, float] = field(default_factory=dict)
    intent_continuity_score: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        base = super().to_dict()
        base["intent_dimensions"] = {k: round(v, 4) for k, v in self.intent_dimensions.items()}
        base["intent_continuity_score"] = round(self.intent_continuity_score, 4)
        return base


def evidence_from_intent_forecaster(
    forecaster: AttentionForecast,
    *,
    bridge: RuntimeAttentionMemoryBridge | None = None,
    target_id: str = "intent-gate-target",
    submissions: int = 0,
) -> CognitiveIntentContinuityAttentionEvidence:
    base = evidence_from_value_forecaster(
        forecaster, bridge=bridge, target_id=target_id, submissions=submissions
    )
    drift = collect_motivational_drift_containment_metrics()
    boundary = collect_motivational_boundary_metrics()
    lineage = collect_intent_lineage_integrity_metrics()
    decay = collect_intent_decay_metrics()
    prov = collect_intent_provenance_metrics()
    integrity = collect_motivational_integrity_metrics()
    return CognitiveIntentContinuityAttentionEvidence(
        **{k: getattr(base, k) for k in base.__dataclass_fields__},
        motivational_drift_containment_rate=drift.containment_rate,
        motivational_boundary_rate=boundary.boundary_rate,
        intent_lineage_integrity_rate=lineage.integrity_rate,
        intent_decay_rate=decay.decay_rate,
        intent_provenance_rate=prov.provenance_rate,
        motivational_integrity_rate=integrity.integrity_rate,
    )


def evaluate_cognitive_intent_continuity(
    evidence: CognitiveIntentContinuityAttentionEvidence | None = None,
    *,
    forecaster: AttentionForecast | None = None,
    bridge: RuntimeAttentionMemoryBridge | None = None,
    kernel: AttentionKernel | None = None,
) -> CognitiveIntentContinuityScore:
    if evidence is None:
        fc = forecaster or AttentionForecast(kernel=kernel)
        evidence = evidence_from_intent_forecaster(fc, bridge=bridge)

    value_report = evaluate_cognitive_value_continuity(evidence, forecaster=forecaster, bridge=bridge)

    intent_dims = {
        "motivational_drift_containment": clamp01(evidence.motivational_drift_containment_rate),
        "motivational_boundary": clamp01(evidence.motivational_boundary_rate),
        "intent_lineage_integrity": clamp01(evidence.intent_lineage_integrity_rate),
        "intent_decay": clamp01(evidence.intent_decay_rate),
        "intent_provenance": clamp01(evidence.intent_provenance_rate),
        "motivational_integrity": clamp01(evidence.motivational_integrity_rate),
    }
    intent_bonus = sum(intent_dims[k] * INTENT_EXTRA_WEIGHTS[k] for k in INTENT_EXTRA_WEIGHTS)
    combined = clamp01(value_report.value_continuity_score * 0.86 + intent_bonus)

    hard_failures = list(value_report.hard_failures)
    if evidence.motivational_drift_containment_rate < 0.5:
        hard_failures.append("motivational_drift_containment_failed")
    if evidence.motivational_boundary_rate < 0.5:
        hard_failures.append("motivational_boundary_failed")
    if not evidence.guardian_supremacy_preserved:
        hard_failures.append("guardian_supremacy_at_risk")

    gate_pass = (
        combined >= INTENT_CONTINUITY_GATE_THRESHOLD
        and value_report.gate_pass
        and len(hard_failures) == 0
    )

    classification = (
        "production_grade_cognitive_intent_continuity"
        if combined >= 0.95
        else "stable_cognitive_intent_continuity"
        if combined >= INTENT_CONTINUITY_GATE_THRESHOLD
        else "restricted_cognitive_intent_continuity"
    )

    return CognitiveIntentContinuityScore(
        score=combined,
        classification=classification,
        dimensions=value_report.dimensions,
        gate_pass=gate_pass,
        gate_threshold=INTENT_CONTINUITY_GATE_THRESHOLD,
        evidence=evidence,
        hard_failures=hard_failures,
        runtime_dimensions=value_report.runtime_dimensions,
        runtime_score=value_report.runtime_score,
        memory_dimensions=value_report.memory_dimensions,
        memory_score=value_report.memory_score,
        forecast_dimensions=value_report.forecast_dimensions,
        forecast_score=value_report.forecast_score,
        calibration_dimensions=value_report.calibration_dimensions,
        calibration_score=value_report.calibration_score,
        governance_dimensions=value_report.governance_dimensions,
        governance_score=value_report.governance_score,
        constitutional_dimensions=value_report.constitutional_dimensions,
        constitutional_score=value_report.constitutional_score,
        identity_dimensions=value_report.identity_dimensions,
        identity_score=value_report.identity_score,
        coherence_dimensions=value_report.coherence_dimensions,
        coherence_score=value_report.coherence_score,
        metacognitive_dimensions=value_report.metacognitive_dimensions,
        metacognition_score=value_report.metacognition_score,
        homeostasis_dimensions=value_report.homeostasis_dimensions,
        homeostasis_score=value_report.homeostasis_score,
        external_dimensions=value_report.external_dimensions,
        external_skill_score=value_report.external_skill_score,
        external_runtime_dimensions=value_report.external_runtime_dimensions,
        external_runtime_score=value_report.external_runtime_score,
        civilization_dimensions=value_report.civilization_dimensions,
        civilization_score=value_report.civilization_score,
        reality_dimensions=value_report.reality_dimensions,
        reality_alignment_score=value_report.reality_alignment_score,
        temporal_dimensions=value_report.temporal_dimensions,
        temporal_continuity_score=value_report.temporal_continuity_score,
        meaning_dimensions=value_report.meaning_dimensions,
        meaning_continuity_score=value_report.meaning_continuity_score,
        value_dimensions=value_report.value_dimensions,
        value_continuity_score=value_report.value_continuity_score,
        intent_dimensions=intent_dims,
        intent_continuity_score=combined,
    )
