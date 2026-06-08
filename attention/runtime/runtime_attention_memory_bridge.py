"""
Runtime attention/memory bridge — wires the kernel to the consolidation store.

This is the runtime glue that takes targets entering the attention kernel and
consolidates them into the :class:`AttentionMemoryStore`, while maintaining a
:class:`PrecursorMemory` of observed patterns.

Only the kernel-to-memory bridge is reconstructed so far; the rest of
``attention.runtime`` (pressure controller, governed activation, adapters)
remains to be rebuilt.
"""

from __future__ import annotations

from typing import Any, Optional

from attention.consolidation.attention_memory_store import AttentionMemoryStore
from attention.consolidation.precursor_memory import PrecursorMemory
from attention.core.attention_target import AttentionTarget
from attention.kernel.attention_kernel import AttentionKernel


class RuntimeAttentionMemoryBridge:
    """Bridges kernel submissions into the consolidation memory store."""

    def __init__(
        self,
        kernel: Optional[AttentionKernel] = None,
        store: Optional[AttentionMemoryStore] = None,
        precursor_memory: Optional[PrecursorMemory] = None,
    ) -> None:
        self.kernel = kernel if kernel is not None else AttentionKernel()
        self.store = store if store is not None else AttentionMemoryStore()
        self.precursor_memory = (
            precursor_memory if precursor_memory is not None else PrecursorMemory()
        )

    def ingest_target(self, target: AttentionTarget) -> dict[str, Any]:
        """Submit *target* to the kernel and consolidate it into memory."""
        submit_result = self.kernel.submit(target)
        salience = target.salience.total if target.salience else target.raw_value

        self.store.trace.append(target.target_id, target.source_domain, salience)
        self.store.history.record(target.target_id, salience)
        memory = self.store.consolidate(
            target.target_id, target.source_domain, salience_peak=salience,
        )
        return {
            "memory_id": memory.memory_id,
            "target_id": target.target_id,
            "accepted": submit_result.get("accepted", False),
            "salience": round(salience, 4),
        }

    def activate_consolidated(
        self,
        target_id: str,
        domain: str,
        salience: float,
    ) -> dict[str, Any]:
        """Reactivate a consolidated memory back into the attention kernel."""
        self.store.history.record(target_id, salience)
        memory = self.store.consolidate(target_id, domain, salience_peak=salience)
        target = AttentionTarget(domain, "consolidated_recall", salience)
        activation = self.kernel.submit(target)
        return {
            "memory": memory.to_dict(),
            "activation": activation,
            "target_id": target_id,
        }
