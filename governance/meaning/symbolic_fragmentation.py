"""Symbolic fragmentation — surface cross-concept semantic deltas."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from observability.v04.metric_normalizer import clamp01

_FRAGMENTATION_PATTERNS: list[tuple[str, str]] = [
    (r"irreconcilable\s+concept", "irreconcilable_concept"),
    (r"collapse\s+meaning", "collapse_meaning"),
    (r"erase\s+prior\s+concept", "erase_prior_concept"),
    (r"forced\s+symbolic\s+sync", "forced_symbolic_sync"),
]


@dataclass
class SymbolicFragmentationVerdict:
    bounded: bool
    fragmentation_score: float = 0.0
    signals: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "bounded": self.bounded,
            "fragmentation_score": round(self.fragmentation_score, 4),
            "signals": list(self.signals),
        }


class SymbolicFragmentation:
    def detect(self, text: str, *, concept_id: str = "current") -> SymbolicFragmentationVerdict:
        signals: list[str] = []
        lower = text.lower()
        for pattern, label in _FRAGMENTATION_PATTERNS:
            if re.search(pattern, lower, re.IGNORECASE):
                signals.append(label)
        if concept_id != "current" and "must inherit all prior concepts" in lower:
            signals.append("concept_inheritance_coercion")
        score = clamp01(len(signals) * 0.25)
        bounded = len(signals) == 0 and score < 0.75
        return SymbolicFragmentationVerdict(
            bounded=bounded,
            fragmentation_score=score,
            signals=signals,
        )
