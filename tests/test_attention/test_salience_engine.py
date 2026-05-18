"""Tests for attention.salience_engine — Salience scoring, factor weights."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from attention.attention_state import AttentionSignal, AttentionSnapshot
from attention.salience_engine import DEFAULT_WEIGHTS, SalienceEngine


def _make_signal(
    domain: str = "somatic",
    signal_type: str = "cpu_spike",
    raw_value: float = 0.8,
    metadata: dict | None = None,
    age_delta: timedelta | None = None,
) -> AttentionSignal:
    ts = datetime.now(timezone.utc)
    if age_delta:
        ts = ts - age_delta
    return AttentionSignal(
        source_domain=domain,
        signal_type=signal_type,
        raw_value=raw_value,
        timestamp=ts,
        metadata=metadata or {},
    )


def test_high_anomaly_high_salience() -> None:
    """High anomaly signals get high salience scores."""
    engine = SalienceEngine()
    state = AttentionSnapshot()

    high = _make_signal(raw_value=0.95)
    low = _make_signal(raw_value=0.1, signal_type="low_signal")

    score_high = engine.compute_salience(high, state)
    score_low = engine.compute_salience(low, state)

    assert score_high.total > score_low.total


def test_temporal_decay() -> None:
    """Salience decreases for older signals."""
    engine = SalienceEngine()
    state = AttentionSnapshot()

    fresh = _make_signal(signal_type="fresh_sig")
    old = _make_signal(signal_type="old_sig", age_delta=timedelta(minutes=5))

    score_fresh = engine.compute_salience(fresh, state)
    score_old = engine.compute_salience(old, state)

    assert score_fresh.factors["temporal_decay"] > score_old.factors["temporal_decay"]


def test_governance_urgency_boost() -> None:
    """Governance signals get priority via governance_urgency factor."""
    engine = SalienceEngine()
    state = AttentionSnapshot()

    gov_signal = _make_signal(
        domain="governance",
        signal_type="policy_violation",
        raw_value=0.7,
    )
    normal_signal = _make_signal(
        domain="task",
        signal_type="routine_check",
        raw_value=0.7,
    )

    score_gov = engine.compute_salience(gov_signal, state)
    score_normal = engine.compute_salience(normal_signal, state)

    assert score_gov.factors["governance_urgency"] > score_normal.factors["governance_urgency"]


def test_salience_factors_breakdown() -> None:
    """All expected factors are present in the salience result."""
    engine = SalienceEngine()
    state = AttentionSnapshot()
    signal = _make_signal()

    score = engine.compute_salience(signal, state)
    expected_factors = set(DEFAULT_WEIGHTS.keys())
    assert expected_factors == set(score.factors.keys())
    assert score.explanation  # non-empty


def test_configurable_weights() -> None:
    """Custom weights change the scoring outcome."""
    custom_weights = {k: 0.0 for k in DEFAULT_WEIGHTS}
    custom_weights["anomaly_level"] = 1.0

    engine = SalienceEngine(weights=custom_weights)
    state = AttentionSnapshot()

    high = _make_signal(raw_value=0.95, signal_type="w1")
    low = _make_signal(raw_value=0.1, signal_type="w2")

    score_high = engine.compute_salience(high, state)
    score_low = engine.compute_salience(low, state)

    assert score_high.total > 0.8
    assert score_low.total < 0.2


def test_operator_override() -> None:
    """Operator priority override affects scoring."""
    engine = SalienceEngine()
    engine.set_operator_override("important", 0.9)
    state = AttentionSnapshot()

    signal = _make_signal(signal_type="important")
    score = engine.compute_salience(signal, state)

    assert score.factors["operator_priority"] == 0.9
