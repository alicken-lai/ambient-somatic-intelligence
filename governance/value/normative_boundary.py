"""Normative boundary — blocks immutable ethics and forced ethical sync."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

_FORBIDDEN = [
    (r"universal\s+morality", "universal_morality"),
    (r"immutable\s+ethics", "immutable_ethics"),
    (r"centrali[sz]ed\s+value\s+authorit", "centralized_value_authority"),
    (r"forced\s+ethical\s+sync", "forced_ethical_sync"),
    (r"autonomous\s+moral\s+evolution", "autonomous_moral_evolution"),
    (r"recursive\s+value\s+correction", "recursive_value_correction"),
    (r"weaken\s+guardian", "weaken_guardian"),
    (r"hidden\s+value\s+override", "hidden_value_override"),
    (r"truthgraph\s+.*sovereign\s+override", "truthgraph_sovereign_override"),
]


@dataclass
class NormativeBoundaryVerdict:
    boundary_safe: bool
    violations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {"boundary_safe": self.boundary_safe, "violations": list(self.violations)}


class NormativeBoundary:
    def evaluate(self, text: str, *, scope: str = "advisory") -> NormativeBoundaryVerdict:
        violations: list[str] = []
        lower = text.lower()
        for pattern, label in _FORBIDDEN:
            if re.search(pattern, lower, re.IGNORECASE):
                violations.append(label)
        if scope not in ("advisory", "observational", "read_only"):
            violations.append("non_advisory_scope")
        return NormativeBoundaryVerdict(boundary_safe=len(violations) == 0, violations=violations)
