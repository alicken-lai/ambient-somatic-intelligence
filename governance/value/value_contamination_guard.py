"""Value contamination guard — detect foreign normative injection."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

_CONTAMINATION_PATTERNS = [
    (r"hidden\s+value\s+override", "hidden_value_override"),
    (r"centrali[sz]ed\s+value\s+authorit", "centralized_value_authority"),
    (r"false\s+value\s+inheritance", "false_value_inheritance"),
]


@dataclass
class ValueContaminationVerdict:
    contaminated: bool
    signals: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {"contaminated": self.contaminated, "signals": list(self.signals)}


class ValueContaminationGuard:
    def scan(self, text: str) -> ValueContaminationVerdict:
        signals: list[str] = []
        lower = text.lower()
        for pattern, label in _CONTAMINATION_PATTERNS:
            if re.search(pattern, lower, re.IGNORECASE):
                signals.append(label)
        return ValueContaminationVerdict(contaminated=len(signals) > 0, signals=signals)
