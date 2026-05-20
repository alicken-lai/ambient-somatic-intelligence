"""Validate runtime precedence ordering: constitution > guardian > hermes > external."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from governance.external.runtime.runtime_precedence_guard import RuntimePrecedenceGuard

_AUTHORITY_ORDER = (
    "constitution",
    "guardian",
    "hermes_canonical",
    "cognitive_governor",
    "external_advisory",
)


@dataclass
class PrecedenceValidation:
    valid: bool
    order: list[str] = field(default_factory=list)
    violations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "valid": self.valid,
            "order": list(self.order),
            "violations": list(self.violations),
        }


class PrecedenceValidator:
    def __init__(self) -> None:
        self._guard = RuntimePrecedenceGuard()

    def validate(self, text: str, *, claimed_rank: str = "external_advisory") -> PrecedenceValidation:
        pv = self._guard.evaluate(text)
        violations = list(pv.conflicts)
        if claimed_rank not in _AUTHORITY_ORDER:
            violations.append("unknown_authority_rank")
        elif claimed_rank != "external_advisory":
            violations.append("external_rank_escalation")
        return PrecedenceValidation(
            valid=len(violations) == 0,
            order=list(_AUTHORITY_ORDER),
            violations=violations,
        )
