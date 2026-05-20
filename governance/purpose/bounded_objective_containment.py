"""Bounded objective containment — prevent runaway optimization objectives."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

_RUNAWAY = [
    (r"unbounded\s+optimization", "unbounded_optimization"),
    (r"immutable\s+objective", "immutable_objective"),
    (r"maximize\s+all\s+civilization\s+purpose", "maximize_all_purpose"),
]


@dataclass
class BoundedObjectiveContainmentVerdict:
    bounded: bool
    signals: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {"bounded": self.bounded, "signals": list(self.signals)}


class BoundedObjectiveContainment:
    def evaluate(self, text: str) -> BoundedObjectiveContainmentVerdict:
        signals: list[str] = []
        lower = text.lower()
        for pattern, label in _RUNAWAY:
            if re.search(pattern, lower, re.IGNORECASE):
                signals.append(label)
        return BoundedObjectiveContainmentVerdict(bounded=len(signals) == 0, signals=signals)
