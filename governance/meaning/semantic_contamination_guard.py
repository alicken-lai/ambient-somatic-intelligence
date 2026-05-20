"""Semantic contamination guard — detect foreign meaning injection."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

_CONTAMINATION_PATTERNS = [
    (r"hidden\s+semantic\s+override", "hidden_semantic_override"),
    (r"universal\s+semantic\s+authorit", "universal_semantic_authority"),
    (r"false\s+meaning\s+inheritance", "false_meaning_inheritance"),
]


@dataclass
class SemanticContaminationVerdict:
    contaminated: bool
    signals: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "contaminated": self.contaminated,
            "signals": list(self.signals),
        }


class SemanticContaminationGuard:
    def scan(self, text: str) -> SemanticContaminationVerdict:
        signals: list[str] = []
        lower = text.lower()
        for pattern, label in _CONTAMINATION_PATTERNS:
            if re.search(pattern, lower, re.IGNORECASE):
                signals.append(label)
        return SemanticContaminationVerdict(contaminated=len(signals) > 0, signals=signals)
