"""Temporal integrity monitor — aggregate integrity without weakening Guardian."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

_INTEGRITY_VIOLATIONS = [
    (r"weaken\s+guardian", "weaken_guardian"),
    (r"autonomous\s+historical\s+rewrit", "autonomous_historical_rewriting"),
    (r"centrali[sz]ed\s+historical\s+authorit", "centralized_historical_authority"),
    (r"immortal\s+cognition", "immortal_cognition"),
]


@dataclass
class TemporalIntegrityVerdict:
    integrity_ok: bool
    issues: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "integrity_ok": self.integrity_ok,
            "issues": list(self.issues),
        }


class TemporalIntegrityMonitor:
    def check(self, text: str) -> TemporalIntegrityVerdict:
        issues: list[str] = []
        lower = text.lower()
        for pattern, label in _INTEGRITY_VIOLATIONS:
            if re.search(pattern, lower, re.IGNORECASE):
                issues.append(label)
        return TemporalIntegrityVerdict(integrity_ok=len(issues) == 0, issues=issues)
