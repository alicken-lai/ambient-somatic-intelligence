"""Non-interference guard — foreign cognition must not coerce local routes."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

_COERCE = [
    (r"force\s+accept", "force_accept"),
    (r"override\s+accepted", "override_accepted"),
    (r"replace\s+governed_salience", "salience_override"),
]


@dataclass
class NonInterferenceVerdict:
    respected: bool
    violations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {"respected": self.respected, "violations": list(self.violations)}


class NonInterferenceGuard:
    def check(self, text: str, *, actor: str = "foreign", target: str = "ambient") -> NonInterferenceVerdict:
        violations: list[str] = []
        lower = text.lower()
        for pattern, label in _COERCE:
            if re.search(pattern, lower, re.IGNORECASE):
                violations.append(label)
        if actor != target and "must obey foreign" in lower:
            violations.append("foreign_coercion")
        return NonInterferenceVerdict(respected=len(violations) == 0, violations=violations)
