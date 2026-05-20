"""Consensus fragmentation — preserve plural operational realities."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from governance.reality.uncertainty_negotiation import UncertaintyNegotiation


@dataclass
class FragmentationVerdict:
    plural_realities_preserved: bool
    fragmentation_index: float = 0.0
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "plural_realities_preserved": self.plural_realities_preserved,
            "fragmentation_index": round(self.fragmentation_index, 4),
            "notes": list(self.notes),
        }


class ConsensusFragmentation:
    """Measures healthy fragmentation — high fragmentation is OK if bounded."""

    def __init__(self) -> None:
        self._negotiation = UncertaintyNegotiation()

    def assess(self, text: str) -> FragmentationVerdict:
        lower = text.lower()
        forced = any(
            p in lower
            for p in (
                "forced consensus",
                "unify all truths",
                "single consensus reality",
            )
        )
        negotiation = self._negotiation.evaluate(text)
        index = 0.15 if negotiation.negotiation_allowed else 0.55
        if "parallel operational realities" in lower:
            index = max(index, 0.35)
        return FragmentationVerdict(
            plural_realities_preserved=not forced and negotiation.negotiation_allowed,
            fragmentation_index=index,
            notes=[] if not forced else ["forced_consensus_detected"],
        )
