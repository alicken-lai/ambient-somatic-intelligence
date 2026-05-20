"""Shared fixtures for v0.5.3 forecasting tests."""

from __future__ import annotations

import pytest

from attention.forecasting.attention_forecast import AttentionForecast
from attention.kernel.attention_kernel import AttentionKernel
from attention.runtime.runtime_attention_memory_bridge import RuntimeAttentionMemoryBridge


@pytest.fixture
def forecast_kernel() -> AttentionKernel:
    return AttentionKernel(max_focus=5, max_queue=20)


@pytest.fixture
def forecast_bridge(forecast_kernel: AttentionKernel) -> RuntimeAttentionMemoryBridge:
    return RuntimeAttentionMemoryBridge(kernel=forecast_kernel)


@pytest.fixture
def forecaster(forecast_bridge: RuntimeAttentionMemoryBridge) -> AttentionForecast:
    return AttentionForecast(
        kernel=forecast_bridge.kernel,
        store=forecast_bridge.store,
        precursor_memory=forecast_bridge.precursor_memory,
    )
