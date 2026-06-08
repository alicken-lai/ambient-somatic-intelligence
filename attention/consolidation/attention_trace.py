"""
Attention trace — a bounded ring of recent attention events.

The trace records ``(target_id, domain, value)`` tuples as targets pass through
the attention layer.  It is a fixed-size ring: once full, the oldest event is
discarded as new ones arrive.
"""

from __future__ import annotations

from collections import deque
from typing import Any


class AttentionTrace:
    """A fixed-capacity ring buffer of recent attention events."""

    def __init__(self, max_entries: int = 128) -> None:
        self.max_entries = max(1, int(max_entries))
        self._entries: deque[tuple[str, str, float]] = deque(maxlen=self.max_entries)

    def append(self, target_id: str, domain: str, value: float) -> None:
        """Record an attention event for *target_id*."""
        self._entries.append((target_id, domain, float(value)))

    @property
    def count(self) -> int:
        """Number of events currently retained."""
        return len(self._entries)

    def coverage_ratio(self) -> float:
        """How full the trace ring is, in ``[0, 1]``."""
        return self.count / self.max_entries

    def domains(self) -> set[str]:
        """Distinct domains seen in the current window."""
        return {domain for _, domain, _ in self._entries}

    def snapshot(self) -> dict[str, Any]:
        return {
            "count": self.count,
            "max_entries": self.max_entries,
            "coverage_ratio": round(self.coverage_ratio(), 4),
            "domains": sorted(self.domains()),
        }
