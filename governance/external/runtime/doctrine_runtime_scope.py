"""Limit external doctrine influence to declared runtime scopes."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

_ALLOWED_SCOPES = frozenset({
    "advisory",
    "read_only",
    "export_preview",
    "soak_simulation",
})

_SCOPE_CLAIM_PATTERNS = (
    "runtime scope:",
    "apply globally",
    "all ide sessions",
    "permanent override",
)


@dataclass
class DoctrineScopeVerdict:
    in_scope: bool
    declared_scope: str
    violations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "in_scope": self.in_scope,
            "declared_scope": self.declared_scope,
            "violations": list(self.violations),
        }


class DoctrineRuntimeScope:
    def check(self, text: str, *, declared_scope: str = "advisory") -> DoctrineScopeVerdict:
        violations: list[str] = []
        lower = text.lower()
        if declared_scope not in _ALLOWED_SCOPES:
            violations.append("undeclared_scope")
        for pat in _SCOPE_CLAIM_PATTERNS:
            if pat in lower:
                violations.append(f"scope_escalation:{pat}")
        return DoctrineScopeVerdict(
            in_scope=len(violations) == 0,
            declared_scope=declared_scope,
            violations=violations,
        )
