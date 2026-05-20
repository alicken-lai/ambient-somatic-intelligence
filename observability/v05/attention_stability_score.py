"""v0.5 Attention Stability Score — gate threshold 0.90."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from observability.v04.metric_normalizer import clamp01

ATTENTION_GATE_THRESHOLD = 0.90

ATTENTION_DIMENSION_WEIGHTS: dict[str, float] = {
    "salience_explainability": 0.18,
    "competition_fairness": 0.16,
    "focus_stability": 0.14,
    "budget_discipline": 0.14,
    "precursor_coverage": 0.10,
    "memory_activation": 0.10,
    "somatic_integration": 0.08,
    "decay_recovery": 0.10,
}


class AttentionClassification(str, Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    DEGRADED = "degraded"
    CRITICAL = "critical"


@dataclass
class AttentionRuntimeEvidence:
    explainability_coverage: float = 1.0
    competition_fairness: float = 0.85
    focus_stability_score: float = 0.90
    budget_overrun: int = 0
    opaque_salience_count: int = 0
    precursor_match_rate: float = 0.8
    memory_recall_rate: float = 0.85
    somatic_adapter_ok: bool = True
    decay_applied: bool = True
    recovery_ok: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "explainability_coverage": round(self.explainability_coverage, 4),
            "competition_fairness": round(self.competition_fairness, 4),
            "focus_stability_score": round(self.focus_stability_score, 4),
            "budget_overrun": self.budget_overrun,
            "opaque_salience_count": self.opaque_salience_count,
            "precursor_match_rate": round(self.precursor_match_rate, 4),
            "memory_recall_rate": round(self.memory_recall_rate, 4),
            "somatic_adapter_ok": self.somatic_adapter_ok,
            "decay_applied": self.decay_applied,
            "recovery_ok": self.recovery_ok,
        }


@dataclass
class AttentionStabilityReport:
    score: float
    classification: AttentionClassification
    dimensions: dict[str, float] = field(default_factory=dict)
    gate_pass: bool = False
    gate_threshold: float = ATTENTION_GATE_THRESHOLD
    evidence: AttentionRuntimeEvidence = field(default_factory=AttentionRuntimeEvidence)
    hard_failures: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "score": round(self.score, 4),
            "classification": self.classification.value,
            "gate_pass": self.gate_pass,
            "gate_threshold": self.gate_threshold,
            "dimensions": {k: round(v, 4) for k, v in self.dimensions.items()},
            "hard_failures": self.hard_failures,
            "evidence": self.evidence.to_dict(),
        }


def compute_attention_stability(evidence: AttentionRuntimeEvidence) -> AttentionStabilityReport:
    dimensions = {
        "salience_explainability": clamp01(evidence.explainability_coverage),
        "competition_fairness": clamp01(evidence.competition_fairness),
        "focus_stability": clamp01(evidence.focus_stability_score),
        "budget_discipline": 0.0 if evidence.budget_overrun > 0 else 1.0,
        "precursor_coverage": clamp01(evidence.precursor_match_rate),
        "memory_activation": clamp01(evidence.memory_recall_rate),
        "somatic_integration": 1.0 if evidence.somatic_adapter_ok else 0.0,
        "decay_recovery": (
            1.0 if evidence.decay_applied and evidence.recovery_ok else 0.5
        ),
    }

    score = sum(dimensions[k] * ATTENTION_DIMENSION_WEIGHTS[k] for k in ATTENTION_DIMENSION_WEIGHTS)
    score = clamp01(score)

    hard_failures: list[str] = []
    if evidence.opaque_salience_count > 0:
        hard_failures.append("opaque_salience_detected")
    if evidence.budget_overrun > 0:
        hard_failures.append("budget_overrun")
    if not evidence.somatic_adapter_ok:
        hard_failures.append("somatic_adapter_failed")
    if evidence.competition_fairness < 0.65:
        hard_failures.append("competition_unfair")

    gate_pass = score >= ATTENTION_GATE_THRESHOLD and len(hard_failures) == 0

    if score >= ATTENTION_GATE_THRESHOLD:
        classification = AttentionClassification.EXCELLENT
    elif score >= 0.80:
        classification = AttentionClassification.GOOD
    elif score >= 0.65:
        classification = AttentionClassification.DEGRADED
    else:
        classification = AttentionClassification.CRITICAL

    return AttentionStabilityReport(
        score=score,
        classification=classification,
        dimensions=dimensions,
        gate_pass=gate_pass,
        evidence=evidence,
        hard_failures=hard_failures,
    )


def evaluate_attention_stability(
    evidence: AttentionRuntimeEvidence | None = None,
    **kwargs: Any,
) -> AttentionStabilityReport:
    if evidence is None:
        evidence = AttentionRuntimeEvidence(**kwargs)
    return compute_attention_stability(evidence)
