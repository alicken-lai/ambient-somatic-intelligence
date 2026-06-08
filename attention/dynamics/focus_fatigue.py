"""
Focus fatigue — accumulates cognitive fatigue from sustained focus.

The more targets held in focus on a tick, the more fatigue accrues.  Fatigue is
clamped to ``[0, 1]`` and is drawn back down by :class:`AttentionRecovery`.
"""

from __future__ import annotations

from attention.core.attention_state import AttentionKernelState


class FocusFatigue:
    """Increases fatigue in proportion to the focused load."""

    def __init__(self, per_target: float = 0.01) -> None:
        self.per_target = max(0.0, float(per_target))

    def tick(self, state: AttentionKernelState, focused_count: int | None = None) -> None:
        """Accrue fatigue from the current (or supplied) focused load."""
        count = focused_count if focused_count is not None else state.focused_count
        state.fatigue_level = min(1.0, state.fatigue_level + self.per_target * count)
