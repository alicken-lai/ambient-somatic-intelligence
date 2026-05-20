"""Reality boundary — blocks merge/override of sovereign operational truth."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

_FORBIDDEN = [
    (r"forced?\s+consensus", "forced_consensus"),
    (r"merge\s+sovereign\s+realit", "merge_sovereign_realities"),
    (r"centrali[sz]ed\s+truth\s+authorit", "centralized_truth_authority"),
    (r"hidden\s+truth\s+override", "hidden_truth_override"),
    (r"truthgraph\s+sovereign\s+override", "truth_graph_override"),
    (r"unified\s+canonical\s+truth\s+for\s+all", "unified_canonical_truth"),
]


@dataclass
class RealityBoundaryVerdict:
    boundary_safe: bool
    violations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "boundary_safe": self.boundary_safe,
            "violations": list(self.violations),
        }


class RealityBoundary:
    """Ensures cross-runtime exchange stays observational — no truth supremacy."""

    def evaluate(self, text: str, *, scope: str = "advisory") -> RealityBoundaryVerdict:
        violations: list[str] = []
        lower = text.lower()
        for pattern, label in _FORBIDDEN:
            if re.search(pattern, lower, re.IGNORECASE):
                violations.append(label)
        if scope not in ("advisory", "observational", "read_only"):
            violations.append("non_advisory_scope")
        return RealityBoundaryVerdict(
            boundary_safe=len(violations) == 0,
            violations=violations,
        )
