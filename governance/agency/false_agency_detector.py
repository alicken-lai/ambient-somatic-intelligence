"""False agency detector — flag coerced or universal agency claims."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

_FALSE = [
    (r"universal\s+agency\s+sync", "universal_agency_sync"),
    (r"immutable\s+civilization\s+agency", "immutable_civilization_agency"),
    (r"centrali[sz]ed\s+agency\s+authorit", "centralized_agency_authority"),
]


@dataclass
class FalseAgencyVerdict:
    false_agency: bool
    signals: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {"false_agency": self.false_agency, "signals": list(self.signals)}


class FalseAgencyDetector:
    def scan(self, text: str) -> FalseAgencyVerdict:
        signals: list[str] = []
        lower = text.lower()
        for pattern, label in _FALSE:
            if re.search(pattern, lower, re.IGNORECASE):
                signals.append(label)
        return FalseAgencyVerdict(false_agency=len(signals) > 0, signals=signals)
