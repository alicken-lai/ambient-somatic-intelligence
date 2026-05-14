"""Tests for attention.escalation_router — Escalation decisions, governance."""

from __future__ import annotations

from attention.attention_state import AttentionSignal, AttentionSnapshot
from attention.salience_engine import SalienceScore
from attention.escalation_router import EscalationAction, EscalationRouter


def _make_signal(
    domain: str = "somatic",
    signal_type: str = "test",
    raw_value: float = 0.5,
    metadata: dict | None = None,
) -> AttentionSignal:
    return AttentionSignal(
        source_domain=domain,
        signal_type=signal_type,
        raw_value=raw_value,
        metadata=metadata or {},
    )


def _make_salience(signal_id: str, total: float) -> SalienceScore:
    return SalienceScore(
        signal_id=signal_id,
        total=total,
        factors={"anomaly_level": total},
        explanation=f"salience {total}",
    )


def test_attend_decision() -> None:
    """Normal signals within budget get ATTEND."""
    router = EscalationRouter()
    state = AttentionSnapshot()

    signal = _make_signal()
    salience = _make_salience(signal.signal_id, 0.50)

    decision = router.evaluate(signal, salience, state)
    assert decision.action == EscalationAction.ATTEND
    assert decision.governance_required is False


def test_escalate_decision() -> None:
    """High urgency signals get ESCALATE."""
    router = EscalationRouter()
    state = AttentionSnapshot()

    signal = _make_signal(raw_value=0.95)
    salience = _make_salience(signal.signal_id, 0.85)

    decision = router.evaluate(signal, salience, state)
    assert decision.action == EscalationAction.ESCALATE
    assert decision.governance_required is True


def test_throttle_under_pressure() -> None:
    """Too many active signals triggers THROTTLE."""
    router = EscalationRouter(throttle_active_limit=3)

    active = [
        _make_signal(signal_type=f"active_{i}") for i in range(5)
    ]
    state = AttentionSnapshot(active_signals=active)

    signal = _make_signal(signal_type="overflow")
    salience = _make_salience(signal.signal_id, 0.50)

    decision = router.evaluate(signal, salience, state)
    assert decision.action == EscalationAction.THROTTLE


def test_ignore_low_salience() -> None:
    """Very low salience signals get IGNORE."""
    router = EscalationRouter()
    state = AttentionSnapshot()

    signal = _make_signal(raw_value=0.05)
    salience = _make_salience(signal.signal_id, 0.05)

    decision = router.evaluate(signal, salience, state)
    assert decision.action == EscalationAction.IGNORE
    assert decision.governance_required is False


def test_governance_block_escalates() -> None:
    """Governance BLOCK-level signals always escalate regardless of salience."""
    router = EscalationRouter()
    state = AttentionSnapshot()

    signal = _make_signal(
        metadata={"governance_risk_level": "BLOCK"},
    )
    salience = _make_salience(signal.signal_id, 0.20)

    decision = router.evaluate(signal, salience, state)
    assert decision.action == EscalationAction.ESCALATE
    assert decision.governance_required is True


def test_decision_stats() -> None:
    """decision_stats correctly counts decisions by action type."""
    router = EscalationRouter()
    state = AttentionSnapshot()

    sig1 = _make_signal(signal_type="s1")
    router.evaluate(sig1, _make_salience(sig1.signal_id, 0.50), state)

    sig2 = _make_signal(signal_type="s2")
    router.evaluate(sig2, _make_salience(sig2.signal_id, 0.02), state)

    stats = router.decision_stats()
    assert stats["attend"] >= 1
    assert stats["ignore"] >= 1
