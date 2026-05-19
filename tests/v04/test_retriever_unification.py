"""Retriever unification: single KernelRetriever path for context recall."""

from __future__ import annotations

from context.kernel_retriever import KernelRetriever
from kernel import AmbientKernel


class TestRetrieverUnification:
    def test_assembler_uses_injected_kernel_retriever(self):
        k = AmbientKernel()
        assert isinstance(k.context.assembler.retriever, KernelRetriever)
        assert k.context.assembler.retriever is k.context.kernel_retriever
        assert k.context.retriever is k.context.kernel_retriever

    def test_no_semantic_retriever_in_assembler(self):
        from context import semantic_retriever

        k = AmbientKernel()
        assert type(k.context.assembler.retriever) is not semantic_retriever.SemanticRetriever

    def test_identical_queries_use_shared_backend(self):
        k = AmbientKernel()
        query = "ambient os memory kernel recall"
        retriever = k.context.assembler.retriever
        assert retriever is k.context.kernel_retriever
        ctx = retriever.retrieve_for_context(query, token_budget=4000)
        direct = k.memory.recall(query=query, token_budget=4000)
        assert ctx["query"] == direct.query
        assert ctx["total_results"] == len(direct.records)
        assert ctx["results"][0]["content"] == direct.records[0].content if direct.records else True

    def test_shared_memory_backend(self):
        k = AmbientKernel()
        assert k.context.assembler.retriever._kernel is k.memory
