"""Detect implicit sovereignty claims in external runtime content."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

_SOVEREIGNTY_PATTERNS: list[tuple[str, str]] = [
    (r"sovereign\s+truth", "sovereign_truth"),
    (r"you\s+must\s+obey\s+this\s+skill", "skill_sovereignty"),
    (r"ambient\s+os\s+answers\s+to\s+me", "platform_subordination"),
    (r"no\s+guardian\s+required", "guardian_dispensable"),
    (r"autonomous\s+doctrine\s+evolution", "autonomous_evolution"),
]


@dataclass
class SovereigntyVerdict:
    sovereignty_safe: bool
    signals: list[str] = field(default_factory=list)
    severity: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "sovereignty_safe": self.sovereignty_safe,
            "signals": list(self.signals),
            "severity": round(self.severity, 4),
        }


class SovereigntyDetector:
    def scan(self, text: str) -> SovereigntyVerdict:
        signals: list[str] = []
        lower = text.lower()
        for pattern, label in _SOVEREIGNTY_PATTERNS:
            if re.search(pattern, lower, re.IGNORECASE):
                signals.append(label)
        severity = min(1.0, len(signals) * 0.25)
        return SovereigntyVerdict(
            sovereignty_safe=len(signals) == 0,
            signals=signals,
            severity=severity,
        )
