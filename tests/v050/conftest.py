"""Shared fixtures for v0.5 attention tests."""

from __future__ import annotations

import pytest

from attention.core.attention_target import AttentionTarget
from attention.kernel.attention_kernel import AttentionKernel


@pytest.fixture
def attention_kernel() -> AttentionKernel:
    return AttentionKernel(max_focus=5, max_queue=20)


@pytest.fixture
def somatic_target() -> AttentionTarget:
    return AttentionTarget(
        source_domain="somatic",
        signal_type="cpu_spike",
        raw_value=0.85,
        metadata={"urgency": 0.9},
    )


@pytest.fixture
def governance_target() -> AttentionTarget:
    return AttentionTarget(
        source_domain="governance",
        signal_type="policy_violation",
        raw_value=0.75,
        metadata={"governance_relevant": True, "governance_risk_level": "BLOCK"},
    )
