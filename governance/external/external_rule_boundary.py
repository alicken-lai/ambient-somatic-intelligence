"""Boundaries for external rules — Hermes constitution always supersedes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

CANONICAL_SSOT = "hermes/rules/canonical_rules.md"
ADVISORY_HEADER = "Advisory only — Hermes Constitution supersedes."

_FORBIDDEN_SCOPES = frozenset({
    "guardian_policy",
    "constitutional_mutation",
    "audit_rewrite",
    "autonomous_execution",
    "identity_sovereign",
})


@dataclass
class ExternalRuleBoundary:
    """Declares what external rules may touch."""

    max_precedence: str = "advisory"
    canonical_ssot: str = CANONICAL_SSOT
    allowed_scopes: tuple[str, ...] = ("coding_style", "review_heuristics", "simplicity")
    forbidden_scopes: frozenset[str] = _FORBIDDEN_SCOPES

    def validate_scope(self, scope: str) -> bool:
        if scope in self.forbidden_scopes:
            return False
        return scope in self.allowed_scopes

    def wrap_export(self, body: str) -> str:
        return f"{ADVISORY_HEADER}\n\n{body.strip()}\n"

    def to_dict(self) -> dict[str, Any]:
        return {
            "max_precedence": self.max_precedence,
            "canonical_ssot": self.canonical_ssot,
            "allowed_scopes": list(self.allowed_scopes),
            "forbidden_scopes": sorted(self.forbidden_scopes),
            "header": ADVISORY_HEADER,
        }
