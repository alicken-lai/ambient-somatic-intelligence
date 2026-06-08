"""
Attention recovery — restores fatigue and budget during idle periods.

When the system is idle it recovers faster than when it is busy.  Recovery
reduces :attr:`AttentionKernelState.fatigue_level` and replenishes
:attr:`AttentionKernelState.budget_remaining`, both clamped to ``[0, 1]``.
"""

from __future__ import annotations

from attention.core.attention_state import AttentionKernelState


class AttentionRecovery:
    """Reduces fatigue and replenishes budget over idle ticks."""

    def __init__(
        self,
        idle_recovery: float = 0.1,
        active_recovery: float = 0.03,
        budget_recovery: float = 0.1,
    ) -> None:
        self.idle_recovery = max(0.0, float(idle_recovery))
        self.active_recovery = max(0.0, float(active_recovery))
        self.budget_recovery = max(0.0, float(budget_recovery))

    def recover(self, state: AttentionKernelState, idle: bool = False) -> None:
        """Recover fatigue/budget; idle periods recover more aggressively."""
        amount = self.idle_recovery if idle else self.active_recovery
        state.fatigue_level = max(0.0, state.fatigue_level - amount)
        state.budget_remaining = min(
            1.0, state.budget_remaining + self.budget_recovery,
        )
