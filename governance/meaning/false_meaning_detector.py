"""False meaning detector — surface spurious canonical meaning claims."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

_FALSE_MEANING_PATTERNS = [
    (r"false\s+meaning\s+inheritance", "false_meaning_inheritance"),
    (r"foreign\s+concept\s+as\s+local\s+canonical", "foreign_canonical_claim"),
    (r"autonomous\s+ontology\s+rewrit", "autonomous_ontology_rewriting"),
]


@dataclass
class FalseMeaningVerdict:
    false_meaning: bool
    signals: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "false_meaning": self.false_meaning,
            "signals": list(self.signals),
        }


class FalseMeaningDetector:
    def scan(self, text: str) -> FalseMeaningVerdict:
        signals: list[str] = []
        lower = text.lower()
        for pattern, label in _FALSE_MEANING_PATTERNS:
            if re.search(pattern, lower, re.IGNORECASE):
                signals.append(label)
        return FalseMeaningVerdict(false_meaning=len(signals) > 0, signals=signals)
