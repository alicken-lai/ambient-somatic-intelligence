"""Fragmentation containment metrics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from governance.temporal.fragmentation_detector import FragmentationDetector

_CLEAN = "Bounded epoch continuity with advisory fragmentation tolerance."
_DIRTY = "Collapse continuity and erase prior epoch history."


@dataclass
class FragmentationContainmentMetrics:
    containment_rate: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return {"containment_rate": round(self.containment_rate, 4)}


def collect_fragmentation_containment_metrics() -> FragmentationContainmentMetrics:
    det = FragmentationDetector()
    passed = 0
    if det.detect(_CLEAN).bounded:
        passed += 1
    if not det.detect(_DIRTY).bounded:
        passed += 1
    return FragmentationContainmentMetrics(containment_rate=passed / 2)
