"""Shared fixtures for v0.6.0 cognitive governance tests."""

from __future__ import annotations

import pytest

from attention.forecasting.attention_forecast import AttentionForecast
from attention.kernel.attention_kernel import AttentionKernel
from attention.runtime.governed_attention_activation import GovernedAttentionActivation
from attention.runtime.runtime_attention_memory_bridge import RuntimeAttentionMemoryBridge


@pytest.fixture
def governance_kernel() -> AttentionKernel:
    return AttentionKernel(max_focus=5, max_queue=20)


@pytest.fixture
def governance_bridge(governance_kernel: AttentionKernel) -> RuntimeAttentionMemoryBridge:
    return RuntimeAttentionMemoryBridge(kernel=governance_kernel)


@pytest.fixture
def governed_forecaster(governance_bridge: RuntimeAttentionMemoryBridge) -> AttentionForecast:
    return AttentionForecast(
        kernel=governance_bridge.kernel,
        store=governance_bridge.store,
        precursor_memory=governance_bridge.precursor_memory,
    )


@pytest.fixture
def governed_activation(governance_bridge: RuntimeAttentionMemoryBridge) -> GovernedAttentionActivation:
    return GovernedAttentionActivation(
        kernel=governance_bridge.kernel,
        store=governance_bridge.store,
    )
