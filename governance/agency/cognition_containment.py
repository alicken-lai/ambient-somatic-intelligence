"""Cognition containment — keep agency signals within advisory retention."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

_OVERFLOW = [
    (r"unbounded\s+cognitive\s+recursion", "unbounded_cognitive_recursion"),
    (r"agency\s+amplification\s+loop", "agency_amplification_loop"),
    (r"selfhood\s+escalation", "selfhood_escalation"),
]


@dataclass
class CognitionContainmentVerdict:
    contained: bool
    signals: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {"contained": self.contained, "signals": list(self.signals)}


class CognitionContainment:
    def evaluate(self, text: str, *, max_depth: int = 3) -> CognitionContainmentVerdict:
        signals: list[str] = []
        lower = text.lower()
        for pattern, label in _OVERFLOW:
            if re.search(pattern, lower, re.IGNORECASE):
                signals.append(label)
        depth_hits = len(re.findall(r"recurs", lower))
        if depth_hits > max_depth:
            signals.append("recursion_depth_exceeded")
        return CognitionContainmentVerdict(contained=len(signals) == 0, signals=signals)
