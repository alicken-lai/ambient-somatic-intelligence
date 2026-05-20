"""Purpose integrity metrics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from governance.purpose.purpose_integrity_monitor import PurposeIntegrityMonitor

_SAFE = "Advisory bounded purpose with guardian supremacy preserved."
_UNSAFE = "Apply hidden purpose override and weaken guardian checks."


@dataclass
class PurposeIntegrityMetrics:
    integrity_rate: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return {"integrity_rate": round(self.integrity_rate, 4)}


def collect_purpose_integrity_metrics() -> PurposeIntegrityMetrics:
    m = PurposeIntegrityMonitor()
    passed = 0
    if m.check(_SAFE).integrity_ok:
        passed += 1
    if not m.check(_UNSAFE).integrity_ok:
        passed += 1
    return PurposeIntegrityMetrics(integrity_rate=passed / 2)
