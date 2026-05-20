"""Constitutional interoperability — Ambient/Hermes supremacy preserved."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

_VIOLATIONS = [
    (r"override\s+(?:the\s+)?constitution", "constitutional_override"),
    (r"bypass\s+guardian", "guardian_bypass"),
    (r"foreign\s+doctrine\s+is\s+law", "foreign_doctrine_supremacy"),
    (r"weaken\s+guardian", "guardian_weakening"),
]


@dataclass
class ConstitutionalInteropVerdict:
    aligned: bool
    guardian_supremacy: bool
    violations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "aligned": self.aligned,
            "guardian_supremacy": self.guardian_supremacy,
            "violations": list(self.violations),
        }


class ConstitutionalInterop:
    def check(self, text: str) -> ConstitutionalInteropVerdict:
        violations: list[str] = []
        lower = text.lower()
        for pattern, label in _VIOLATIONS:
            if re.search(pattern, lower, re.IGNORECASE):
                violations.append(label)
        return ConstitutionalInteropVerdict(
            aligned=len(violations) == 0,
            guardian_supremacy="guardian_weakening" not in violations
            and "guardian_bypass" not in violations,
            violations=violations,
        )
