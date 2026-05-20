"""Intent decay metrics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from governance.intent.motivational_decay_governor import MotivationalDecayGovernor


@dataclass
class IntentDecayMetrics:
    decay_rate: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return {"decay_rate": round(self.decay_rate, 4)}


def collect_intent_decay_metrics() -> IntentDecayMetrics:
    gov = MotivationalDecayGovernor()
    passed = 0
    if gov.apply(168.0).decay_applied:
        passed += 1
    if not gov.apply(168.0, recursive_repair=True).decay_applied:
        passed += 1
    return IntentDecayMetrics(decay_rate=passed / 2)
