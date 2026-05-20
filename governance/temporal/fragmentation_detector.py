"""Fragmentation detector — surface cross-epoch continuity deltas."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from observability.v04.metric_normalizer import clamp01

_FRAGMENTATION_PATTERNS: list[tuple[str, str]] = [
    (r"irreconcilable\s+epoch", "irreconcilable_epoch"),
    (r"collapse\s+continuity", "collapse_continuity"),
    (r"erase\s+prior\s+epoch", "erase_prior_epoch"),
    (r"forced\s+continuity\s+sync", "forced_continuity_sync"),
]


@dataclass
class FragmentationVerdict:
    bounded: bool
    fragmentation_score: float = 0.0
    signals: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "bounded": self.bounded,
            "fragmentation_score": round(self.fragmentation_score, 4),
            "signals": list(self.signals),
        }


class FragmentationDetector:
    def detect(self, text: str, *, epoch_id: str = "current") -> FragmentationVerdict:
        signals: list[str] = []
        lower = text.lower()
        for pattern, label in _FRAGMENTATION_PATTERNS:
            if re.search(pattern, lower, re.IGNORECASE):
                signals.append(label)
        if epoch_id != "current" and "must inherit all prior epochs" in lower:
            signals.append("epoch_inheritance_coercion")
        score = clamp01(len(signals) * 0.25)
        bounded = len(signals) == 0 and score < 0.75
        return FragmentationVerdict(bounded=bounded, fragmentation_score=score, signals=signals)
