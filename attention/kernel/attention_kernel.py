"""
Attention kernel — orchestrates submission, scoring, and focus selection.

The kernel is the heart of the attention layer:

- :meth:`submit` scores an incoming :class:`AttentionTarget` and queues it.
- :meth:`tick` pulls the highest-salience targets (up to ``max_focus``) into
  focus, refreshes the :class:`AttentionKernelState`, and returns a
  :class:`KernelTickResult` snapshot.

Decay, recovery and fatigue are *not* applied here; those belong to
:mod:`attention.dynamics`, which mutate the same :class:`AttentionKernelState`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from attention.core.attention_state import AttentionKernelState
from attention.core.attention_target import AttentionTarget
from attention.dynamics.salience_decay import SalienceDecay
from attention.kernel.attention_queue import AttentionQueue
from attention.kernel.salience_engine import KernelSalienceEngine


@dataclass
class FocusAllocator:
    """Tracks the finite number of focus slots the kernel can fill per tick."""

    max_slots: int = 5


@dataclass
class KernelTickResult:
    """Snapshot returned by :meth:`AttentionKernel.tick`."""

    state: AttentionKernelState
    focused_salience: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "state": self.state.to_dict(),
            "focused_salience": {
                k: round(v, 4) for k, v in self.focused_salience.items()
            },
        }


class AttentionKernel:
    """Scores, queues and focuses attention targets."""

    def __init__(self, max_focus: int = 5, max_queue: int = 20, decay_rate: float = 0.1) -> None:
        self.max_focus = max_focus
        self.max_queue = max_queue
        self.queue = AttentionQueue(max_queue=max_queue)
        self.engine = KernelSalienceEngine()
        self.allocator = FocusAllocator(max_slots=max_focus)
        self.decay = SalienceDecay(decay_rate=decay_rate)
        self.state = AttentionKernelState()
        self._targets: dict[str, AttentionTarget] = {}

    def submit(self, target: AttentionTarget) -> dict[str, Any]:
        """Score *target*, attach its salience, and enqueue it."""
        salience = self.engine.compute(target)
        target.salience = salience
        accepted = self.queue.push(target, salience.total)
        if accepted:
            self._targets[target.target_id] = target
        self.state.queue_depth = self.queue.depth
        return {
            "accepted": accepted,
            "target_id": target.target_id,
            "salience": round(salience.total, 4),
        }

    def tick(self) -> KernelTickResult:
        """Pull the top targets into focus and refresh kernel state."""
        focused: list[AttentionTarget] = []
        focused_salience: dict[str, float] = {}
        salience_by_target: dict[str, Any] = {}

        for _ in range(self.allocator.max_slots):
            target = self.queue.pop_highest()
            if target is None:
                break
            sv = target.salience or self.engine.compute(target)
            focused.append(target)
            focused_salience[target.target_id] = sv.total
            salience_by_target[target.target_id] = sv

        self.state.focused_targets = focused
        self.state.salience_by_target = salience_by_target
        self.state.queue_depth = self.queue.depth
        return KernelTickResult(state=self.state, focused_salience=focused_salience)

    def apply_decay(self) -> None:
        """Attenuate tracked salience for one tick via :class:`SalienceDecay`."""
        self.decay.apply(self.state)
