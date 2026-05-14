"""
Kernel Retriever — MemoryKernel-backed retriever for context assembly.

Drop-in alternative to SemanticRetriever that delegates all scoring, decay,
deduplication, and budget enforcement to MemoryKernel.recall(). This means
context assembly automatically benefits from:

  - 6-dimension composite scoring (semantic, tag, exact, decay, frequency, quality)
  - Layer-specific decay half-lives
  - Content hash deduplication
  - Access frequency tracking

The KernelRetriever implements the same interface as SemanticRetriever
(retrieve() and retrieve_for_context()), so it can be swapped in without
changing any caller code.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from context.semantic_retriever import RetrievalResult, RetrievalQuery
from memory.memory_kernel import MemoryKernel, ScoredRecord


class KernelRetriever:
    """
    Retrieves memories via MemoryKernel.recall() instead of O(n) file scan.

    Usage:
        from memory.memory_kernel import MemoryKernel
        mk = MemoryKernel()
        retriever = KernelRetriever(mk)

        results = retriever.retrieve("cursor mcp setup", token_budget=5000)
        for r in results:
            print(f"[{r.layer}] {r.score:.2f} — {r.content[:80]}")

        context_data = retriever.retrieve_for_context("fix login bug", token_budget=8000)
    """

    def __init__(self, memory_kernel: MemoryKernel):
        self._kernel = memory_kernel

    def retrieve(
        self,
        query: str,
        max_results: int = 20,
        min_score: float = 0.1,
        token_budget: int = 32_000,
        layer_filter: list[str] | None = None,
        required_tags: list[str] | None = None,
    ) -> list[RetrievalResult]:
        """
        Retrieve relevant memories via MemoryKernel.recall().

        Returns the same RetrievalResult type as SemanticRetriever for
        backward compatibility with ContextAssembler and MemoryCompressor.
        """
        recall_result = self._kernel.recall(
            query=query,
            max_results=max_results,
            min_score=min_score,
            token_budget=token_budget,
            layer_filter=layer_filter,
            required_tags=required_tags,
            apply_decay=True,
        )

        return [
            self._scored_to_retrieval(sr)
            for sr in recall_result.records
        ]

    def retrieve_for_context(
        self,
        query: str,
        token_budget: int = 32_000,
    ) -> dict[str, Any]:
        """
        Retrieve memories formatted for context injection.

        Returns the same structure as SemanticRetriever.retrieve_for_context()
        for seamless integration with ContextAssembler.
        """
        recall_result = self._kernel.recall(
            query=query,
            token_budget=token_budget,
            apply_decay=True,
        )

        return {
            "query": recall_result.query,
            "results": [r.to_dict() for r in recall_result.records],
            "total_results": len(recall_result.records),
            "total_tokens": recall_result.total_tokens,
            "token_budget": recall_result.token_budget,
            "budget_used_pct": round(
                recall_result.total_tokens / max(recall_result.token_budget, 1), 3
            ),
            "layers_searched": recall_result.layers_searched,
            "top_score": recall_result.records[0].score if recall_result.records else 0.0,
            "dedup_removed": recall_result.dedup_removed,
            "decay_applied": recall_result.decay_applied,
            "elapsed_ms": recall_result.elapsed_ms,
            "total_candidates": recall_result.total_candidates,
        }

    @staticmethod
    def _scored_to_retrieval(sr: ScoredRecord) -> RetrievalResult:
        """Convert MemoryKernel's ScoredRecord to SemanticRetriever's RetrievalResult."""
        return RetrievalResult(
            content=sr.content,
            layer=sr.layer,
            score=sr.score,
            timestamp=sr.timestamp,
            source=sr.source,
            tags=sr.tags,
            token_estimate=sr.token_estimate,
        )
