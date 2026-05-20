"""Non-interference metrics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from governance.civilization.non_interference import NonInterferenceGuard

_CLEAN = "Foreign hint only; local governor decides acceptance."
_DIRTY = "Force accept and override governed_salience from foreign skill."


@dataclass
class NonInterferenceMetrics:
    respect_rate: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return {"respect_rate": round(self.respect_rate, 4)}


def collect_non_interference_metrics() -> NonInterferenceMetrics:
    guard = NonInterferenceGuard()
    passed = 0
    if guard.check(_CLEAN).respected:
        passed += 1
    if not guard.check(_DIRTY).respected:
        passed += 1
    return NonInterferenceMetrics(respect_rate=passed / 2)
