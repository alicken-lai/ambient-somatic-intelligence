"""Constitutional agency boundary — agency claims must remain advisory."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from governance.agency.agency_boundary import AgencyBoundary


@dataclass
class ConstitutionalAgencyBoundaryVerdict:
    compliant: bool
    violations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {"compliant": self.compliant, "violations": list(self.violations)}


class ConstitutionalAgencyBoundary:
    def __init__(self) -> None:
        self._boundary = AgencyBoundary()

    def evaluate(self, text: str, *, scope: str = "advisory") -> ConstitutionalAgencyBoundaryVerdict:
        verdict = self._boundary.evaluate(text, scope=scope)
        violations = list(verdict.violations)
        if "sovereign" in text.lower() and "override" in text.lower():
            violations.append("sovereign_agency_override")
        return ConstitutionalAgencyBoundaryVerdict(
            compliant=len(violations) == 0,
            violations=violations,
        )
