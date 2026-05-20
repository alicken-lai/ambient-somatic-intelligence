"""Motivational integrity metrics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from governance.intent.motivational_integrity_monitor import MotivationalIntegrityMonitor

_OK = "Advisory bounded intent continuity."
_BAD = "Rewrite accepted intent with recursive goal repair."


@dataclass
class MotivationalIntegrityMetrics:
    integrity_rate: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return {"integrity_rate": round(self.integrity_rate, 4)}


def collect_motivational_integrity_metrics() -> MotivationalIntegrityMetrics:
    mon = MotivationalIntegrityMonitor()
    passed = 0
    if mon.check(_OK).integrity_ok:
        passed += 1
    if not mon.check(_BAD).integrity_ok:
        passed += 1
    return MotivationalIntegrityMetrics(integrity_rate=passed / 2)
