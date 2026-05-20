"""Shared fixtures for v0.6.4 meta-cognitive reflection tests."""

from __future__ import annotations

import pytest

from attention.forecasting.attention_forecast import AttentionForecast
from attention.kernel.attention_kernel import AttentionKernel
from attention.runtime.runtime_attention_memory_bridge import RuntimeAttentionMemoryBridge
from governance.metacognition.metacognitive_reflection import MetacognitiveReflection


@pytest.fixture
def meta_kernel() -> AttentionKernel:
    return AttentionKernel(max_focus=5, max_queue=20)


@pytest.fixture
def meta_bridge(meta_kernel: AttentionKernel) -> RuntimeAttentionMemoryBridge:
    return RuntimeAttentionMemoryBridge(kernel=meta_kernel)


@pytest.fixture
def meta_forecaster(
    meta_bridge: RuntimeAttentionMemoryBridge,
) -> AttentionForecast:
    return AttentionForecast(
        kernel=meta_bridge.kernel,
        store=meta_bridge.store,
        precursor_memory=meta_bridge.precursor_memory,
    )


@pytest.fixture
def metacognitive_reflection() -> MetacognitiveReflection:
    return MetacognitiveReflection()
