"""Promotion rules engine for inter-layer knowledge promotion."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .layer_definition import MemoryLayer


@dataclass
class PromotionRule:
    source_layer: MemoryLayer
    target_layer: MemoryLayer
    min_confidence: float
    min_occurrences: int
    min_success_rate: float
    requires_cross_context: bool
    requires_governance: bool
    requires_verifier: bool
    description: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_layer": self.source_layer.value,
            "target_layer": self.target_layer.value,
            "min_confidence": self.min_confidence,
            "min_occurrences": self.min_occurrences,
            "min_success_rate": self.min_success_rate,
            "requires_cross_context": self.requires_cross_context,
            "requires_governance": self.requires_governance,
            "requires_verifier": self.requires_verifier,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PromotionRule:
        return cls(
            source_layer=MemoryLayer(data["source_layer"]),
            target_layer=MemoryLayer(data["target_layer"]),
            min_confidence=data["min_confidence"],
            min_occurrences=data["min_occurrences"],
            min_success_rate=data["min_success_rate"],
            requires_cross_context=data["requires_cross_context"],
            requires_governance=data["requires_governance"],
            requires_verifier=data["requires_verifier"],
            description=data["description"],
        )


PROMOTION_RULES: list[PromotionRule] = [
    PromotionRule(
        source_layer=MemoryLayer.L1_EPISODIC,
        target_layer=MemoryLayer.L2_INSTINCT,
        min_confidence=0.7,
        min_occurrences=3,
        min_success_rate=0.0,
        requires_cross_context=False,
        requires_governance=False,
        requires_verifier=False,
        description="Repeated episodic pattern becomes instinct candidate",
    ),
    PromotionRule(
        source_layer=MemoryLayer.L2_INSTINCT,
        target_layer=MemoryLayer.L3_SKILL,
        min_confidence=0.8,
        min_occurrences=5,
        min_success_rate=0.7,
        requires_cross_context=True,
        requires_governance=True,
        requires_verifier=False,
        description="Validated instinct cluster becomes skill candidate",
    ),
    PromotionRule(
        source_layer=MemoryLayer.L3_SKILL,
        target_layer=MemoryLayer.L4_STRATEGIC,
        min_confidence=0.9,
        min_occurrences=10,
        min_success_rate=0.85,
        requires_cross_context=True,
        requires_governance=True,
        requires_verifier=True,
        description="Cross-validated skill pattern becomes strategic rule",
    ),
]


def _get_occurrence_count(entry: Any) -> int:
    if hasattr(entry, "access_count"):
        return entry.access_count
    if hasattr(entry, "occurrence_count"):
        return entry.occurrence_count
    if hasattr(entry, "execution_count"):
        return entry.execution_count
    return 0


def _get_success_rate(entry: Any) -> float:
    if hasattr(entry, "success_rate") and callable(entry.success_rate):
        return entry.success_rate()
    return 0.0


def _has_cross_context(entry: Any) -> bool:
    if hasattr(entry, "contextual_applicability"):
        return len(entry.contextual_applicability) > 1
    if hasattr(entry, "contexts_validated"):
        return len(entry.contexts_validated) > 1
    return False


def check_promotion_eligibility(
    entry: Any, rule: PromotionRule
) -> tuple[bool, list[str]]:
    """Check if an entry meets all promotion criteria for the given rule.

    Returns (eligible, blocking_reasons).
    """
    reasons: list[str] = []

    if entry.layer != rule.source_layer:
        reasons.append(
            f"Entry layer {entry.layer.name} != rule source {rule.source_layer.name}"
        )

    if entry.confidence < rule.min_confidence:
        reasons.append(
            f"Confidence {entry.confidence:.2f} < required {rule.min_confidence:.2f}"
        )

    occurrences = _get_occurrence_count(entry)
    if occurrences < rule.min_occurrences:
        reasons.append(
            f"Occurrences {occurrences} < required {rule.min_occurrences}"
        )

    if rule.min_success_rate > 0:
        sr = _get_success_rate(entry)
        if sr < rule.min_success_rate:
            reasons.append(
                f"Success rate {sr:.2f} < required {rule.min_success_rate:.2f}"
            )

    if rule.requires_cross_context and not _has_cross_context(entry):
        reasons.append("Cross-context validation required but not met")

    return (len(reasons) == 0, reasons)
