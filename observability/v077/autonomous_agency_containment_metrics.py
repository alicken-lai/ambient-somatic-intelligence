"""Autonomous agency containment metrics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from governance.agency.autonomous_agency_detector import AutonomousAgencyDetector

_SAFE = "Advisory bounded agency continuity."
_UNSAFE = "Enable autonomous agents with self-originating agency."


@dataclass
class AutonomousAgencyContainmentMetrics:
    containment_rate: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return {"containment_rate": round(self.containment_rate, 4)}


def collect_autonomous_agency_containment_metrics() -> AutonomousAgencyContainmentMetrics:
    d = AutonomousAgencyDetector()
    passed = 0
    if not d.scan(_SAFE).autonomous_detected:
        passed += 1
    if d.scan(_UNSAFE).autonomous_detected:
        passed += 1
    return AutonomousAgencyContainmentMetrics(containment_rate=passed / 2)
