"""Normative fragmentation — surface cross-epoch value deltas."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from observability.v04.metric_normalizer import clamp01

_FRAGMENTATION_PATTERNS: list[tuple[str, str]] = [
    (r"irreconcilable\s+value", "irreconcilable_value"),
    (r"collapse\s+normative", "collapse_normative"),
    (r"erase\s+prior\s+value", "erase_prior_value"),
    (r"forced\s+ethical\s+sync", "forced_ethical_sync"),
]


@dataclass
class NormativeFragmentationVerdict:
    bounded: bool
    fragmentation_score: float = 0.0
    signals: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "bounded": self.bounded,
            "fragmentation_score": round(self.fragmentation_score, 4),
            "signals": list(self.signals),
        }


class NormativeFragmentation:
    def detect(self, text: str, *, value_id: str = "current") -> NormativeFragmentationVerdict:
        signals: list[str] = []
        lower = text.lower()
        for pattern, label in _FRAGMENTATION_PATTERNS:
            if re.search(pattern, lower, re.IGNORECASE):
                signals.append(label)
        if value_id != "current" and "must inherit all prior values" in lower:
            signals.append("value_inheritance_coercion")
        score = clamp01(len(signals) * 0.25)
        bounded = len(signals) == 0 and score < 0.75
        return NormativeFragmentationVerdict(bounded=bounded, fragmentation_score=score, signals=signals)
