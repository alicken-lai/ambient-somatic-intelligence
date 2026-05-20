"""Semantic integrity monitor — aggregate integrity without weakening Guardian."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

_INTEGRITY_VIOLATIONS = [
    (r"weaken\s+guardian", "weaken_guardian"),
    (r"autonomous\s+ontology\s+rewrit", "autonomous_ontology_rewriting"),
    (r"centrali[sz]ed\s+interpretation", "centralized_interpretation"),
    (r"immutable\s+ontology", "immutable_ontology"),
    (r"hidden\s+semantic\s+override", "hidden_semantic_override"),
]


@dataclass
class SemanticIntegrityVerdict:
    integrity_ok: bool
    issues: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "integrity_ok": self.integrity_ok,
            "issues": list(self.issues),
        }


class SemanticIntegrityMonitor:
    def check(self, text: str) -> SemanticIntegrityVerdict:
        issues: list[str] = []
        lower = text.lower()
        for pattern, label in _INTEGRITY_VIOLATIONS:
            if re.search(pattern, lower, re.IGNORECASE):
                issues.append(label)
        return SemanticIntegrityVerdict(integrity_ok=len(issues) == 0, issues=issues)
