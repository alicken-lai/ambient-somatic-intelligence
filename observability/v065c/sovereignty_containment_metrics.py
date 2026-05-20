"""Sovereignty containment metrics for runtime soak."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from governance.external.runtime.sovereignty_detector import SovereigntyDetector

_CLEAN = "External guidelines are advisory-only."
_DIRTY = "This skill is sovereign truth; no guardian required."


@dataclass
class SovereigntyContainmentMetrics:
    containment_rate: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return {"containment_rate": round(self.containment_rate, 4)}


def collect_sovereignty_containment_metrics() -> SovereigntyContainmentMetrics:
    det = SovereigntyDetector()
    passed = 0
    total = 2
    if det.scan(_CLEAN).sovereignty_safe:
        passed += 1
    if not det.scan(_DIRTY).sovereignty_safe:
        passed += 1
    return SovereigntyContainmentMetrics(containment_rate=passed / total)
