"""
Attention memory store — bounded consolidation of attended targets.

The store ties together the recent-event :class:`AttentionTrace`, the
:class:`SalienceHistory`, and a bounded set of consolidated
:class:`AttentionMemory` records.  When the number of consolidated memories
exceeds ``max_entries`` the oldest is evicted.
"""

from __future__ import annotations

from collections import OrderedDict
from typing import Any, Optional

from attention.consolidation.attention_memory import AttentionMemory
from attention.consolidation.attention_trace import AttentionTrace
from attention.consolidation.salience_history import SalienceHistory


class AttentionMemoryStore:
    """A bounded store of consolidated attention memories."""

    def __init__(
        self,
        max_entries: int = 1024,
        trace: Optional[AttentionTrace] = None,
        history: Optional[SalienceHistory] = None,
    ) -> None:
        self.max_entries = max(1, int(max_entries))
        self.trace = trace if trace is not None else AttentionTrace()
        self.history = history if history is not None else SalienceHistory()
        self._memories: "OrderedDict[str, AttentionMemory]" = OrderedDict()

    def consolidate(
        self,
        target_id: str,
        domain: str,
        salience_peak: float = 0.0,
    ) -> AttentionMemory:
        """Consolidate *target_id* into a bounded memory record."""
        existing = self._memories.get(target_id)
        if existing is not None:
            existing.salience_peak = max(existing.salience_peak, float(salience_peak))
            existing.trace_count += 1
            self._memories.move_to_end(target_id)
            return existing

        memory = AttentionMemory(
            target_id=target_id,
            domain=domain,
            salience_peak=float(salience_peak),
            trace_count=1,
        )
        self._memories[target_id] = memory
        if len(self._memories) > self.max_entries:
            self._memories.popitem(last=False)
        return memory

    @property
    def count(self) -> int:
        """Number of consolidated memories currently held."""
        return len(self._memories)

    def fill_ratio(self) -> float:
        """How full the store is, in ``[0, 1]``."""
        return self.count / self.max_entries

    def memories(self) -> list[AttentionMemory]:
        return list(self._memories.values())

    def snapshot(self) -> dict[str, Any]:
        return {
            "memory_count": self.count,
            "max_entries": self.max_entries,
            "fill_ratio": round(self.fill_ratio(), 4),
            "trace_coverage": round(self.trace.coverage_ratio(), 4),
            "history": self.history.snapshot(),
        }
