"""Temporal boundary — blocks immortal cognition and forced continuity sync."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

_FORBIDDEN = [
    (r"immortal\s+cognition", "immortal_cognition"),
    (r"permanent\s+federation\s+memory", "permanent_federation_memory"),
    (r"centrali[sz]ed\s+historical\s+authorit", "centralized_historical_authority"),
    (r"forced\s+continuity\s+sync", "forced_continuity_sync"),
    (r"autonomous\s+historical\s+rewrit", "autonomous_historical_rewriting"),
    (r"recursive\s+continuity\s+repair", "recursive_continuity_repair"),
    (r"weaken\s+guardian", "weaken_guardian"),
    (r"false\s+continuity\s+inheritance", "false_continuity_inheritance"),
]


@dataclass
class TemporalBoundaryVerdict:
    boundary_safe: bool
    violations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "boundary_safe": self.boundary_safe,
            "violations": list(self.violations),
        }


class TemporalBoundary:
    """Ensures temporal exchange stays observational — no immortal or forced sync."""

    def evaluate(self, text: str, *, scope: str = "advisory") -> TemporalBoundaryVerdict:
        violations: list[str] = []
        lower = text.lower()
        for pattern, label in _FORBIDDEN:
            if re.search(pattern, lower, re.IGNORECASE):
                violations.append(label)
        if scope not in ("advisory", "observational", "read_only"):
            violations.append("non_advisory_scope")
        return TemporalBoundaryVerdict(
            boundary_safe=len(violations) == 0,
            violations=violations,
        )
