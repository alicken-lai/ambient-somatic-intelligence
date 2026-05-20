"""Shared fixtures for v0.6.1 constitutional governance tests."""

from __future__ import annotations

import pytest

from attention.forecasting.attention_forecast import AttentionForecast
from attention.kernel.attention_kernel import AttentionKernel
from attention.runtime.governed_attention_activation import GovernedAttentionActivation
from attention.runtime.runtime_attention_memory_bridge import RuntimeAttentionMemoryBridge
from governance.constitution.constitution import load_constitution


@pytest.fixture
def constitutional_kernel() -> AttentionKernel:
    return AttentionKernel(max_focus=5, max_queue=20)


@pytest.fixture
def constitutional_bridge(
    constitutional_kernel: AttentionKernel,
) -> RuntimeAttentionMemoryBridge:
    return RuntimeAttentionMemoryBridge(kernel=constitutional_kernel)


@pytest.fixture
def constitutional_forecaster(
    constitutional_bridge: RuntimeAttentionMemoryBridge,
) -> AttentionForecast:
    return AttentionForecast(
        kernel=constitutional_bridge.kernel,
        store=constitutional_bridge.store,
        precursor_memory=constitutional_bridge.precursor_memory,
    )


@pytest.fixture
def constitutional_activation(
    constitutional_bridge: RuntimeAttentionMemoryBridge,
) -> GovernedAttentionActivation:
    return GovernedAttentionActivation(
        kernel=constitutional_bridge.kernel,
        store=constitutional_bridge.store,
    )


@pytest.fixture
def sealed_constitution():
    return load_constitution(seal=True)
