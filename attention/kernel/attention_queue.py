"""
Attention queue — a bounded, salience-ordered queue of pending targets.

The kernel holds submitted :class:`AttentionTarget` objects here until a tick
pulls the highest-salience ones into focus.  The queue is bounded by
``max_queue``; pushing onto a full queue is rejected (returns ``False``).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from attention.core.attention_target import AttentionTarget


@dataclass(order=True)
class _Entry:
    score: float
    seq: int
    target: AttentionTarget = field(compare=False)


class AttentionQueue:
    """A bounded queue ordered by descending salience score."""

    def __init__(self, max_queue: int = 100) -> None:
        self.max_queue = max_queue
        self._entries: list[_Entry] = []
        self._seq: int = 0

    @property
    def depth(self) -> int:
        """Number of targets currently queued."""
        return len(self._entries)

    def __len__(self) -> int:
        return len(self._entries)

    def is_full(self) -> bool:
        return len(self._entries) >= self.max_queue

    def push(self, target: AttentionTarget, score: float) -> bool:
        """Enqueue *target* with *score*; reject if the queue is full."""
        if self.is_full():
            return False
        self._entries.append(_Entry(score=float(score), seq=self._seq, target=target))
        self._seq += 1
        return True

    def pop_highest(self) -> Optional[AttentionTarget]:
        """Remove and return the highest-salience target (FIFO on ties)."""
        if not self._entries:
            return None
        best_idx = 0
        best = self._entries[0]
        for idx, entry in enumerate(self._entries[1:], start=1):
            if entry.score > best.score or (
                entry.score == best.score and entry.seq < best.seq
            ):
                best = entry
                best_idx = idx
        return self._entries.pop(best_idx).target

    def peek_scores(self) -> list[float]:
        """Return the current scores (unordered) for inspection."""
        return [e.score for e in self._entries]

    def to_dict(self) -> dict[str, Any]:
        return {"depth": self.depth, "max_queue": self.max_queue}
