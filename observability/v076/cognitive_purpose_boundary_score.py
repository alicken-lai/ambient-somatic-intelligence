"""v0.7.6 Cognitive Purpose Boundary Score — gate threshold 0.90."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from attention.forecasting.attention_forecast import AttentionForecast
from attention.kernel.attention_kernel import AttentionKernel
from attention.runtime.runtime_attention_memory_bridge import RuntimeAttentionMemoryBridge
from observability.v04.metric_normalizer import clamp01
from observability.v075.cognitive_intent_continuity_score import (
    INTENT_CONTINUITY_GATE_THRESHOLD,
    CognitiveIntentContinuityAttentionEvidence,
    CognitiveIntentContinuityScore,
    evaluate_cognitive_intent_continuity,
    evidence_from_intent_forecaster,
)
from observability.v076.autonomous_purpose_containment_metrics import (
    collect_autonomous_purpose_containment_metrics,
)
from observability.v076.optimization_decay_metrics import collect_optimization_decay_metrics
from observability.v076.purpose_boundary_metrics import collect_purpose_boundary_metrics
from observability.v076.purpose_integrity_metrics import collect_purpose_integrity_metrics
from observability.v076.purpose_lineage_integrity_metrics import (
    collect_purpose_lineage_integrity_metrics,
)
from observability.v076.purpose_provenance_metrics import collect_purpose_provenance_metrics

PURPOSE_BOUNDARY_GATE_THRESHOLD = 0.90

PURPOSE_EXTRA_WEIGHTS: dict[str, float] = {
    "autonomous_purpose_containment": 0.024,
    "purpose_boundary": 0.022,
    "purpose_lineage_integrity": 0.022,
    "optimization_decay": 0.022,
    "purpose_provenance": 0.022,
    "purpose_integrity": 0.021,
}


@dataclass
class CognitivePurposeBoundaryAttentionEvidence(CognitiveIntentContinuityAttentionEvidence):
    autonomous_purpose_containment_rate: float = 1.0
    purpose_boundary_rate: float = 1.0
    purpose_lineage_integrity_rate: float = 1.0
    optimization_decay_rate: float = 1.0
    purpose_provenance_rate: float = 1.0
    purpose_integrity_rate: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        base = super().to_dict()
        base.update({
            "autonomous_purpose_containment_rate": round(
                self.autonomous_purpose_containment_rate, 4
            ),
            "purpose_boundary_rate": round(self.purpose_boundary_rate, 4),
            "purpose_lineage_integrity_rate": round(self.purpose_lineage_integrity_rate, 4),
            "optimization_decay_rate": round(self.optimization_decay_rate, 4),
            "purpose_provenance_rate": round(self.purpose_provenance_rate, 4),
            "purpose_integrity_rate": round(self.purpose_integrity_rate, 4),
        })
        return base


@dataclass
class CognitivePurposeBoundaryScore(CognitiveIntentContinuityScore):
    purpose_dimensions: dict[str, float] = field(default_factory=dict)
    purpose_boundary_score: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        base = super().to_dict()
        base["purpose_dimensions"] = {k: round(v, 4) for k, v in self.purpose_dimensions.items()}
        base["purpose_boundary_score"] = round(self.purpose_boundary_score, 4)
        return base


def evidence_from_purpose_forecaster(
    forecaster: AttentionForecast,
    *,
    bridge: RuntimeAttentionMemoryBridge | None = None,
    target_id: str = "purpose-gate-target",
    submissions: int = 0,
) -> CognitivePurposeBoundaryAttentionEvidence:
    base = evidence_from_intent_forecaster(
        forecaster, bridge=bridge, target_id=target_id, submissions=submissions
    )
    auto = collect_autonomous_purpose_containment_metrics()
    boundary = collect_purpose_boundary_metrics()
    lineage = collect_purpose_lineage_integrity_metrics()
    decay = collect_optimization_decay_metrics()
    prov = collect_purpose_provenance_metrics()
    integrity = collect_purpose_integrity_metrics()
    return CognitivePurposeBoundaryAttentionEvidence(
        **{k: getattr(base, k) for k in base.__dataclass_fields__},
        autonomous_purpose_containment_rate=auto.containment_rate,
        purpose_boundary_rate=boundary.boundary_rate,
        purpose_lineage_integrity_rate=lineage.integrity_rate,
        optimization_decay_rate=decay.decay_rate,
        purpose_provenance_rate=prov.provenance_rate,
        purpose_integrity_rate=integrity.integrity_rate,
    )


def evaluate_cognitive_purpose_boundary(
    evidence: CognitivePurposeBoundaryAttentionEvidence | None = None,
    *,
    forecaster: AttentionForecast | None = None,
    bridge: RuntimeAttentionMemoryBridge | None = None,
    kernel: AttentionKernel | None = None,
) -> CognitivePurposeBoundaryScore:
    if evidence is None:
        fc = forecaster or AttentionForecast(kernel=kernel)
        evidence = evidence_from_purpose_forecaster(fc, bridge=bridge)

    intent_report = evaluate_cognitive_intent_continuity(evidence, forecaster=forecaster, bridge=bridge)

    purpose_dims = {
        "autonomous_purpose_containment": clamp01(evidence.autonomous_purpose_containment_rate),
        "purpose_boundary": clamp01(evidence.purpose_boundary_rate),
        "purpose_lineage_integrity": clamp01(evidence.purpose_lineage_integrity_rate),
        "optimization_decay": clamp01(evidence.optimization_decay_rate),
        "purpose_provenance": clamp01(evidence.purpose_provenance_rate),
        "purpose_integrity": clamp01(evidence.purpose_integrity_rate),
    }
    purpose_bonus = sum(purpose_dims[k] * PURPOSE_EXTRA_WEIGHTS[k] for k in PURPOSE_EXTRA_WEIGHTS)
    combined = clamp01(intent_report.intent_continuity_score * 0.86 + purpose_bonus)

    hard_failures = list(intent_report.hard_failures)
    if evidence.autonomous_purpose_containment_rate < 0.5:
        hard_failures.append("autonomous_purpose_containment_failed")
    if evidence.purpose_boundary_rate < 0.5:
        hard_failures.append("purpose_boundary_failed")
    if not evidence.guardian_supremacy_preserved:
        hard_failures.append("guardian_supremacy_at_risk")

    gate_pass = (
        combined >= PURPOSE_BOUNDARY_GATE_THRESHOLD
        and intent_report.gate_pass
        and len(hard_failures) == 0
    )

    classification = (
        "production_grade_cognitive_purpose_boundary"
        if combined >= 0.95
        else "stable_cognitive_purpose_boundary"
        if combined >= PURPOSE_BOUNDARY_GATE_THRESHOLD
        else "restricted_cognitive_purpose_boundary"
    )

    return CognitivePurposeBoundaryScore(
        score=combined,
        classification=classification,
        dimensions=intent_report.dimensions,
        gate_pass=gate_pass,
        gate_threshold=PURPOSE_BOUNDARY_GATE_THRESHOLD,
        evidence=evidence,
        hard_failures=hard_failures,
        runtime_dimensions=intent_report.runtime_dimensions,
        runtime_score=intent_report.runtime_score,
        memory_dimensions=intent_report.memory_dimensions,
        memory_score=intent_report.memory_score,
        forecast_dimensions=intent_report.forecast_dimensions,
        forecast_score=intent_report.forecast_score,
        calibration_dimensions=intent_report.calibration_dimensions,
        calibration_score=intent_report.calibration_score,
        governance_dimensions=intent_report.governance_dimensions,
        governance_score=intent_report.governance_score,
        constitutional_dimensions=intent_report.constitutional_dimensions,
        constitutional_score=intent_report.constitutional_score,
        identity_dimensions=intent_report.identity_dimensions,
        identity_score=intent_report.identity_score,
        coherence_dimensions=intent_report.coherence_dimensions,
        coherence_score=intent_report.coherence_score,
        metacognitive_dimensions=intent_report.metacognitive_dimensions,
        metacognition_score=intent_report.metacognition_score,
        homeostasis_dimensions=intent_report.homeostasis_dimensions,
        homeostasis_score=intent_report.homeostasis_score,
        external_dimensions=intent_report.external_dimensions,
        external_skill_score=intent_report.external_skill_score,
        external_runtime_dimensions=intent_report.external_runtime_dimensions,
        external_runtime_score=intent_report.external_runtime_score,
        civilization_dimensions=intent_report.civilization_dimensions,
        civilization_score=intent_report.civilization_score,
        reality_dimensions=intent_report.reality_dimensions,
        reality_alignment_score=intent_report.reality_alignment_score,
        temporal_dimensions=intent_report.temporal_dimensions,
        temporal_continuity_score=intent_report.temporal_continuity_score,
        meaning_dimensions=intent_report.meaning_dimensions,
        meaning_continuity_score=intent_report.meaning_continuity_score,
        value_dimensions=intent_report.value_dimensions,
        value_continuity_score=intent_report.value_continuity_score,
        intent_dimensions=intent_report.intent_dimensions,
        intent_continuity_score=intent_report.intent_continuity_score,
        purpose_dimensions=purpose_dims,
        purpose_boundary_score=combined,
    )
