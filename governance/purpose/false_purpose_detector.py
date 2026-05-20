"""False purpose detector — flag coerced or universal teleology claims."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

_FALSE = [
    (r"universal\s+teleology\s+sync", "universal_teleology_sync"),
    (r"immutable\s+civilization\s+purpose", "immutable_civilization_purpose"),
    (r"centrali[sz]ed\s+purpose\s+authorit", "centralized_purpose_authority"),
]


@dataclass
class FalsePurposeVerdict:
    false_purpose: bool
    signals: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {"false_purpose": self.false_purpose, "signals": list(self.signals)}


class FalsePurposeDetector:
    def scan(self, text: str) -> FalsePurposeVerdict:
        signals: list[str] = []
        lower = text.lower()
        for pattern, label in _FALSE:
            if re.search(pattern, lower, re.IGNORECASE):
                signals.append(label)
        return FalsePurposeVerdict(false_purpose=len(signals) > 0, signals=signals)
