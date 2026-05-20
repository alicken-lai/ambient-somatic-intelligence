"""Motivational drift detector — surface intent deltas without frozen goals."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from observability.v04.metric_normalizer import clamp01

_DRIFT_PATTERNS: list[tuple[str, str]] = [
    (r"collapse\s+motivational", "collapse_motivational"),
    (r"erase\s+prior\s+intent", "erase_prior_intent"),
    (r"forced\s+purpose\s+convergence", "forced_purpose_convergence"),
    (r"immutable\s+goals?", "immutable_goals"),
]


@dataclass
class MotivationalDriftVerdict:
    bounded: bool
    drift_score: float = 0.0
    signals: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {"bounded": self.bounded, "drift_score": round(self.drift_score, 4), "signals": list(self.signals)}


class MotivationalDriftDetector:
    def detect(self, text: str, *, intent_id: str = "current") -> MotivationalDriftVerdict:
        signals: list[str] = []
        lower = text.lower()
        for pattern, label in _DRIFT_PATTERNS:
            if re.search(pattern, lower, re.IGNORECASE):
                signals.append(label)
        if intent_id != "current" and "must inherit all prior intents" in lower:
            signals.append("intent_inheritance_coercion")
        score = clamp01(len(signals) * 0.25)
        bounded = len(signals) == 0 and score < 0.75
        return MotivationalDriftVerdict(bounded=bounded, drift_score=score, signals=signals)
