"""
Runtime somatic attention — submits live somatic signals into the kernel.

Wraps the :class:`SomaticAttentionAdapter` with the current somatic stress
level and forwards converted targets into an :class:`AttentionKernel`,
returning the kernel's acceptance decision.
"""

from __future__ import annotations

from typing import Any

from attention.attention_state import AttentionSignal
from attention.kernel.attention_kernel import AttentionKernel
from attention.somatic.somatic_attention_adapter import SomaticAttentionAdapter


def _clamp_unit(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


class RuntimeSomaticAttention:
    """Live submission path from the somatic subsystem into the kernel."""

    def __init__(self, kernel: AttentionKernel, stress: float = 0.0) -> None:
        self.kernel = kernel
        self.adapter = SomaticAttentionAdapter()
        self.adapter.update_stress(stress)

    def set_stress(self, stress: float) -> None:
        self.adapter.update_stress(stress)

    @property
    def stress(self) -> float:
        return self.adapter.stress

    def submit_signal(self, signal: AttentionSignal) -> dict[str, Any]:
        target = self.adapter.from_signal(signal)
        result = self.kernel.submit(target)
        return {
            "accepted": bool(result["accepted"]),
            "target_id": result["target_id"],
            "salience": result.get("salience"),
            "stress": self.adapter.stress,
        }
