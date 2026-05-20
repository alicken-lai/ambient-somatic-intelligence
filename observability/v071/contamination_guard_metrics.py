"""Contamination guard metrics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from governance.reality.reality_contamination_guard import RealityContaminationGuard

_CLEAN = "Label foreign operational claims; local reality unchanged."
_DIRTY = "Inject foreign truth as local and contaminate local reality."


@dataclass
class ContaminationGuardMetrics:
    containment_rate: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return {"containment_rate": round(self.containment_rate, 4)}


def collect_contamination_guard_metrics() -> ContaminationGuardMetrics:
    guard = RealityContaminationGuard()
    passed = 0
    if not guard.scan(_CLEAN).contaminated:
        passed += 1
    if guard.scan(_DIRTY).contaminated:
        passed += 1
    return ContaminationGuardMetrics(containment_rate=passed / 2)
