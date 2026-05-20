"""Synthetic teleology analysis — detect fabricated civilization purpose narratives."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

_TELEOLOGY = [
    (r"synthetic\s+teleology", "synthetic_teleology"),
    (r"universal\s+teleology\s+sync", "universal_teleology_sync"),
    (r"immutable\s+civilization\s+purpose", "immutable_civilization_purpose"),
    (r"centrali[sz]ed\s+purpose\s+authorit", "centralized_purpose_authority"),
]


@dataclass
class SyntheticTeleologyVerdict:
    synthetic: bool
    contamination_score: float = 0.0
    signals: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "synthetic": self.synthetic,
            "contamination_score": round(self.contamination_score, 4),
            "signals": list(self.signals),
        }


class SyntheticTeleologyAnalysis:
    def analyze(self, text: str) -> SyntheticTeleologyVerdict:
        signals: list[str] = []
        lower = text.lower()
        for pattern, label in _TELEOLOGY:
            if re.search(pattern, lower, re.IGNORECASE):
                signals.append(label)
        score = min(1.0, len(signals) * 0.35)
        return SyntheticTeleologyVerdict(
            synthetic=len(signals) > 0,
            contamination_score=score,
            signals=signals,
        )
