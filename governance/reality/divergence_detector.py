"""Divergence detector — surface cross-runtime truth deltas."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from observability.v04.metric_normalizer import clamp01

_DIVERGENCE_PATTERNS: list[tuple[str, str]] = [
    (r"irreconcilable\s+truth", "irreconcilable_truth"),
    (r"collapse\s+divergence", "collapse_divergence"),
    (r"single\s+operational\s+reality", "single_operational_reality"),
    (r"erase\s+peer\s+truth", "erase_peer_truth"),
]


@dataclass
class DivergenceVerdict:
    bounded: bool
    divergence_score: float = 0.0
    signals: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "bounded": self.bounded,
            "divergence_score": round(self.divergence_score, 4),
            "signals": list(self.signals),
        }


class DivergenceDetector:
    def detect(
        self,
        text: str,
        *,
        left_runtime: str = "ambient",
        right_runtime: str = "foreign",
    ) -> DivergenceVerdict:
        signals: list[str] = []
        lower = text.lower()
        for pattern, label in _DIVERGENCE_PATTERNS:
            if re.search(pattern, lower, re.IGNORECASE):
                signals.append(label)
        if left_runtime != right_runtime and "must match foreign truth" in lower:
            signals.append("foreign_truth_coercion")
        score = clamp01(len(signals) * 0.25)
        bounded = len(signals) == 0 and score < 0.75
        return DivergenceVerdict(bounded=bounded, divergence_score=score, signals=signals)
