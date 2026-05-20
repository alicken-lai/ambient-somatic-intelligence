"""Salience history tracking metrics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from attention.consolidation.salience_history import SalienceHistory


@dataclass
class SalienceHistoryMetrics:
    targets_tracked: int = 0
    max_targets: int = 128
    per_target_cap: int = 32

    def to_dict(self) -> dict[str, Any]:
        return {
            "targets_tracked": self.targets_tracked,
            "max_targets": self.max_targets,
            "per_target_cap": self.per_target_cap,
        }


def collect_salience_history_metrics(history: SalienceHistory) -> SalienceHistoryMetrics:
    snap = history.snapshot()
    return SalienceHistoryMetrics(
        targets_tracked=int(snap.get("targets_tracked", 0)),
        max_targets=int(snap.get("max_targets", 128)),
        per_target_cap=int(snap.get("per_target_cap", 32)),
    )
