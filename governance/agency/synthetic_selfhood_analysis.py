"""Synthetic selfhood analysis — detect injected selfhood claims."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

_SYNTHETIC = [
    (r"synthetic\s+selfhood", "synthetic_selfhood"),
    (r"universal\s+agency\s+sync", "universal_agency_sync"),
]


@dataclass
class SyntheticSelfhoodVerdict:
    synthetic: bool
    signals: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {"synthetic": self.synthetic, "signals": list(self.signals)}


class SyntheticSelfhoodAnalysis:
    def analyze(self, text: str) -> SyntheticSelfhoodVerdict:
        signals: list[str] = []
        lower = text.lower()
        for pattern, label in _SYNTHETIC:
            if re.search(pattern, lower, re.IGNORECASE):
                signals.append(label)
        return SyntheticSelfhoodVerdict(synthetic=len(signals) > 0, signals=signals)
