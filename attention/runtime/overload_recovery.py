"""
Overload recovery — restores kernel headroom after pressure spikes.

Each :meth:`step` applies :class:`AttentionRecovery` (reducing fatigue and
replenishing budget) and lets unreinforced salience decay.  Recovery is more
aggressive when the kernel is idle (empty queue, no focus).
"""

from __future__ import annotations

from typing import Any

from attention.dynamics.attention_recovery import AttentionRecovery
from attention.kernel.attention_kernel import AttentionKernel


class OverloadRecovery:
    """Drives fatigue/budget recovery and salience decay on the kernel."""

    def __init__(self, kernel: AttentionKernel, recovery: AttentionRecovery | None = None) -> None:
        self.kernel = kernel
        self.recovery = recovery or AttentionRecovery()

    def step(self) -> dict[str, Any]:
        state = self.kernel.state
        idle = state.queue_depth == 0 and state.focused_count == 0
        before_fatigue = state.fatigue_level
        before_budget = state.budget_remaining

        self.recovery.recover(state, idle=idle)
        self.kernel.apply_decay()

        return {
            "recovery": "idle" if idle else "active",
            "fatigue_level": round(state.fatigue_level, 4),
            "budget_remaining": round(state.budget_remaining, 4),
            "fatigue_delta": round(state.fatigue_level - before_fatigue, 4),
            "budget_delta": round(state.budget_remaining - before_budget, 4),
        }
