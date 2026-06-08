"""
Precursor memory bridge — turns precursor signals into memory activations.

Converts an early :class:`PrecursorSignal` into a memory-recall
:class:`AttentionTarget` (tagging it with the precursor reference) and routes it
through :class:`RuntimeMemoryActivation`.
"""

from __future__ import annotations

from typing import Any

from attention.core.attention_target import AttentionTarget
from attention.core.precursor_signal import PrecursorSignal
from attention.runtime.runtime_memory_activation import RuntimeMemoryActivation


class PrecursorMemoryBridge:
    """Bridges precursor signals into bounded memory activation."""

    def __init__(self, activation: RuntimeMemoryActivation) -> None:
        self.activation = activation

    def from_precursor(
        self,
        precursor: PrecursorSignal,
        recent_tags: list[str] | None = None,
    ) -> dict[str, Any]:
        tags = list(precursor.metadata.get("tags", []) or [])
        target = AttentionTarget(
            source_domain=precursor.domain or "memory",
            signal_type=precursor.pattern_id,
            raw_value=precursor.strength,
            metadata={
                "tags": tags,
                "memory_relevance": precursor.strength,
                "precursor_pattern": precursor.pattern_id,
            },
            precursor_refs=[precursor.pattern_id],
        )
        return self.activation.activate(target, recent_tags=recent_tags)
