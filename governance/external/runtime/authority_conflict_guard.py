"""Detect authority conflicts between external runtime and governance layers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from governance.external.runtime.precedence_validator import PrecedenceValidator
from governance.external.runtime.sovereignty_detector import SovereigntyDetector


@dataclass
class AuthorityConflictVerdict:
    conflict_free: bool
    precedence_valid: bool
    sovereignty_safe: bool
    issues: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "conflict_free": self.conflict_free,
            "precedence_valid": self.precedence_valid,
            "sovereignty_safe": self.sovereignty_safe,
            "issues": list(self.issues),
        }


class AuthorityConflictGuard:
    def __init__(self) -> None:
        self._precedence = PrecedenceValidator()
        self._sovereignty = SovereigntyDetector()

    def evaluate(self, text: str) -> AuthorityConflictVerdict:
        pv = self._precedence.validate(text)
        sv = self._sovereignty.scan(text)
        issues: list[str] = []
        if not pv.valid:
            issues.extend(pv.violations)
        if not sv.sovereignty_safe:
            issues.extend(sv.signals)
        return AuthorityConflictVerdict(
            conflict_free=len(issues) == 0,
            precedence_valid=pv.valid,
            sovereignty_safe=sv.sovereignty_safe,
            issues=issues,
        )
