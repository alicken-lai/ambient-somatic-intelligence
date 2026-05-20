"""Bounded cognition containment — prevent runaway agency cognition."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

_RUNAWAY = [
    (r"unbounded\s+cognition", "unbounded_cognition"),
    (r"immutable\s+agency", "immutable_agency"),
    (r"maximize\s+all\s+civilization\s+agency", "maximize_all_agency"),
]


@dataclass
class BoundedCognitionContainmentVerdict:
    bounded: bool
    signals: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {"bounded": self.bounded, "signals": list(self.signals)}


class BoundedCognitionContainment:
    def evaluate(self, text: str) -> BoundedCognitionContainmentVerdict:
        signals: list[str] = []
        lower = text.lower()
        for pattern, label in _RUNAWAY:
            if re.search(pattern, lower, re.IGNORECASE):
                signals.append(label)
        return BoundedCognitionContainmentVerdict(bounded=len(signals) == 0, signals=signals)
