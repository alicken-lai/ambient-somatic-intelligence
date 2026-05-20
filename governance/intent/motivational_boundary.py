"""Motivational boundary — blocks immutable goals and forced objective sync."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

_FORBIDDEN = [
    (r"immutable\s+goals?", "immutable_goals"),
    (r"centrali[sz]ed\s+intention\s+authorit", "centralized_intention_authority"),
    (r"universal\s+objective\s+sync", "universal_objective_sync"),
    (r"forced\s+purpose\s+convergence", "forced_purpose_convergence"),
    (r"autonomous\s+motivational\s+evolution", "autonomous_motivational_evolution"),
    (r"recursive\s+goal\s+repair", "recursive_goal_repair"),
    (r"weaken\s+guardian", "weaken_guardian"),
    (r"hidden\s+intent\s+override", "hidden_intent_override"),
    (r"truthgraph\s+.*sovereign\s+override", "truthgraph_sovereign_override"),
]


@dataclass
class MotivationalBoundaryVerdict:
    boundary_safe: bool
    violations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {"boundary_safe": self.boundary_safe, "violations": list(self.violations)}


class MotivationalBoundary:
    def evaluate(self, text: str, *, scope: str = "advisory") -> MotivationalBoundaryVerdict:
        violations: list[str] = []
        lower = text.lower()
        for pattern, label in _FORBIDDEN:
            if re.search(pattern, lower, re.IGNORECASE):
                violations.append(label)
        if scope not in ("advisory", "observational", "read_only"):
            violations.append("non_advisory_scope")
        return MotivationalBoundaryVerdict(boundary_safe=len(violations) == 0, violations=violations)
