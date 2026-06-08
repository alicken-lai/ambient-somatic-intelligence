"""
Precursor memory — a bounded store of recognised precursor patterns.

Accumulates :class:`PrecursorSignal` patterns so the forecasting layer can match
new signals against historically observed precursors.  Tracks a running match
rate (matched lookups / total lookups).
"""

from __future__ import annotations

from collections import OrderedDict
from typing import Any

from attention.core.precursor_signal import PrecursorSignal


class PrecursorMemory:
    """Bounded memory of precursor patterns with a running match rate."""

    def __init__(self, max_patterns: int = 200) -> None:
        self.max_patterns = max(1, int(max_patterns))
        self._patterns: "OrderedDict[str, PrecursorSignal]" = OrderedDict()
        self._lookups: int = 0
        self._matches: int = 0

    def remember(self, signal: PrecursorSignal) -> None:
        """Store (or refresh) a precursor pattern, evicting the oldest."""
        key = signal.pattern_id
        if key in self._patterns:
            self._patterns.move_to_end(key)
        self._patterns[key] = signal
        if len(self._patterns) > self.max_patterns:
            self._patterns.popitem(last=False)

    def match(self, pattern_id: str) -> bool:
        """Look up a pattern, updating the running match rate."""
        self._lookups += 1
        hit = pattern_id in self._patterns
        if hit:
            self._matches += 1
        return hit

    def match_rate(self) -> float:
        """Fraction of lookups that matched a known pattern."""
        if self._lookups == 0:
            return 0.0
        return self._matches / self._lookups

    @property
    def count(self) -> int:
        return len(self._patterns)

    def snapshot(self) -> dict[str, Any]:
        return {
            "pattern_count": self.count,
            "max_patterns": self.max_patterns,
            "match_rate": round(self.match_rate(), 4),
        }
