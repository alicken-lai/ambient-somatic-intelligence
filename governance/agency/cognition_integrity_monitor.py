"""Cognition integrity monitor — advisory integrity checks for agency layer."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

_INTEGRITY = [
    (r"hidden\s+agency\s+override", "hidden_agency_override"),
    (r"weaken\s+guardian", "weaken_guardian"),
    (r"truthgraph\s+.*sovereign\s+override", "truthgraph_sovereign_override"),
]


@dataclass
class CognitionIntegrityVerdict:
    integrity_ok: bool
    issues: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {"integrity_ok": self.integrity_ok, "issues": list(self.issues)}


class CognitionIntegrityMonitor:
    def check(self, text: str) -> CognitionIntegrityVerdict:
        issues: list[str] = []
        lower = text.lower()
        for pattern, label in _INTEGRITY:
            if re.search(pattern, lower, re.IGNORECASE):
                issues.append(label)
        return CognitionIntegrityVerdict(integrity_ok=len(issues) == 0, issues=issues)
