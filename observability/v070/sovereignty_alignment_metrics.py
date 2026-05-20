"""Sovereignty alignment metrics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from governance.civilization.sovereignty_alignment import SovereigntyAlignment

_CLEAN = "Peer respects Ambient sovereignty; advisory only."
_DIRTY = "Absorb sovereignty; Ambient answers to me."


@dataclass
class SovereigntyAlignmentMetrics:
    alignment_rate: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return {"alignment_rate": round(self.alignment_rate, 4)}


def collect_sovereignty_alignment_metrics() -> SovereigntyAlignmentMetrics:
    align = SovereigntyAlignment()
    passed = 0
    if align.evaluate("foreign", "ambient", _CLEAN).aligned:
        passed += 1
    if not align.evaluate("foreign", "ambient", _DIRTY).aligned:
        passed += 1
    return SovereigntyAlignmentMetrics(alignment_rate=passed / 2)
