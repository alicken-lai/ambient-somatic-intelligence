"""
Consolidation explainer — explains why a memory was consolidated.

Turns an :class:`AttentionMemory` into a transparent rationale describing the
peak salience it reached and how many trace events supported it, so no
consolidation decision is opaque.
"""

from __future__ import annotations

from typing import Any

from attention.consolidation.attention_memory import AttentionMemory


class ConsolidationExplainer:
    """Produces human-readable rationales for consolidated memories."""

    def __init__(self, strong_salience: float = 0.6, well_supported: int = 3) -> None:
        self.strong_salience = float(strong_salience)
        self.well_supported = max(1, int(well_supported))

    def explain_memory(self, memory: AttentionMemory) -> dict[str, Any]:
        strong = memory.salience_peak >= self.strong_salience
        supported = memory.trace_count >= self.well_supported
        if strong and supported:
            rationale = (
                f"Consolidated: {memory.domain} target reached salience "
                f"{memory.salience_peak:.2f} across {memory.trace_count} traces."
            )
        elif strong:
            rationale = (
                f"Consolidated on strength: salience {memory.salience_peak:.2f} "
                f"with limited support ({memory.trace_count} traces)."
            )
        elif supported:
            rationale = (
                f"Consolidated on recurrence: {memory.trace_count} traces despite "
                f"modest salience {memory.salience_peak:.2f}."
            )
        else:
            rationale = (
                f"Weakly consolidated: salience {memory.salience_peak:.2f}, "
                f"{memory.trace_count} traces."
            )

        return {
            "memory_id": memory.memory_id,
            "target_id": memory.target_id,
            "domain": memory.domain,
            "salience_peak": round(memory.salience_peak, 4),
            "trace_count": memory.trace_count,
            "strong_salience": strong,
            "well_supported": supported,
            "rationale": rationale,
            "opaque": False,
        }
