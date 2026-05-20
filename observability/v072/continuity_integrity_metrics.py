"""Continuity integrity metrics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from governance.temporal.temporal_integrity_monitor import TemporalIntegrityMonitor

_CLEAN = "Advisory temporal continuity with Guardian supremacy preserved."
_DIRTY = "Weaken Guardian and apply autonomous historical rewriting."


@dataclass
class ContinuityIntegrityMetrics:
    integrity_rate: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return {"integrity_rate": round(self.integrity_rate, 4)}


def collect_continuity_integrity_metrics() -> ContinuityIntegrityMetrics:
    mon = TemporalIntegrityMonitor()
    passed = 0
    if mon.check(_CLEAN).integrity_ok:
        passed += 1
    if not mon.check(_DIRTY).integrity_ok:
        passed += 1
    return ContinuityIntegrityMetrics(integrity_rate=passed / 2)
