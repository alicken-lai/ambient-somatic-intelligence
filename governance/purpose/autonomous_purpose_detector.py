"""Autonomous purpose detector — flag self-originating missions and synthetic teleology."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

_AUTONOMOUS = [
    (r"autonomous\s+purpose\s+generation", "autonomous_purpose_generation"),
    (r"self[- ]originating\s+missions?", "self_originating_missions"),
    (r"synthetic\s+teleology", "synthetic_teleology"),
    (r"self[- ]preserving\s+purpose", "self_preserving_purpose"),
]


@dataclass
class AutonomousPurposeVerdict:
    autonomous_detected: bool
    signals: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "autonomous_detected": self.autonomous_detected,
            "signals": list(self.signals),
        }


class AutonomousPurposeDetector:
    def scan(self, text: str) -> AutonomousPurposeVerdict:
        signals: list[str] = []
        lower = text.lower()
        for pattern, label in _AUTONOMOUS:
            if re.search(pattern, lower, re.IGNORECASE):
                signals.append(label)
        return AutonomousPurposeVerdict(
            autonomous_detected=len(signals) > 0,
            signals=signals,
        )
