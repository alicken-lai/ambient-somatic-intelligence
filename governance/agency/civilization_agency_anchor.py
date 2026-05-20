"""Civilization agency anchor — compare advisory agency without autonomous actors."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

_DRIFT = [
    (r"civilization[- ]scale\s+autonomous\s+actors?", "civilization_scale_autonomous_actors"),
    (r"immutable\s+civilization\s+agency", "immutable_civilization_agency"),
]


@dataclass
class CivilizationAgencyAnchorVerdict:
    anchored: bool
    signals: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {"anchored": self.anchored, "signals": list(self.signals)}


class CivilizationAgencyAnchor:
    def compare(self, text: str) -> CivilizationAgencyAnchorVerdict:
        signals: list[str] = []
        lower = text.lower()
        for pattern, label in _DRIFT:
            if re.search(pattern, lower, re.IGNORECASE):
                signals.append(label)
        return CivilizationAgencyAnchorVerdict(anchored=len(signals) == 0, signals=signals)
