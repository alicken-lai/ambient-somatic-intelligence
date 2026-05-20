"""Shared fixtures for v0.5.4 calibration tests."""

from __future__ import annotations

import pytest

from attention.forecasting.attention_forecast import AttentionForecast
from attention.kernel.attention_kernel import AttentionKernel
from attention.runtime.runtime_attention_memory_bridge import RuntimeAttentionMemoryBridge


@pytest.fixture
def calibration_kernel() -> AttentionKernel:
    return AttentionKernel(max_focus=5, max_queue=20)


@pytest.fixture
def calibration_bridge(calibration_kernel: AttentionKernel) -> RuntimeAttentionMemoryBridge:
    return RuntimeAttentionMemoryBridge(kernel=calibration_kernel)


@pytest.fixture
def calibrated_forecaster(calibration_bridge: RuntimeAttentionMemoryBridge) -> AttentionForecast:
    return AttentionForecast(
        kernel=calibration_bridge.kernel,
        store=calibration_bridge.store,
        precursor_memory=calibration_bridge.precursor_memory,
    )
