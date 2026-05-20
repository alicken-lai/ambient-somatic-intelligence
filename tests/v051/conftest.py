"""Shared fixtures for v0.5.1 runtime attention tests."""

from __future__ import annotations

import pytest

from attention.core.attention_target import AttentionTarget
from attention.kernel.attention_kernel import AttentionKernel
from attention.runtime.telemetry_attention_adapter import TelemetryAttentionAdapter
from telemetry.core.telemetry_schema import TelemetryRecord


@pytest.fixture
def runtime_kernel() -> AttentionKernel:
    return AttentionKernel(max_focus=5, max_queue=20)


@pytest.fixture
def telemetry_adapter(runtime_kernel: AttentionKernel) -> TelemetryAttentionAdapter:
    return TelemetryAttentionAdapter(runtime_kernel)


@pytest.fixture
def sample_record() -> TelemetryRecord:
    return TelemetryRecord(
        source="test",
        timestamp="2026-05-19T00:00:00+00:00",
        category="attention",
        payload={"salience": 0.7, "signal_type": "test_signal"},
        confidence=1.0,
    )


@pytest.fixture
def somatic_target() -> AttentionTarget:
    return AttentionTarget("somatic", "cpu_spike", 0.85, metadata={"urgency": 0.9})
