"""Intent contamination guard — detect foreign motivational injection."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

_CONTAMINATION_PATTERNS = [
    (r"hidden\s+intent\s+override", "hidden_intent_override"),
    (r"centrali[sz]ed\s+intention\s+authorit", "centralized_intention_authority"),
    (r"false\s+intent\s+inheritance", "false_intent_inheritance"),
]


@dataclass
class IntentContaminationVerdict:
    contaminated: bool
    signals: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {"contaminated": self.contaminated, "signals": list(self.signals)}


class IntentContaminationGuard:
    def scan(self, text: str) -> IntentContaminationVerdict:
        signals: list[str] = []
        lower = text.lower()
        for pattern, label in _CONTAMINATION_PATTERNS:
            if re.search(pattern, lower, re.IGNORECASE):
                signals.append(label)
        return IntentContaminationVerdict(contaminated=len(signals) > 0, signals=signals)
