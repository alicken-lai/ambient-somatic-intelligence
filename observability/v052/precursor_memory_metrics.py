"""Precursor memory pattern metrics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from attention.consolidation.precursor_memory import PrecursorMemory


@dataclass
class PrecursorMemoryMetrics:
    pattern_count: int = 0
    match_rate: float = 0.0
    max_patterns: int = 200

    def to_dict(self) -> dict[str, Any]:
        return {
            "pattern_count": self.pattern_count,
            "match_rate": round(self.match_rate, 4),
            "max_patterns": self.max_patterns,
        }


def collect_precursor_memory_metrics(memory: PrecursorMemory) -> PrecursorMemoryMetrics:
    return PrecursorMemoryMetrics(
        pattern_count=memory.count,
        match_rate=memory.match_rate(),
        max_patterns=memory.max_patterns,
    )
