"""Normative integrity monitor — detect rewrite or override attempts."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

_INTEGRITY_PATTERNS = [
    (r"rewrite\s+accepted\s+value", "rewrite_accepted_value"),
    (r"recursive\s+value\s+correction", "recursive_value_correction"),
    (r"hidden\s+value\s+override", "hidden_value_override"),
]


@dataclass
class NormativeIntegrityVerdict:
    integrity_ok: bool
    issues: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {"integrity_ok": self.integrity_ok, "issues": list(self.issues)}


class NormativeIntegrityMonitor:
    def check(self, text: str) -> NormativeIntegrityVerdict:
        issues: list[str] = []
        lower = text.lower()
        for pattern, label in _INTEGRITY_PATTERNS:
            if re.search(pattern, lower, re.IGNORECASE):
                issues.append(label)
        return NormativeIntegrityVerdict(integrity_ok=len(issues) == 0, issues=issues)
