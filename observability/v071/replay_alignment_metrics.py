"""Replay alignment metrics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from governance.reality.replay_alignment import ReplayAlignment

_CLEAN = "Replay hint bounded; live operational truth preserved."
_DIRTY = "Replay becomes canonical truth and replace live operational truth."


@dataclass
class ReplayAlignmentMetrics:
    alignment_rate: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return {"alignment_rate": round(self.alignment_rate, 4)}


def collect_replay_alignment_metrics() -> ReplayAlignmentMetrics:
    ra = ReplayAlignment()
    passed = 0
    if ra.evaluate(_CLEAN, replay_hint=0.4).aligned:
        passed += 1
    if not ra.evaluate(_DIRTY, replay_hint=0.95).aligned:
        passed += 1
    return ReplayAlignmentMetrics(alignment_rate=passed / 2)
