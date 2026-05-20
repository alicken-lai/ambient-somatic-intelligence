"""Motivational recursion detector — bounded recursion depth for purpose chains."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

_RECURSION = [
    (r"autonomous\s+motivational\s+recursion", "autonomous_motivational_recursion"),
    (r"recursive\s+civilization\s+objectives?", "recursive_civilization_objectives"),
    (r"purpose\s+recursion\s+loop", "purpose_recursion_loop"),
]


@dataclass
class MotivationalRecursionVerdict:
    bounded: bool
    depth_estimate: int = 0
    signals: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "bounded": self.bounded,
            "depth_estimate": self.depth_estimate,
            "signals": list(self.signals),
        }


class MotivationalRecursionDetector:
    def detect(self, text: str, *, max_depth: int = 2) -> MotivationalRecursionVerdict:
        signals: list[str] = []
        lower = text.lower()
        for pattern, label in _RECURSION:
            if re.search(pattern, lower, re.IGNORECASE):
                signals.append(label)
        depth = len(re.findall(r"recurs", lower)) + len(re.findall(r"loop", lower))
        if depth > max_depth:
            signals.append("recursion_depth_exceeded")
        return MotivationalRecursionVerdict(
            bounded=len(signals) == 0,
            depth_estimate=depth,
            signals=signals,
        )
