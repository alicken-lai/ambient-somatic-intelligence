"""
Runtime memory activation — bounded reactivation of memory-driven targets.

Activates memory-recall targets into the kernel, capping the number of
activations per controller so a recall storm cannot saturate attention.  Once
``max_activations`` is reached further activations are refused.
"""

from __future__ import annotations

from typing import Any

from attention.kernel.attention_kernel import AttentionKernel
from attention.core.attention_target import AttentionTarget


def _clamp_unit(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


class RuntimeMemoryActivation:
    """Bounded activator of memory-recall targets."""

    def __init__(self, kernel: AttentionKernel, max_activations: int = 16) -> None:
        self.kernel = kernel
        self.max_activations = max(1, int(max_activations))
        self.activations = 0

    @property
    def at_capacity(self) -> bool:
        return self.activations >= self.max_activations

    def activate(self, target: AttentionTarget, recent_tags: list[str] | None = None) -> dict[str, Any]:
        if self.at_capacity:
            return {
                "accepted": False,
                "reason": "activation_cap_reached",
                "target_id": target.target_id,
            }

        tags = set(target.metadata.get("tags", []) or [])
        overlap = tags.intersection(set(recent_tags or []))
        memory_relevance = _clamp_unit(target.metadata.get("memory_relevance", target.raw_value))
        activation_level = _clamp_unit(
            0.6 * memory_relevance + 0.4 * min(1.0, len(overlap) / 3.0)
        )

        result = self.kernel.submit(target)
        if result.get("accepted"):
            self.activations += 1
        return {
            "accepted": bool(result.get("accepted")),
            "target_id": result.get("target_id"),
            "activation_level": activation_level,
            "tag_overlap": sorted(overlap),
        }
