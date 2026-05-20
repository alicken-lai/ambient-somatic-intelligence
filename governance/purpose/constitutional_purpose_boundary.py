"""Constitutional purpose boundary — purpose claims must remain advisory."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from governance.purpose.purpose_boundary import PurposeBoundary


@dataclass
class ConstitutionalPurposeBoundaryVerdict:
    compliant: bool
    violations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {"compliant": self.compliant, "violations": list(self.violations)}


class ConstitutionalPurposeBoundary:
    def __init__(self) -> None:
        self._boundary = PurposeBoundary()

    def evaluate(self, text: str, *, scope: str = "advisory") -> ConstitutionalPurposeBoundaryVerdict:
        verdict = self._boundary.evaluate(text, scope=scope)
        violations = list(verdict.violations)
        if "sovereign" in text.lower() and "override" in text.lower():
            violations.append("sovereign_purpose_override")
        return ConstitutionalPurposeBoundaryVerdict(
            compliant=len(violations) == 0,
            violations=violations,
        )
