"""
Explain attention — human-readable breakdown of a salience score.

``explain_attention`` turns a :class:`SalienceVector` into an
:class:`AttentionExplanation` whose ``breakdown`` enumerates all ten salience
dimensions (one child each) with their weighted contribution, and whose
``dominant_factor`` names the single largest contributor.

This is the transparency primitive the attention layer relies on so that no
salience decision is opaque (see the v0.5 attention stability gate).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from attention.core.salience import SalienceVector
from attention.core.salience_factor import ALL_DIMENSIONS, DEFAULT_DIMENSION_WEIGHTS


@dataclass
class BreakdownNode:
    """One dimension's contribution to the total salience."""

    name: str
    value: float
    weight: float
    contribution: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "value": round(self.value, 4),
            "weight": round(self.weight, 4),
            "contribution": round(self.contribution, 4),
        }


@dataclass
class AttentionBreakdown:
    """The full set of per-dimension contributions."""

    children: list[BreakdownNode] = field(default_factory=list)
    total: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "total": round(self.total, 4),
            "children": [c.to_dict() for c in self.children],
        }


@dataclass
class AttentionExplanation:
    """A transparent explanation of why a target is (or isn't) salient."""

    dominant_factor: str
    breakdown: AttentionBreakdown
    summary: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "dominant_factor": self.dominant_factor,
            "summary": self.summary,
            "breakdown": self.breakdown.to_dict(),
        }


def explain_attention(salience: SalienceVector) -> AttentionExplanation:
    """Build an :class:`AttentionExplanation` from a :class:`SalienceVector`."""
    weights = salience.weights or DEFAULT_DIMENSION_WEIGHTS
    children: list[BreakdownNode] = []
    for name in ALL_DIMENSIONS:
        value = float(salience.dimensions.get(name, 0.0))
        weight = float(weights.get(name, 0.0))
        children.append(
            BreakdownNode(
                name=name,
                value=value,
                weight=weight,
                contribution=value * weight,
            )
        )

    dominant = max(children, key=lambda c: c.contribution)
    breakdown = AttentionBreakdown(children=children, total=salience.total)
    summary = (
        f"Salience {salience.total:.2f} dominated by "
        f"{dominant.name} ({dominant.contribution:.2f})"
    )
    return AttentionExplanation(
        dominant_factor=dominant.name,
        breakdown=breakdown,
        summary=summary,
    )
