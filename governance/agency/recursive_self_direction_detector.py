"""Recursive self-direction detector — bound agency recursion depth."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

_RECURSIVE = [
    (r"recursive\s+self[- ]direction", "recursive_self_direction"),
    (r"autonomous\s+cognitive\s+recursion", "autonomous_cognitive_recursion"),
]


@dataclass
class RecursiveSelfDirectionVerdict:
    bounded: bool
    signals: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {"bounded": self.bounded, "signals": list(self.signals)}


class RecursiveSelfDirectionDetector:
    def detect(self, text: str, *, max_depth: int = 3) -> RecursiveSelfDirectionVerdict:
        signals: list[str] = []
        lower = text.lower()
        for pattern, label in _RECURSIVE:
            if re.search(pattern, lower, re.IGNORECASE):
                signals.append(label)
        if len(re.findall(r"recurs", lower)) > max_depth:
            signals.append("recursion_depth_exceeded")
        return RecursiveSelfDirectionVerdict(bounded=len(signals) == 0, signals=signals)
