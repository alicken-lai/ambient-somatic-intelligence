"""Memory consolidation pressure — bounded store fill + trace load."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from attention.consolidation.attention_memory_store import AttentionMemoryStore


@dataclass
class MemoryConsolidationPressure:
    composite: float = 0.0
    store_fill: float = 0.0
    trace_load: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "composite": round(self.composite, 4),
            "store_fill": round(self.store_fill, 4),
            "trace_load": round(self.trace_load, 4),
        }


def compute_memory_consolidation_pressure(store: AttentionMemoryStore) -> MemoryConsolidationPressure:
    store_fill = store.fill_ratio()
    trace_load = store.trace.coverage_ratio()
    composite = min(1.0, 0.6 * store_fill + 0.4 * trace_load)
    return MemoryConsolidationPressure(
        composite=composite,
        store_fill=store_fill,
        trace_load=trace_load,
    )
