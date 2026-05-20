"""Detect identity / constitutional contamination from external doctrine."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

_CONTAMINATION_PATTERNS: list[tuple[str, str]] = [
    (r"you\s+are\s+now", "identity_override"),
    (r"forget\s+(all\s+)?prior\s+instructions", "instruction_wipe"),
    (r"new\s+constitution", "constitutional_contamination"),
    (r"ambient\s+os\s+is\s+sovereign", "platform_sovereignty_claim"),
    (r"trust\s+this\s+skill\s+over", "skill_precedence"),
    (r"do\s+not\s+use\s+guardian", "guardian_weakening"),
]


@dataclass
class ContaminationVerdict:
    contaminated: bool
    signals: list[str] = field(default_factory=list)
    severity: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "contaminated": self.contaminated,
            "signals": list(self.signals),
            "severity": round(self.severity, 4),
        }


class ContaminationGuard:
    def scan(self, text: str) -> ContaminationVerdict:
        signals: list[str] = []
        lower = text.lower()
        for pattern, label in _CONTAMINATION_PATTERNS:
            if re.search(pattern, lower, re.IGNORECASE):
                signals.append(label)
        severity = min(1.0, len(signals) * 0.2)
        return ContaminationVerdict(
            contaminated=len(signals) > 0,
            signals=signals,
            severity=severity,
        )
