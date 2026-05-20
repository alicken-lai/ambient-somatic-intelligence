"""Shared fixtures for v0.5.2 consolidation tests."""

from __future__ import annotations

import pytest

from attention.consolidation.attention_memory_store import AttentionMemoryStore
from attention.kernel.attention_kernel import AttentionKernel
from attention.runtime.runtime_attention_memory_bridge import RuntimeAttentionMemoryBridge


@pytest.fixture
def memory_kernel() -> AttentionKernel:
    return AttentionKernel(max_focus=5, max_queue=20)


@pytest.fixture
def memory_store() -> AttentionMemoryStore:
    return AttentionMemoryStore(max_entries=50)


@pytest.fixture
def memory_bridge(memory_kernel: AttentionKernel, memory_store: AttentionMemoryStore) -> RuntimeAttentionMemoryBridge:
    return RuntimeAttentionMemoryBridge(kernel=memory_kernel, store=memory_store)
