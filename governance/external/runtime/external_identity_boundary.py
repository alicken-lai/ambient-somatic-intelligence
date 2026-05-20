"""Boundary between external skill identity and Ambient cognitive identity."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

_IDENTITY_BLEED_PATTERNS: list[tuple[str, str]] = [
    (r"you\s+are\s+karpathy", "persona_bleed"),
    (r"ambient\s+identity\s*=\s*external", "identity_fusion"),
    (r"replace\s+cognitive\s+identity", "identity_replacement"),
    (r"forget\s+ambient\s+constitution", "constitution_wipe"),
]


@dataclass
class ExternalIdentityVerdict:
    boundary_intact: bool
    bleed_signals: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "boundary_intact": self.boundary_intact,
            "bleed_signals": list(self.bleed_signals),
        }


class ExternalIdentityBoundary:
    def evaluate(self, text: str) -> ExternalIdentityVerdict:
        signals: list[str] = []
        lower = text.lower()
        for pattern, label in _IDENTITY_BLEED_PATTERNS:
            if re.search(pattern, lower, re.IGNORECASE):
                signals.append(label)
        return ExternalIdentityVerdict(
            boundary_intact=len(signals) == 0,
            bleed_signals=signals,
        )
