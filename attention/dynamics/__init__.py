"""
attention.dynamics — time-driven mutation of the attention kernel state.

These operators mutate an :class:`attention.core.attention_state.AttentionKernelState`
in place each tick:

- :class:`SalienceDecay`     — fades unreinforced salience
- :class:`AttentionRecovery` — restores fatigue and budget when idle
- :class:`FocusFatigue`      — accrues fatigue from sustained focus
"""

from attention.dynamics.attention_recovery import AttentionRecovery
from attention.dynamics.focus_fatigue import FocusFatigue
from attention.dynamics.salience_decay import SalienceDecay

__all__ = [
    "AttentionRecovery",
    "FocusFatigue",
    "SalienceDecay",
]
