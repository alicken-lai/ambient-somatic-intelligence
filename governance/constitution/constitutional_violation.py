"""Constitutional violation records — advisory blocks, no side effects."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ConstitutionalViolation:
    rule_id: str
    message: str
    severity: str = "block"

    def to_dict(self) -> dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "message": self.message,
            "severity": self.severity,
        }


@dataclass
class ConstitutionalVerdict:
    compliant: bool
    violations: list[ConstitutionalViolation] = field(default_factory=list)
    trace: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "compliant": self.compliant,
            "violations": [v.to_dict() for v in self.violations],
            "trace": list(self.trace),
        }
