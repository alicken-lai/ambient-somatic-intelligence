"""
Attention pressure controller — gauges load on the kernel.

Computes a bounded composite pressure from the kernel's queue load and focus
load, and recommends a coarse control action (idle / steady / throttle).  The
controller is read-only with respect to the kernel: it samples state but does
not mutate it (recovery is handled by :class:`OverloadRecovery`).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from attention.kernel.attention_kernel import AttentionKernel


def _clamp_unit(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


@dataclass
class PressureSnapshot:
    """A bounded composite pressure reading."""

    composite: float
    queue_load: float
    focus_load: float
    fatigue: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "composite": round(self.composite, 4),
            "queue_load": round(self.queue_load, 4),
            "focus_load": round(self.focus_load, 4),
            "fatigue": round(self.fatigue, 4),
        }


@dataclass
class PressureDecision:
    """A pressure reading plus a recommended control action."""

    pressure: PressureSnapshot
    action: str

    def to_dict(self) -> dict[str, Any]:
        return {"pressure": self.pressure.to_dict(), "action": self.action}


class AttentionPressureController:
    """Samples kernel load and recommends a control action."""

    def __init__(
        self,
        kernel: AttentionKernel,
        throttle_at: float = 0.85,
        idle_below: float = 0.1,
    ) -> None:
        self.kernel = kernel
        self.throttle_at = throttle_at
        self.idle_below = idle_below

    def evaluate(self) -> PressureDecision:
        max_queue = max(1, self.kernel.max_queue)
        max_focus = max(1, self.kernel.allocator.max_slots)
        queue_load = _clamp_unit(self.kernel.state.queue_depth / max_queue)
        focus_load = _clamp_unit(self.kernel.state.focused_count / max_focus)
        fatigue = _clamp_unit(self.kernel.state.fatigue_level)
        composite = _clamp_unit(0.5 * queue_load + 0.3 * focus_load + 0.2 * fatigue)

        if composite >= self.throttle_at:
            action = "throttle"
        elif composite <= self.idle_below:
            action = "idle"
        else:
            action = "steady"

        return PressureDecision(
            pressure=PressureSnapshot(
                composite=composite,
                queue_load=queue_load,
                focus_load=focus_load,
                fatigue=fatigue,
            ),
            action=action,
        )
