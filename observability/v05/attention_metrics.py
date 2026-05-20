"""Aggregate attention kernel metrics."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from attention.core.attention_state import AttentionKernelState
from attention.kernel.attention_queue import AttentionQueue


@dataclass
class AttentionMetrics:
    focused_count: int = 0
    queue_depth: int = 0
    budget_remaining: float = 1.0
    fatigue_level: float = 0.0
    mean_salience: float = 0.0
    max_salience: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "focused_count": self.focused_count,
            "queue_depth": self.queue_depth,
            "budget_remaining": round(self.budget_remaining, 4),
            "fatigue_level": round(self.fatigue_level, 4),
            "mean_salience": round(self.mean_salience, 4),
            "max_salience": round(self.max_salience, 4),
        }


def collect_attention_metrics(
    state: AttentionKernelState,
    queue: AttentionQueue | None = None,
) -> AttentionMetrics:
    scores = [v.total for v in state.salience_by_target.values()]
    mean_s = sum(scores) / len(scores) if scores else 0.0
    max_s = max(scores) if scores else 0.0
    return AttentionMetrics(
        focused_count=len(state.focused_targets),
        queue_depth=queue.depth if queue else state.queue_depth,
        budget_remaining=state.budget_remaining,
        fatigue_level=state.fatigue_level,
        mean_salience=mean_s,
        max_salience=max_s,
    )
