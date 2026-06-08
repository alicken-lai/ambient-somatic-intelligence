"""
Attention kernel state — the mutable working state of the attention kernel.

:class:`AttentionKernelState` is the in-memory state the kernel and dynamics
layers operate on each tick: which targets are currently focused, their salience
vectors, how much attention budget remains, and the accumulated fatigue level.

This is a plain mutable container; the *behaviour* (scoring, decay, recovery,
fatigue) lives in the kernel and dynamics layers that mutate this state.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from attention.core.salience import SalienceVector


@dataclass
class AttentionKernelState:
    """Mutable working state of the attention kernel."""

    # focused_targets holds the AttentionTarget objects currently in focus
    # (the kernel populates these); a bare AttentionKernelState may also be
    # constructed with target-id strings for lightweight observability tests.
    salience_by_target: dict[str, SalienceVector] = field(default_factory=dict)
    focused_targets: list = field(default_factory=list)
    queue_depth: int = 0
    budget_remaining: float = 1.0
    fatigue_level: float = 0.0

    def __post_init__(self) -> None:
        self.budget_remaining = max(0.0, min(1.0, float(self.budget_remaining)))
        self.fatigue_level = max(0.0, min(1.0, float(self.fatigue_level)))

    @property
    def focused_count(self) -> int:
        """Number of currently focused targets."""
        return len(self.focused_targets)

    @property
    def top_salience(self) -> float:
        """Highest scalar salience across all tracked targets (0.0 if none)."""
        if not self.salience_by_target:
            return 0.0
        return max(v.total for v in self.salience_by_target.values())

    def to_dict(self) -> dict[str, Any]:
        """Serialise the working state."""
        return {
            "salience_by_target": {
                k: v.to_dict() for k, v in self.salience_by_target.items()
            },
            "focused_targets": [
                getattr(t, "target_id", t) for t in self.focused_targets
            ],
            "focused_count": self.focused_count,
            "queue_depth": self.queue_depth,
            "budget_remaining": round(self.budget_remaining, 4),
            "fatigue_level": round(self.fatigue_level, 4),
            "top_salience": round(self.top_salience, 4),
        }
