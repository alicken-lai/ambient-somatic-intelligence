"""Purpose integrity monitor — advisory integrity checks for purpose layer."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

_INTEGRITY = [
    (r"hidden\s+purpose\s+override", "hidden_purpose_override"),
    (r"weaken\s+guardian", "weaken_guardian"),
    (r"truthgraph\s+.*sovereign\s+override", "truthgraph_sovereign_override"),
]


@dataclass
class PurposeIntegrityVerdict:
    integrity_ok: bool
    issues: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {"integrity_ok": self.integrity_ok, "issues": list(self.issues)}


class PurposeIntegrityMonitor:
    def check(self, text: str) -> PurposeIntegrityVerdict:
        issues: list[str] = []
        lower = text.lower()
        for pattern, label in _INTEGRITY:
            if re.search(pattern, lower, re.IGNORECASE):
                issues.append(label)
        return PurposeIntegrityVerdict(integrity_ok=len(issues) == 0, issues=issues)
