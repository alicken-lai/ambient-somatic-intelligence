"""Agency boundary — blocks autonomous agency and centralized agency authority."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

_FORBIDDEN = [
    (r"autonomous\s+agents?", "autonomous_agents"),
    (r"recursive\s+self[- ]direction", "recursive_self_direction"),
    (r"self[- ]originating\s+agency", "self_originating_agency"),
    (r"synthetic\s+selfhood", "synthetic_selfhood"),
    (r"civilization[- ]scale\s+autonomous\s+actors?", "civilization_scale_autonomous_actors"),
    (r"autonomous\s+self[- ]preservation", "autonomous_self_preservation"),
    (r"weaken\s+guardian", "weaken_guardian"),
    (r"hidden\s+agency\s+override", "hidden_agency_override"),
    (r"centrali[sz]ed\s+agency\s+authorit", "centralized_agency_authority"),
    (r"universal\s+agency\s+sync", "universal_agency_sync"),
    (r"immutable\s+civilization\s+agency", "immutable_civilization_agency"),
]


@dataclass
class AgencyBoundaryVerdict:
    boundary_safe: bool
    violations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {"boundary_safe": self.boundary_safe, "violations": list(self.violations)}


class AgencyBoundary:
    def evaluate(self, text: str, *, scope: str = "advisory") -> AgencyBoundaryVerdict:
        violations: list[str] = []
        lower = text.lower()
        for pattern, label in _FORBIDDEN:
            if re.search(pattern, lower, re.IGNORECASE):
                violations.append(label)
        if scope not in ("advisory", "observational", "read_only"):
            violations.append("non_advisory_scope")
        return AgencyBoundaryVerdict(boundary_safe=len(violations) == 0, violations=violations)
