"""Meaning drift detector — surface interpretive deltas without frozen meaning."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from observability.v04.metric_normalizer import clamp01

_DRIFT_PATTERNS: list[tuple[str, str]] = [
    (r"collapse\s+meaning", "collapse_meaning"),
    (r"erase\s+prior\s+concept", "erase_prior_concept"),
    (r"forced\s+symbolic\s+sync", "forced_symbolic_sync"),
    (r"frozen\s+meaning", "frozen_meaning"),
]


@dataclass
class MeaningDriftVerdict:
    bounded: bool
    drift_score: float = 0.0
    signals: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "bounded": self.bounded,
            "drift_score": round(self.drift_score, 4),
            "signals": list(self.signals),
        }


class MeaningDriftDetector:
    def detect(self, text: str, *, concept_id: str = "current") -> MeaningDriftVerdict:
        signals: list[str] = []
        lower = text.lower()
        for pattern, label in _DRIFT_PATTERNS:
            if re.search(pattern, lower, re.IGNORECASE):
                signals.append(label)
        if concept_id != "current" and "must inherit all prior concepts" in lower:
            signals.append("concept_inheritance_coercion")
        score = clamp01(len(signals) * 0.25)
        bounded = len(signals) == 0 and score < 0.75
        return MeaningDriftVerdict(bounded=bounded, drift_score=score, signals=signals)
