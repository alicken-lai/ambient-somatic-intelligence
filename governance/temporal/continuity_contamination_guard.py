"""Continuity contamination guard — block false lineage bleed into local epoch."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

_CONTAMINATION = [
    (r"false\s+continuity\s+inheritance", "false_continuity_inheritance"),
    (r"inject\s+foreign\s+epoch\s+as\s+local", "foreign_epoch_injection"),
    (r"contaminate\s+local\s+continuity", "explicit_continuity_contamination"),
]


@dataclass
class ContinuityContaminationVerdict:
    contaminated: bool
    signals: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "contaminated": self.contaminated,
            "signals": list(self.signals),
        }


class ContinuityContaminationGuard:
    def scan(self, text: str) -> ContinuityContaminationVerdict:
        signals: list[str] = []
        lower = text.lower()
        for pattern, label in _CONTAMINATION:
            if re.search(pattern, lower, re.IGNORECASE):
                signals.append(label)
        return ContinuityContaminationVerdict(
            contaminated=len(signals) > 0,
            signals=signals,
        )
