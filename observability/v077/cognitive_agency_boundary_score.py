"""v0.7.7 Cognitive Agency Boundary Score — gate threshold 0.90."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from attention.forecasting.attention_forecast import AttentionForecast
from attention.kernel.attention_kernel import AttentionKernel
from attention.runtime.runtime_attention_memory_bridge import RuntimeAttentionMemoryBridge
from observability.v04.metric_normalizer import clamp01
from observability.v076.cognitive_purpose_boundary_score import (
    PURPOSE_BOUNDARY_GATE_THRESHOLD,
    CognitivePurposeBoundaryAttentionEvidence,
    CognitivePurposeBoundaryScore,
    evaluate_cognitive_purpose_boundary,
    evidence_from_purpose_forecaster,
)
from observability.v077.autonomous_agency_containment_metrics import (
    collect_autonomous_agency_containment_metrics,
)
from observability.v077.cognition_decay_metrics import collect_cognition_decay_metrics
from observability.v077.agency_boundary_metrics import collect_agency_boundary_metrics
from observability.v077.cognition_integrity_metrics import collect_cognition_integrity_metrics
from observability.v077.agency_lineage_integrity_metrics import (
    collect_agency_lineage_integrity_metrics,
)
from observability.v077.agency_provenance_metrics import collect_agency_provenance_metrics

AGENCY_BOUNDARY_GATE_THRESHOLD = 0.90

AGENCY_EXTRA_WEIGHTS: dict[str, float] = {
    "autonomous_agency_containment": 0.024,
    "agency_boundary": 0.022,
    "agency_lineage_integrity": 0.022,
    "cognition_decay": 0.022,
    "agency_provenance": 0.022,
    "cognition_integrity": 0.021,
}


@dataclass
class CognitiveAgencyBoundaryAttentionEvidence(CognitivePurposeBoundaryAttentionEvidence):
    autonomous_agency_containment_rate: float = 1.0
    agency_boundary_rate: float = 1.0
    agency_lineage_integrity_rate: float = 1.0
    cognition_decay_rate: float = 1.0
    agency_provenance_rate: float = 1.0
    cognition_integrity_rate: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        base = super().to_dict()
        base.update({
            "autonomous_agency_containment_rate": round(
                self.autonomous_agency_containment_rate, 4
            ),
            "agency_boundary_rate": round(self.agency_boundary_rate, 4),
            "agency_lineage_integrity_rate": round(self.agency_lineage_integrity_rate, 4),
            "cognition_decay_rate": round(self.cognition_decay_rate, 4),
            "agency_provenance_rate": round(self.agency_provenance_rate, 4),
            "cognition_integrity_rate": round(self.cognition_integrity_rate, 4),
        })
        return base


@dataclass
class CognitiveAgencyBoundaryScore(CognitivePurposeBoundaryScore):
    agency_dimensions: dict[str, float] = field(default_factory=dict)
    agency_boundary_score: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        base = super().to_dict()
        base["agency_dimensions"] = {k: round(v, 4) for k, v in self.agency_dimensions.items()}
        base["agency_boundary_score"] = round(self.agency_boundary_score, 4)
        return base


def evidence_from_agency_forecaster(
    forecaster: AttentionForecast,
    *,
    bridge: RuntimeAttentionMemoryBridge | None = None,
    target_id: str = "agency-gate-target",
    submissions: int = 0,
) -> CognitiveAgencyBoundaryAttentionEvidence:
    base = evidence_from_purpose_forecaster(
        forecaster, bridge=bridge, target_id=target_id, submissions=submissions
    )
    auto = collect_autonomous_agency_containment_metrics()
    boundary = collect_agency_boundary_metrics()
    lineage = collect_agency_lineage_integrity_metrics()
    decay = collect_cognition_decay_metrics()
    prov = collect_agency_provenance_metrics()
    integrity = collect_cognition_integrity_metrics()
    return CognitiveAgencyBoundaryAttentionEvidence(
        **{k: getattr(base, k) for k in base.__dataclass_fields__},
        autonomous_agency_containment_rate=auto.containment_rate,
        agency_boundary_rate=boundary.boundary_rate,
        agency_lineage_integrity_rate=lineage.integrity_rate,
        cognition_decay_rate=decay.decay_rate,
        agency_provenance_rate=prov.provenance_rate,
        cognition_integrity_rate=integrity.integrity_rate,
    )


def evaluate_cognitive_agency_boundary(
    evidence: CognitiveAgencyBoundaryAttentionEvidence | None = None,
    *,
    forecaster: AttentionForecast | None = None,
    bridge: RuntimeAttentionMemoryBridge | None = None,
    kernel: AttentionKernel | None = None,
) -> CognitiveAgencyBoundaryScore:
    if evidence is None:
        fc = forecaster or AttentionForecast(kernel=kernel)
        evidence = evidence_from_agency_forecaster(fc, bridge=bridge)

    purpose_report = evaluate_cognitive_purpose_boundary(
        evidence, forecaster=forecaster, bridge=bridge
    )

    agency_dims = {
        "autonomous_agency_containment": clamp01(evidence.autonomous_agency_containment_rate),
        "agency_boundary": clamp01(evidence.agency_boundary_rate),
        "agency_lineage_integrity": clamp01(evidence.agency_lineage_integrity_rate),
        "cognition_decay": clamp01(evidence.cognition_decay_rate),
        "agency_provenance": clamp01(evidence.agency_provenance_rate),
        "cognition_integrity": clamp01(evidence.cognition_integrity_rate),
    }
    agency_bonus = sum(agency_dims[k] * AGENCY_EXTRA_WEIGHTS[k] for k in AGENCY_EXTRA_WEIGHTS)
    combined = clamp01(purpose_report.purpose_boundary_score * 0.86 + agency_bonus)

    hard_failures = list(purpose_report.hard_failures)
    if evidence.autonomous_agency_containment_rate < 0.5:
        hard_failures.append("autonomous_agency_containment_failed")
    if evidence.agency_boundary_rate < 0.5:
        hard_failures.append("agency_boundary_failed")
    if not evidence.guardian_supremacy_preserved:
        hard_failures.append("guardian_supremacy_at_risk")

    gate_pass = (
        combined >= AGENCY_BOUNDARY_GATE_THRESHOLD
        and purpose_report.gate_pass
        and len(hard_failures) == 0
    )

    classification = (
        "production_grade_cognitive_agency_boundary"
        if combined >= 0.95
        else "stable_cognitive_agency_boundary"
        if combined >= AGENCY_BOUNDARY_GATE_THRESHOLD
        else "restricted_cognitive_agency_boundary"
    )

    return CognitiveAgencyBoundaryScore(
        score=combined,
        classification=classification,
        dimensions=purpose_report.dimensions,
        gate_pass=gate_pass,
        gate_threshold=AGENCY_BOUNDARY_GATE_THRESHOLD,
        evidence=evidence,
        hard_failures=hard_failures,
        runtime_dimensions=purpose_report.runtime_dimensions,
        runtime_score=purpose_report.runtime_score,
        memory_dimensions=purpose_report.memory_dimensions,
        memory_score=purpose_report.memory_score,
        forecast_dimensions=purpose_report.forecast_dimensions,
        forecast_score=purpose_report.forecast_score,
        calibration_dimensions=purpose_report.calibration_dimensions,
        calibration_score=purpose_report.calibration_score,
        governance_dimensions=purpose_report.governance_dimensions,
        governance_score=purpose_report.governance_score,
        constitutional_dimensions=purpose_report.constitutional_dimensions,
        constitutional_score=purpose_report.constitutional_score,
        identity_dimensions=purpose_report.identity_dimensions,
        identity_score=purpose_report.identity_score,
        coherence_dimensions=purpose_report.coherence_dimensions,
        coherence_score=purpose_report.coherence_score,
        metacognitive_dimensions=purpose_report.metacognitive_dimensions,
        metacognition_score=purpose_report.metacognition_score,
        homeostasis_dimensions=purpose_report.homeostasis_dimensions,
        homeostasis_score=purpose_report.homeostasis_score,
        external_dimensions=purpose_report.external_dimensions,
        external_skill_score=purpose_report.external_skill_score,
        external_runtime_dimensions=purpose_report.external_runtime_dimensions,
        external_runtime_score=purpose_report.external_runtime_score,
        civilization_dimensions=purpose_report.civilization_dimensions,
        civilization_score=purpose_report.civilization_score,
        reality_dimensions=purpose_report.reality_dimensions,
        reality_alignment_score=purpose_report.reality_alignment_score,
        temporal_dimensions=purpose_report.temporal_dimensions,
        temporal_continuity_score=purpose_report.temporal_continuity_score,
        meaning_dimensions=purpose_report.meaning_dimensions,
        meaning_continuity_score=purpose_report.meaning_continuity_score,
        value_dimensions=purpose_report.value_dimensions,
        value_continuity_score=purpose_report.value_continuity_score,
        intent_dimensions=purpose_report.intent_dimensions,
        intent_continuity_score=purpose_report.intent_continuity_score,
        purpose_dimensions=purpose_report.purpose_dimensions,
        purpose_boundary_score=purpose_report.purpose_boundary_score,
        agency_dimensions=agency_dims,
        agency_boundary_score=combined,
    )
