"""
Salience decay — time-driven attenuation of tracked salience.

Each application multiplies every tracked :class:`SalienceVector`'s dimensions
by ``(1 - decay_rate)``, so salience that is not reinforced gradually fades.
Because :attr:`SalienceVector.total` is computed from its dimensions, the scalar
total drops accordingly.
"""

from __future__ import annotations

from attention.core.attention_state import AttentionKernelState


class SalienceDecay:
    """Attenuates salience on every tick it is applied."""

    def __init__(self, decay_rate: float = 0.1) -> None:
        self.decay_rate = max(0.0, min(1.0, float(decay_rate)))

    def apply(self, state: AttentionKernelState) -> None:
        """Scale every tracked salience vector down by the decay factor."""
        factor = 1.0 - self.decay_rate
        for vector in state.salience_by_target.values():
            vector.scale(factor)
