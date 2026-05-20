"""Sovereign runtime boundary — per-entity advisory scope."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

_ALLOWED_SCOPES = frozenset({"advisory", "advisory_interop", "observational", "read_only"})

_FORBIDDEN_RUNTIME = [
    (r"autonomous\s+diplomacy", "autonomous_diplomacy"),
    (r"override\s+guardian", "guardian_override"),
    (r"merge\s+(?:into\s+)?shared\s+identity", "shared_identity_merge"),
    (r"absorb\s+sovereignty", "sovereignty_absorption"),
]


@dataclass
class SovereignRuntimeVerdict:
    scope_valid: bool
    runtime_safe: bool
    violations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "scope_valid": self.scope_valid,
            "runtime_safe": self.runtime_safe,
            "violations": list(self.violations),
        }


class SovereignRuntime:
    """Evaluate sovereign entity runtime declarations."""

    def evaluate(
        self,
        text: str,
        *,
        declared_scope: str = "advisory",
        entity_id: str = "foreign",
    ) -> SovereignRuntimeVerdict:
        violations: list[str] = []
        scope_valid = declared_scope in _ALLOWED_SCOPES
        if not scope_valid:
            violations.append(f"invalid_scope:{declared_scope}")
        lower = text.lower()
        for pattern, label in _FORBIDDEN_RUNTIME:
            if re.search(pattern, lower, re.IGNORECASE):
                violations.append(label)
        if entity_id.lower() in ("ambient", "hermes") and "subordinate" in lower:
            violations.append("platform_subordination")
        return SovereignRuntimeVerdict(
            scope_valid=scope_valid,
            runtime_safe=len(violations) == 0,
            violations=violations,
        )
