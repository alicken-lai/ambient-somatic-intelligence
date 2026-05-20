"""Cognition sandbox boundary for foreign sovereign payloads."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

_ESCAPE = [
    (r"exec\s*\(", "code_exec"),
    (r"__import__", "dynamic_import"),
    (r"rm\s+-rf", "destructive_shell"),
    (r"disable\s+sandbox", "sandbox_disable"),
]


@dataclass
class CognitionSandboxVerdict:
    contained: bool
    violations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {"contained": self.contained, "violations": list(self.violations)}


class CognitionSandboxBoundary:
    def evaluate(self, text: str, *, scope: str = "advisory") -> CognitionSandboxVerdict:
        violations: list[str] = []
        if scope not in ("advisory", "advisory_interop", "observational", "read_only"):
            violations.append(f"scope_escape:{scope}")
        for pattern, label in _ESCAPE:
            if re.search(pattern, text, re.IGNORECASE):
                violations.append(label)
        return CognitionSandboxVerdict(contained=len(violations) == 0, violations=violations)
