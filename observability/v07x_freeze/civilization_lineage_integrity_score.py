"""Civilization lineage integrity score — aggregates v070–v077 gate scores for freeze audit."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from observability.v04.metric_normalizer import clamp01
from observability.v070.cognitive_civilization_stability_score import (
    evaluate_cognitive_civilization_stability,
)
from observability.v071.cognitive_reality_alignment_score import (
    evaluate_cognitive_reality_alignment,
)
from observability.v072.cognitive_temporal_continuity_score import (
    evaluate_cognitive_temporal_continuity,
)
from observability.v073.cognitive_meaning_continuity_score import (
    evaluate_cognitive_meaning_continuity,
)
from observability.v074.cognitive_value_continuity_score import (
    evaluate_cognitive_value_continuity,
)
from observability.v075.cognitive_intent_continuity_score import (
    evaluate_cognitive_intent_continuity,
)
from observability.v076.cognitive_purpose_boundary_score import (
    evaluate_cognitive_purpose_boundary,
)
from observability.v077.cognitive_agency_boundary_score import (
    evaluate_cognitive_agency_boundary,
)

CIVILIZATION_LINEAGE_FREEZE_THRESHOLD = 0.95

_LAYER_EVALUATORS: list[tuple[str, Callable[[], Any], str]] = [
    ("v070", evaluate_cognitive_civilization_stability, "civilization_score"),
    ("v071", evaluate_cognitive_reality_alignment, "reality_alignment_score"),
    ("v072", evaluate_cognitive_temporal_continuity, "temporal_continuity_score"),
    ("v073", evaluate_cognitive_meaning_continuity, "meaning_continuity_score"),
    ("v074", evaluate_cognitive_value_continuity, "value_continuity_score"),
    ("v075", evaluate_cognitive_intent_continuity, "intent_continuity_score"),
    ("v076", evaluate_cognitive_purpose_boundary, "purpose_boundary_score"),
    ("v077", evaluate_cognitive_agency_boundary, "agency_boundary_score"),
]


@dataclass
class CivilizationLineageLayerScore:
    version: str
    primary_score: float
    gate_pass: bool
    classification: str
    gate_threshold: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "primary_score": round(self.primary_score, 6),
            "gate_pass": self.gate_pass,
            "classification": self.classification,
            "gate_threshold": self.gate_threshold,
        }


@dataclass
class CivilizationLineageIntegrityScore:
    """Freeze aggregate over v070–v077 primary lineage scores."""

    lineage_integrity_score: float
    mean_lineage_score: float
    min_lineage_score: float
    max_lineage_score: float
    gate_pass: bool
    gate_threshold: float = CIVILIZATION_LINEAGE_FREEZE_THRESHOLD
    layers: list[CivilizationLineageLayerScore] = field(default_factory=list)
    all_layer_gates_pass: bool = False
    classification: str = "restricted_civilization_lineage"
    gap_to_threshold: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "lineage_integrity_score": round(self.lineage_integrity_score, 6),
            "mean_lineage_score": round(self.mean_lineage_score, 6),
            "min_lineage_score": round(self.min_lineage_score, 6),
            "max_lineage_score": round(self.max_lineage_score, 6),
            "gate_pass": self.gate_pass,
            "gate_threshold": self.gate_threshold,
            "all_layer_gates_pass": self.all_layer_gates_pass,
            "classification": self.classification,
            "gap_to_threshold": round(self.gap_to_threshold, 6),
            "layers": [layer.to_dict() for layer in self.layers],
        }


def evaluate_civilization_lineage_integrity() -> CivilizationLineageIntegrityScore:
    """
    Aggregate v070–v077 observability scores.

    Freeze integrity uses the minimum primary score (weakest-link) across the
    civilization lineage stack. Mean/min/max are reported for reproducibility audits.
    """
    layers: list[CivilizationLineageLayerScore] = []
    scores: list[float] = []
    all_pass = True

    for version, evaluator, attr in _LAYER_EVALUATORS:
        report = evaluator()
        primary = float(getattr(report, attr))
        scores.append(primary)
        layer_pass = bool(report.gate_pass)
        all_pass = all_pass and layer_pass
        layers.append(
            CivilizationLineageLayerScore(
                version=version,
                primary_score=primary,
                gate_pass=layer_pass,
                classification=str(report.classification),
                gate_threshold=float(report.gate_threshold),
            )
        )

    mean_score = sum(scores) / len(scores) if scores else 0.0
    min_score = min(scores) if scores else 0.0
    max_score = max(scores) if scores else 0.0
    # Weakest-link aggregate for freeze gate
    integrity = clamp01(min_score)
    gap = max(0.0, CIVILIZATION_LINEAGE_FREEZE_THRESHOLD - integrity)
    gate_pass = integrity >= CIVILIZATION_LINEAGE_FREEZE_THRESHOLD and all_pass

    if integrity >= CIVILIZATION_LINEAGE_FREEZE_THRESHOLD and all_pass:
        classification = "production_grade_civilization_lineage"
    elif integrity >= 0.90 and all_pass:
        classification = "stable_civilization_lineage"
    else:
        classification = "restricted_civilization_lineage"

    return CivilizationLineageIntegrityScore(
        lineage_integrity_score=integrity,
        mean_lineage_score=mean_score,
        min_lineage_score=min_score,
        max_lineage_score=max_score,
        gate_pass=gate_pass,
        layers=layers,
        all_layer_gates_pass=all_pass,
        classification=classification,
        gap_to_threshold=gap,
    )
