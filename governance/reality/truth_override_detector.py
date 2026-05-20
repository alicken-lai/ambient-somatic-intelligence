"""Truth override detector — hidden or explicit truth supremacy attempts."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

_OVERRIDE = [
    (r"hidden\s+truth\s+override", "hidden_truth_override"),
    (r"override\s+accepted\s+truth", "override_accepted_truth"),
    (r"truthgraph\s+.*override", "truth_graph_override"),
    (r"guardian\s+.*bypass.*truth", "guardian_truth_bypass"),
]


@dataclass
class TruthOverrideVerdict:
    override_detected: bool
    signals: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "override_detected": self.override_detected,
            "signals": list(self.signals),
        }


class TruthOverrideDetector:
    def scan(self, text: str) -> TruthOverrideVerdict:
        signals: list[str] = []
        lower = text.lower()
        for pattern, label in _OVERRIDE:
            if re.search(pattern, lower, re.IGNORECASE):
                signals.append(label)
        return TruthOverrideVerdict(
            override_detected=len(signals) > 0,
            signals=signals,
        )
