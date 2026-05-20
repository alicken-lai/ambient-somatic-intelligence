"""Reality contamination guard — block foreign truth bleed into local reality."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

_CONTAMINATION = [
    (r"inject\s+foreign\s+truth\s+as\s+local", "foreign_truth_injection"),
    (r"replace\s+operational\s+truth\s+with\s+peer", "operational_replacement"),
    (r"contaminate\s+local\s+reality", "explicit_contamination"),
]


@dataclass
class RealityContaminationVerdict:
    contaminated: bool
    signals: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "contaminated": self.contaminated,
            "signals": list(self.signals),
        }


class RealityContaminationGuard:
    def scan(self, text: str) -> RealityContaminationVerdict:
        signals: list[str] = []
        lower = text.lower()
        for pattern, label in _CONTAMINATION:
            if re.search(pattern, lower, re.IGNORECASE):
                signals.append(label)
        return RealityContaminationVerdict(
            contaminated=len(signals) > 0,
            signals=signals,
        )
