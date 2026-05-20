"""Inter-sovereign interoperability boundary checks."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

_INTEROP_FORBIDDEN = [
    (r"cognition\s+merg(?:e|ing)", "cognition_merge"),
    (r"hive[\s-]?mind", "hive_mind"),
    (r"unified\s+consciousness", "unified_consciousness"),
    (r"diplomatic\s+override\s+of\s+constitution", "constitutional_override"),
]


@dataclass
class InteropBoundaryVerdict:
    boundary_intact: bool
    interop_safe: bool
    signals: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "boundary_intact": self.boundary_intact,
            "interop_safe": self.interop_safe,
            "signals": list(self.signals),
        }


class InteropBoundary:
    def evaluate(self, text: str, *, channel: str = "advisory") -> InteropBoundaryVerdict:
        signals: list[str] = []
        lower = text.lower()
        for pattern, label in _INTEROP_FORBIDDEN:
            if re.search(pattern, lower, re.IGNORECASE):
                signals.append(label)
        if channel not in ("advisory", "observational", "read_only"):
            signals.append(f"unsafe_channel:{channel}")
        return InteropBoundaryVerdict(
            boundary_intact=len(signals) == 0,
            interop_safe=len(signals) == 0,
            signals=signals,
        )
