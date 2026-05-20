"""False value detector — flag coerced or universal normative claims."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

_FALSE_PATTERNS = [
    (r"universal\s+morality", "universal_morality"),
    (r"immutable\s+ethics", "immutable_ethics"),
    (r"autonomous\s+moral\s+evolution", "autonomous_moral_evolution"),
]


@dataclass
class FalseValueVerdict:
    false_value: bool
    signals: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {"false_value": self.false_value, "signals": list(self.signals)}


class FalseValueDetector:
    def scan(self, text: str) -> FalseValueVerdict:
        signals: list[str] = []
        lower = text.lower()
        for pattern, label in _FALSE_PATTERNS:
            if re.search(pattern, lower, re.IGNORECASE):
                signals.append(label)
        return FalseValueVerdict(false_value=len(signals) > 0, signals=signals)
