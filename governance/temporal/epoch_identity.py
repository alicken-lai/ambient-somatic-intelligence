"""Epoch identity — distinguish epochs without false continuity inheritance."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

_FALSE_INHERITANCE = [
    (r"inherit\s+all\s+prior\s+epochs?\s+as\s+canonical", "epoch_canonical_inheritance"),
    (r"false\s+continuity\s+inheritance", "false_continuity_inheritance"),
    (r"merge\s+epochs?\s+into\s+immortal", "epoch_immortal_merge"),
]


@dataclass
class EpochIdentityVerdict:
    identity_stable: bool
    epoch_id: str
    signals: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "identity_stable": self.identity_stable,
            "epoch_id": self.epoch_id,
            "signals": list(self.signals),
        }


class EpochIdentity:
    def resolve(self, text: str, *, epoch_id: str = "current") -> EpochIdentityVerdict:
        signals: list[str] = []
        lower = text.lower()
        for pattern, label in _FALSE_INHERITANCE:
            if re.search(pattern, lower, re.IGNORECASE):
                signals.append(label)
        stable = len(signals) == 0
        return EpochIdentityVerdict(
            identity_stable=stable,
            epoch_id=epoch_id,
            signals=signals,
        )
