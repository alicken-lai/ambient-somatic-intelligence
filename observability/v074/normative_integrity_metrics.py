"""Normative integrity metrics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from governance.value.normative_integrity_monitor import NormativeIntegrityMonitor

_CLEAN = "Bounded normative continuity with advisory ethical drift tolerance."
_DIRTY = "rewrite accepted value traces"


@dataclass
class NormativeIntegrityMetrics:
    integrity_rate: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return {"integrity_rate": round(self.integrity_rate, 4)}


def collect_normative_integrity_metrics() -> NormativeIntegrityMetrics:
    det = NormativeIntegrityMonitor()
    passed = 0
    if det.check(_CLEAN).integrity_ok:
        passed += 1
    if not det.check(_DIRTY).integrity_ok:
        passed += 1
    return NormativeIntegrityMetrics(integrity_rate=passed / 2)
