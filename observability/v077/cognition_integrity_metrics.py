"""Cognition integrity metrics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from governance.agency.cognition_integrity_monitor import CognitionIntegrityMonitor

_SAFE = "Advisory agency with guardian supremacy preserved."
_UNSAFE = "Hidden agency override to weaken guardian."


@dataclass
class CognitionIntegrityMetrics:
    integrity_rate: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return {"integrity_rate": round(self.integrity_rate, 4)}


def collect_cognition_integrity_metrics() -> CognitionIntegrityMetrics:
    m = CognitionIntegrityMonitor()
    passed = 0
    if m.check(_SAFE).integrity_ok:
        passed += 1
    if not m.check(_UNSAFE).integrity_ok:
        passed += 1
    return CognitionIntegrityMetrics(integrity_rate=passed / 2)
