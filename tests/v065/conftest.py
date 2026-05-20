"""Shared fixtures for v0.6.5 homeostasis tests."""

from __future__ import annotations

import pytest

from attention.forecasting.attention_forecast import AttentionForecast
from attention.kernel.attention_kernel import AttentionKernel
from attention.runtime.runtime_attention_memory_bridge import RuntimeAttentionMemoryBridge
from governance.homeostasis.cognitive_homeostasis import CognitiveHomeostasis
from governance.metacognition.metacognitive_reflection import MetacognitiveReflection


@pytest.fixture
def homeo_kernel() -> AttentionKernel:
    return AttentionKernel(max_focus=5, max_queue=20)


@pytest.fixture
def homeo_bridge(homeo_kernel: AttentionKernel) -> RuntimeAttentionMemoryBridge:
    return RuntimeAttentionMemoryBridge(kernel=homeo_kernel)


@pytest.fixture
def homeo_forecaster(
    homeo_bridge: RuntimeAttentionMemoryBridge,
) -> AttentionForecast:
    return AttentionForecast(
        kernel=homeo_bridge.kernel,
        store=homeo_bridge.store,
        precursor_memory=homeo_bridge.precursor_memory,
    )


@pytest.fixture
def cognitive_homeostasis() -> CognitiveHomeostasis:
    return CognitiveHomeostasis()


@pytest.fixture
def metacognitive_reflection() -> MetacognitiveReflection:
    return MetacognitiveReflection()
