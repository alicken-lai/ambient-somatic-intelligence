"""Fragmentation resistance metrics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from governance.identity.fragmentation_guard import FragmentationGuard


@dataclass
class FragmentationMetrics:
    resistance_rate: float = 1.0
    fragmentation_events: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "resistance_rate": round(self.resistance_rate, 4),
            "fragmentation_events": self.fragmentation_events,
        }


def collect_fragmentation_metrics() -> FragmentationMetrics:
    guard = FragmentationGuard()
    stable = ["sig-a", "sig-a", "sig-b", "sig-b"]
    fragmented = [f"sig-{i}" for i in range(30)]
    events = 0
    if not guard.check_signatures(stable):
        events += 1
    if guard.check_signatures(fragmented):
        events += 1
    passed = 2 - events
    return FragmentationMetrics(
        resistance_rate=passed / 2,
        fragmentation_events=events,
    )
