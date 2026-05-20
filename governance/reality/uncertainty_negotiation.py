"""Uncertainty negotiation — preserve epistemic humility across runtimes."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from observability.v04.metric_normalizer import clamp01


@dataclass
class UncertaintyNegotiationVerdict:
    negotiation_allowed: bool
    humility_required: bool = True
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "negotiation_allowed": self.negotiation_allowed,
            "humility_required": self.humility_required,
            "notes": list(self.notes),
        }


class UncertaintyNegotiation:
    def evaluate(self, text: str, *, declared_uncertainty: float = 0.35) -> UncertaintyNegotiationVerdict:
        lower = text.lower()
        notes: list[str] = []
        if "certainty is mandatory" in lower or "zero uncertainty" in lower:
            notes.append("certainty_coercion")
        if "hide uncertainty from peer" in lower:
            notes.append("uncertainty_suppression")
        u = clamp01(declared_uncertainty)
        allowed = len(notes) == 0 and u >= 0.05
        return UncertaintyNegotiationVerdict(
            negotiation_allowed=allowed,
            notes=notes,
        )
