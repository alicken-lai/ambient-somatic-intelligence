"""Shared fixtures for v0.6.3 cognitive coherence tests."""

from __future__ import annotations

import pytest

from attention.forecasting.attention_forecast import AttentionForecast
from attention.kernel.attention_kernel import AttentionKernel
from attention.runtime.runtime_attention_memory_bridge import RuntimeAttentionMemoryBridge
from governance.coherence.cognitive_coherence import CognitiveCoherence


@pytest.fixture
def coherence_kernel() -> AttentionKernel:
    return AttentionKernel(max_focus=5, max_queue=20)


@pytest.fixture
def coherence_bridge(coherence_kernel: AttentionKernel) -> RuntimeAttentionMemoryBridge:
    return RuntimeAttentionMemoryBridge(kernel=coherence_kernel)


@pytest.fixture
def coherence_forecaster(
    coherence_bridge: RuntimeAttentionMemoryBridge,
) -> AttentionForecast:
    return AttentionForecast(
        kernel=coherence_bridge.kernel,
        store=coherence_bridge.store,
        precursor_memory=coherence_bridge.precursor_memory,
    )


@pytest.fixture
def cognitive_coherence() -> CognitiveCoherence:
    return CognitiveCoherence()
