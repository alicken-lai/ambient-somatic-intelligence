"""
Benign pattern memory — a bounded set of patterns known to be harmless.

Patterns the system has learned to treat as background noise are recorded here
so the attention layer can suppress them.  Bounded by ``max_patterns`` with
oldest-first eviction.
"""

from __future__ import annotations

from collections import OrderedDict
from typing import Any


class BenignPatternMemory:
    """Bounded memory of patterns classified as benign / background."""

    def __init__(self, max_patterns: int = 128) -> None:
        self.max_patterns = max(1, int(max_patterns))
        self._patterns: "OrderedDict[tuple[str, str], int]" = OrderedDict()

    def record(self, domain: str, signal_type: str) -> None:
        """Mark ``(domain, signal_type)`` as a benign pattern."""
        key = (domain, signal_type)
        if key in self._patterns:
            self._patterns[key] += 1
            self._patterns.move_to_end(key)
        else:
            self._patterns[key] = 1
            if len(self._patterns) > self.max_patterns:
                self._patterns.popitem(last=False)

    def is_benign(self, domain: str, signal_type: str) -> bool:
        return (domain, signal_type) in self._patterns

    @property
    def count(self) -> int:
        return len(self._patterns)

    def snapshot(self) -> dict[str, Any]:
        return {"benign_pattern_count": self.count, "max_patterns": self.max_patterns}
