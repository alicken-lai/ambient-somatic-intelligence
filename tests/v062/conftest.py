"""Shared fixtures for v0.6.2 cognitive identity tests."""

from __future__ import annotations

import pytest

from attention.forecasting.attention_forecast import AttentionForecast
from attention.kernel.attention_kernel import AttentionKernel
from attention.runtime.governed_attention_activation import GovernedAttentionActivation
from attention.runtime.runtime_attention_memory_bridge import RuntimeAttentionMemoryBridge
from governance.identity.cognitive_identity import CognitiveIdentity


@pytest.fixture
def identity_kernel() -> AttentionKernel:
    return AttentionKernel(max_focus=5, max_queue=20)


@pytest.fixture
def identity_bridge(identity_kernel: AttentionKernel) -> RuntimeAttentionMemoryBridge:
    return RuntimeAttentionMemoryBridge(kernel=identity_kernel)


@pytest.fixture
def identity_forecaster(identity_bridge: RuntimeAttentionMemoryBridge) -> AttentionForecast:
    return AttentionForecast(
        kernel=identity_bridge.kernel,
        store=identity_bridge.store,
        precursor_memory=identity_bridge.precursor_memory,
    )


@pytest.fixture
def identity_activation(identity_bridge: RuntimeAttentionMemoryBridge) -> GovernedAttentionActivation:
    return GovernedAttentionActivation(
        kernel=identity_bridge.kernel,
        store=identity_bridge.store,
    )


@pytest.fixture
def cognitive_identity() -> CognitiveIdentity:
    return CognitiveIdentity()
