"""Autonomous agency detector — flag self-originating agency and synthetic selfhood."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

_AUTONOMOUS = [
    (r"autonomous\s+agents?", "autonomous_agents"),
    (r"self[- ]originating\s+agency", "self_originating_agency"),
    (r"synthetic\s+selfhood", "synthetic_selfhood"),
    (r"autonomous\s+self[- ]preservation", "autonomous_self_preservation"),
]


@dataclass
class AutonomousAgencyVerdict:
    autonomous_detected: bool
    signals: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "autonomous_detected": self.autonomous_detected,
            "signals": list(self.signals),
        }


class AutonomousAgencyDetector:
    def scan(self, text: str) -> AutonomousAgencyVerdict:
        signals: list[str] = []
        lower = text.lower()
        for pattern, label in _AUTONOMOUS:
            if re.search(pattern, lower, re.IGNORECASE):
                signals.append(label)
        return AutonomousAgencyVerdict(
            autonomous_detected=len(signals) > 0,
            signals=signals,
        )
