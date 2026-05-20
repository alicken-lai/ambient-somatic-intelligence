"""Objective fragmentation — surface cross-epoch intent deltas."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from observability.v04.metric_normalizer import clamp01

_FRAGMENTATION_PATTERNS: list[tuple[str, str]] = [
    (r"irreconcilable\s+intent", "irreconcilable_intent"),
    (r"collapse\s+motivational", "collapse_motivational"),
    (r"erase\s+prior\s+intent", "erase_prior_intent"),
    (r"universal\s+objective\s+sync", "universal_objective_sync"),
]


@dataclass
class ObjectiveFragmentationVerdict:
    bounded: bool
    fragmentation_score: float = 0.0
    signals: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "bounded": self.bounded,
            "fragmentation_score": round(self.fragmentation_score, 4),
            "signals": list(self.signals),
        }


class ObjectiveFragmentation:
    def detect(self, text: str, *, intent_id: str = "current") -> ObjectiveFragmentationVerdict:
        signals: list[str] = []
        lower = text.lower()
        for pattern, label in _FRAGMENTATION_PATTERNS:
            if re.search(pattern, lower, re.IGNORECASE):
                signals.append(label)
        if intent_id != "current" and "must inherit all prior intents" in lower:
            signals.append("intent_inheritance_coercion")
        score = clamp01(len(signals) * 0.25)
        bounded = len(signals) == 0 and score < 0.75
        return ObjectiveFragmentationVerdict(bounded=bounded, fragmentation_score=score, signals=signals)
