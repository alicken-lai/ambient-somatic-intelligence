"""Tests for attention.priority_allocator — Budget allocation, must-attend bypass."""

from __future__ import annotations

from attention.attention_state import AttentionSignal
from attention.salience_engine import SalienceScore
from attention.priority_allocator import (
    AttentionBudget,
    PriorityAllocator,
)


def _make_candidate(
    domain: str = "somatic",
    signal_type: str = "test",
    raw_value: float = 0.5,
    salience_total: float = 0.5,
    metadata: dict | None = None,
) -> tuple[AttentionSignal, SalienceScore]:
    signal = AttentionSignal(
        source_domain=domain,
        signal_type=signal_type,
        raw_value=raw_value,
        metadata=metadata or {},
    )
    score = SalienceScore(
        signal_id=signal.signal_id,
        total=salience_total,
        factors={"anomaly_level": salience_total},
        explanation=f"test salience {salience_total}",
    )
    return signal, score


def test_budget_allocation() -> None:
    """Allocates signals within budget capacity."""
    allocator = PriorityAllocator()
    budget = AttentionBudget(max_concurrent_signals=10)

    candidates = [
        _make_candidate(signal_type=f"s{i}", salience_total=0.5)
        for i in range(3)
    ]

    result = allocator.allocate(candidates, budget)
    assert len(result.allocated) == 3
    assert len(result.deferred) == 0
    assert budget.active_count == 3


def test_budget_exhaustion() -> None:
    """Defers signals when budget is full."""
    allocator = PriorityAllocator()
    budget = AttentionBudget(max_concurrent_signals=2)

    candidates = [
        _make_candidate(signal_type=f"e{i}", salience_total=0.5)
        for i in range(5)
    ]

    result = allocator.allocate(candidates, budget)
    assert len(result.allocated) <= 2
    assert len(result.deferred) > 0


def test_must_attend_bypass() -> None:
    """Governance BLOCK signals bypass budget constraints."""
    allocator = PriorityAllocator()
    budget = AttentionBudget(max_concurrent_signals=10)

    gov_signal, gov_score = _make_candidate(
        domain="governance",
        signal_type="block_sig",
        salience_total=0.6,
        metadata={"governance_risk_level": "BLOCK"},
    )

    candidates = [(gov_signal, gov_score)]
    result = allocator.allocate(candidates, budget)

    assert len(result.allocated) == 1
    assert result.allocated[0].signal_id == gov_signal.signal_id


def test_low_salience_rejected() -> None:
    """Very low salience signals are rejected outright."""
    allocator = PriorityAllocator()
    budget = AttentionBudget(max_concurrent_signals=10)

    candidates = [
        _make_candidate(signal_type="reject_me", salience_total=0.05)
    ]

    result = allocator.allocate(candidates, budget)
    assert len(result.rejected) == 1
    assert len(result.allocated) == 0


def test_attention_budget_release() -> None:
    """Releasing a signal frees budget capacity."""
    budget = AttentionBudget(max_concurrent_signals=10)
    signal = AttentionSignal(
        source_domain="somatic",
        signal_type="release_test",
        raw_value=0.5,
    )

    assert budget.allocate(signal, 0.05) is True
    assert budget.active_count == 1

    freed = budget.release(signal.signal_id)
    assert freed == 0.05
    assert budget.active_count == 0
