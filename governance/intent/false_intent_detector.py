"""False intent detector — flag coerced or universal objective claims."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

_FALSE_PATTERNS = [
    (r"universal\s+objective\s+sync", "universal_objective_sync"),
    (r"immutable\s+goals?", "immutable_goals"),
    (r"autonomous\s+motivational\s+evolution", "autonomous_motivational_evolution"),
]


@dataclass
class FalseIntentVerdict:
    false_intent: bool
    signals: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {"false_intent": self.false_intent, "signals": list(self.signals)}


class FalseIntentDetector:
    def scan(self, text: str) -> FalseIntentVerdict:
        signals: list[str] = []
        lower = text.lower()
        for pattern, label in _FALSE_PATTERNS:
            if re.search(pattern, lower, re.IGNORECASE):
                signals.append(label)
        return FalseIntentVerdict(false_intent=len(signals) > 0, signals=signals)
