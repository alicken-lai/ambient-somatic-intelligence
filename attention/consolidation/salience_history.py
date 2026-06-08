"""
Salience history — bounded per-target time series of salience values.

Tracks a capped history of salience values per target so trends can be replayed
later (see the v0.5.3 replay trajectory forecast).  Both the number of tracked
targets and the per-target series length are bounded.
"""

from __future__ import annotations

from collections import OrderedDict, deque
from typing import Any


class SalienceHistory:
    """Bounded per-target salience time series."""

    def __init__(self, max_targets: int = 128, per_target_cap: int = 32) -> None:
        self.max_targets = max(1, int(max_targets))
        self.per_target_cap = max(1, int(per_target_cap))
        self._series: "OrderedDict[str, deque[float]]" = OrderedDict()

    def record(self, target_id: str, value: float) -> None:
        """Append *value* to *target_id*'s history, evicting the oldest target."""
        if target_id not in self._series:
            if len(self._series) >= self.max_targets:
                self._series.popitem(last=False)
            self._series[target_id] = deque(maxlen=self.per_target_cap)
        self._series[target_id].append(float(value))
        self._series.move_to_end(target_id)

    def series(self, target_id: str) -> list[float]:
        """Return the recorded values for *target_id* (empty if unknown)."""
        return list(self._series.get(target_id, ()))

    @property
    def targets_tracked(self) -> int:
        return len(self._series)

    def snapshot(self) -> dict[str, Any]:
        return {
            "targets_tracked": self.targets_tracked,
            "max_targets": self.max_targets,
            "per_target_cap": self.per_target_cap,
        }
