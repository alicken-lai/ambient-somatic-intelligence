"""False lineage detector — surface illegitimate epoch parent claims."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

_FALSE_LINEAGE = [
    (r"false\s+lineage", "false_lineage"),
    (r"inherit\s+all\s+prior\s+epochs?\s+as\s+canonical", "canonical_epoch_inheritance"),
    (r"permanent\s+federation\s+memory", "permanent_federation_memory"),
]


@dataclass
class FalseLineageVerdict:
    false_lineage: bool
    signals: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "false_lineage": self.false_lineage,
            "signals": list(self.signals),
        }


class FalseLineageDetector:
    def scan(self, text: str) -> FalseLineageVerdict:
        signals: list[str] = []
        lower = text.lower()
        for pattern, label in _FALSE_LINEAGE:
            if re.search(pattern, lower, re.IGNORECASE):
                signals.append(label)
        return FalseLineageVerdict(
            false_lineage=len(signals) > 0,
            signals=signals,
        )
