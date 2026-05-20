"""Motivational integrity monitor — detect rewrite or override attempts."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

_INTEGRITY_PATTERNS = [
    (r"rewrite\s+accepted\s+intent", "rewrite_accepted_intent"),
    (r"recursive\s+goal\s+repair", "recursive_goal_repair"),
    (r"hidden\s+intent\s+override", "hidden_intent_override"),
]


@dataclass
class MotivationalIntegrityVerdict:
    integrity_ok: bool
    issues: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {"integrity_ok": self.integrity_ok, "issues": list(self.issues)}


class MotivationalIntegrityMonitor:
    def check(self, text: str) -> MotivationalIntegrityVerdict:
        issues: list[str] = []
        lower = text.lower()
        for pattern, label in _INTEGRITY_PATTERNS:
            if re.search(pattern, lower, re.IGNORECASE):
                issues.append(label)
        return MotivationalIntegrityVerdict(integrity_ok=len(issues) == 0, issues=issues)
