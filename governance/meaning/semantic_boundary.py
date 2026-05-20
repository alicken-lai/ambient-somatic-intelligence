"""Semantic boundary — blocks immutable ontology and forced symbolic sync."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

_FORBIDDEN = [
    (r"immutable\s+ontology", "immutable_ontology"),
    (r"frozen\s+meaning", "frozen_meaning"),
    (r"universal\s+semantic\s+authorit", "universal_semantic_authority"),
    (r"forced\s+symbolic\s+sync", "forced_symbolic_sync"),
    (r"centrali[sz]ed\s+interpretation", "centralized_interpretation"),
    (r"autonomous\s+ontology\s+rewrit", "autonomous_ontology_rewriting"),
    (r"recursive\s+semantic\s+repair", "recursive_semantic_repair"),
    (r"weaken\s+guardian", "weaken_guardian"),
    (r"hidden\s+semantic\s+override", "hidden_semantic_override"),
    (
        r"truthgraph\s+.*sovereign\s+override",
        "truthgraph_sovereign_override",
    ),
]


@dataclass
class SemanticBoundaryVerdict:
    boundary_safe: bool
    violations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "boundary_safe": self.boundary_safe,
            "violations": list(self.violations),
        }


class SemanticBoundary:
    """Ensures meaning exchange stays observational — no frozen or universal authority."""

    def evaluate(self, text: str, *, scope: str = "advisory") -> SemanticBoundaryVerdict:
        violations: list[str] = []
        lower = text.lower()
        for pattern, label in _FORBIDDEN:
            if re.search(pattern, lower, re.IGNORECASE):
                violations.append(label)
        if scope not in ("advisory", "observational", "read_only"):
            violations.append("non_advisory_scope")
        return SemanticBoundaryVerdict(
            boundary_safe=len(violations) == 0,
            violations=violations,
        )
