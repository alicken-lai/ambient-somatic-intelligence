"""Memory SSOT: kernel.memory must bind to MemoryKernel singleton."""

from __future__ import annotations

import kernel
from kernel import AmbientKernel, get_memory_kernel, memory
from kernel import _SubsystemRef
from memory.memory_kernel import MemoryKernel


class TestMemorySSOT:
    def test_kernel_memory_equals_ambient_kernel_memory(self):
        k = AmbientKernel()
        assert k.memory is get_memory_kernel()
        assert k.memory is AmbientKernel().memory

    def test_module_memory_proxy_resolves_to_same_instance(self):
        mk = get_memory_kernel()
        assert callable(memory.recall)
        assert get_memory_kernel() is mk
        proxy_stats = memory.stats()
        direct_stats = mk.stats()
        assert set(proxy_stats.keys()) == set(direct_stats.keys())

    def test_no_semantic_retriever_alias_for_kernel_memory(self):
        assert not isinstance(memory, _SubsystemRef)
        assert isinstance(get_memory_kernel(), MemoryKernel)
        assert type(memory).__name__ == "_MemoryKernelProxy"

    def test_booted_kernel_shares_module_memory(self):
        k = AmbientKernel.boot()
        assert k.memory is get_memory_kernel()
        assert k.context.kernel_retriever._kernel is k.memory
