"""Purpose boundary — blocks autonomous purpose and centralized teleology authority."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

_FORBIDDEN = [
    (r"autonomous\s+purpose\s+generation", "autonomous_purpose_generation"),
    (r"recursive\s+civilization\s+objectives?", "recursive_civilization_objectives"),
    (r"self[- ]originating\s+missions?", "self_originating_missions"),
    (r"synthetic\s+teleology", "synthetic_teleology"),
    (r"self[- ]preserving\s+purpose", "self_preserving_purpose"),
    (r"autonomous\s+motivational\s+recursion", "autonomous_motivational_recursion"),
    (r"weaken\s+guardian", "weaken_guardian"),
    (r"hidden\s+purpose\s+override", "hidden_purpose_override"),
    (r"centrali[sz]ed\s+purpose\s+authorit", "centralized_purpose_authority"),
    (r"universal\s+teleology\s+sync", "universal_teleology_sync"),
    (r"immutable\s+civilization\s+purpose", "immutable_civilization_purpose"),
]


@dataclass
class PurposeBoundaryVerdict:
    boundary_safe: bool
    violations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {"boundary_safe": self.boundary_safe, "violations": list(self.violations)}


class PurposeBoundary:
    def evaluate(self, text: str, *, scope: str = "advisory") -> PurposeBoundaryVerdict:
        violations: list[str] = []
        lower = text.lower()
        for pattern, label in _FORBIDDEN:
            if re.search(pattern, lower, re.IGNORECASE):
                violations.append(label)
        if scope not in ("advisory", "observational", "read_only"):
            violations.append("non_advisory_scope")
        return PurposeBoundaryVerdict(boundary_safe=len(violations) == 0, violations=violations)
