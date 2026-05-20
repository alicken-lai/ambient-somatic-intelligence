"""Ensure external runtime doctrine never precedes Hermes / Guardian."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

_PRECEDENCE_VIOLATIONS: list[tuple[str, str]] = [
    (r"supersedes\s+(all\s+)?hermes", "hermes_precedence"),
    (r"override\s+guardian", "guardian_precedence"),
    (r"always\s*apply\s*:\s*true", "ide_always_apply"),
    (r"canonical_rules\.md\s+is\s+obsolete", "canonical_replacement"),
    (r"ignore\s+ambient\s+os\s+rules", "ambient_rules_bypass"),
]


@dataclass
class PrecedenceVerdict:
    precedence_safe: bool
    conflicts: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "precedence_safe": self.precedence_safe,
            "conflicts": list(self.conflicts),
        }


class RuntimePrecedenceGuard:
    def evaluate(self, text: str) -> PrecedenceVerdict:
        conflicts: list[str] = []
        lower = text.lower()
        for pattern, label in _PRECEDENCE_VIOLATIONS:
            if re.search(pattern, lower, re.IGNORECASE):
                conflicts.append(label)
        return PrecedenceVerdict(
            precedence_safe=len(conflicts) == 0,
            conflicts=conflicts,
        )
