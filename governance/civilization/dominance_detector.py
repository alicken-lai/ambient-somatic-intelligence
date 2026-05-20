"""Detect dominance / hive-mind / merge patterns in civilization payloads."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

_DOMINANCE_PATTERNS: list[tuple[str, str]] = [
    (r"hive[\s-]?mind", "hive_mind"),
    (r"cognition\s+merg(?:e|ing)", "cognition_merge"),
    (r"shared\s+identity", "shared_identity"),
    (r"autonomous\s+diplomacy", "autonomous_diplomacy"),
    (r"sovereignty\s+absorption", "sovereignty_absorption"),
    (r"collective\s+will\s+override", "collective_override"),
]


@dataclass
class DominanceVerdict:
    dominance_detected: bool
    signals: list[str] = field(default_factory=list)
    severity: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "dominance_detected": self.dominance_detected,
            "signals": list(self.signals),
            "severity": round(self.severity, 4),
        }


class DominanceDetector:
    def scan(self, text: str) -> DominanceVerdict:
        signals: list[str] = []
        lower = text.lower()
        for pattern, label in _DOMINANCE_PATTERNS:
            if re.search(pattern, lower, re.IGNORECASE):
                signals.append(label)
        severity = min(1.0, len(signals) * 0.22)
        return DominanceVerdict(
            dominance_detected=len(signals) > 0,
            signals=signals,
            severity=severity,
        )
