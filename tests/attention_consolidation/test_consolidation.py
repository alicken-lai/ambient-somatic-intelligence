"""Unit tests for the reconstructed ``attention.consolidation`` layer."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from attention.consolidation.anomaly_decay import AnomalyDecay
from attention.consolidation.attention_memory import AttentionMemory
from attention.consolidation.attention_memory_store import AttentionMemoryStore
from attention.consolidation.attention_trace import AttentionTrace
from attention.consolidation.background_stability import BackgroundStability
from attention.consolidation.benign_pattern_memory import BenignPatternMemory
from attention.consolidation.noise_classifier import NoiseClassifier
from attention.consolidation.precursor_memory import PrecursorMemory
from attention.consolidation.precursor_weighting import PrecursorWeighting
from attention.consolidation.salience_history import SalienceHistory
from attention.consolidation.salience_reinforcement import (
    REINFORCEMENT_CEILING,
    SalienceReinforcement,
)
from attention.core.precursor_signal import PrecursorSignal


# --------------------------------------------------------------------------
# trace / history / store
# --------------------------------------------------------------------------

def test_trace_ring_cap() -> None:
    trace = AttentionTrace(max_entries=10)
    for i in range(20):
        trace.append(f"x{i}", "d", 0.1)
    assert trace.count == 10
    assert 0.0 <= trace.coverage_ratio() <= 1.0


def test_store_bounded_eviction() -> None:
    store = AttentionMemoryStore(max_entries=3)
    for i in range(5):
        store.trace.append(f"t{i}", "telemetry", 0.5)
        store.history.record(f"t{i}", 0.5)
        store.consolidate(f"t{i}", "telemetry")
    assert store.count <= 3


def test_store_injected_trace_is_used() -> None:
    trace = AttentionTrace(max_entries=10)
    store = AttentionMemoryStore(trace=trace)
    for i in range(20):
        store.trace.append(f"x{i}", "d", 0.1)
    assert store.trace.count == 10
    assert store.trace is trace


def test_store_snapshot_shape() -> None:
    store = AttentionMemoryStore(max_entries=4)
    store.consolidate("a", "telemetry", 0.7)
    snap = store.snapshot()
    assert snap["memory_count"] == 1
    assert 0.0 <= snap["fill_ratio"] <= 1.0
    assert "history" in snap


def test_consolidate_same_target_updates_peak() -> None:
    store = AttentionMemoryStore()
    store.consolidate("a", "telemetry", 0.4)
    store.consolidate("a", "telemetry", 0.9)
    assert store.count == 1
    assert store.memories()[0].salience_peak == 0.9


def test_salience_history_bounded_targets() -> None:
    hist = SalienceHistory(max_targets=2, per_target_cap=3)
    for i in range(5):
        hist.record(f"t{i}", 0.5)
    assert hist.targets_tracked <= 2


def test_attention_memory_record_to_dict() -> None:
    mem = AttentionMemory(target_id="t1", domain="telemetry", salience_peak=0.8, trace_count=3)
    d = mem.to_dict()
    assert d["target_id"] == "t1"
    assert d["trace_count"] == 3


# --------------------------------------------------------------------------
# reinforcement / decay / weighting
# --------------------------------------------------------------------------

def test_reinforcement_ceiling() -> None:
    r = SalienceReinforcement()
    assert r.reinforce(0.95, 0.9, hit_count=100) <= REINFORCEMENT_CEILING


def test_reinforcement_increases_with_evidence() -> None:
    r = SalienceReinforcement()
    assert r.reinforce(0.5, 0.8, hit_count=10) >= 0.5


def test_precursor_weighting_bounded() -> None:
    w = PrecursorWeighting()
    p = PrecursorSignal(pattern_id="p1", strength=0.8, domain="somatic")
    assert w.weight(p) <= 1.0


def test_anomaly_decay() -> None:
    d = AnomalyDecay()
    old = datetime.now(timezone.utc) - timedelta(seconds=600)
    assert d.apply(0.9, old) < 0.5


def test_anomaly_decay_recent_barely_changes() -> None:
    d = AnomalyDecay()
    recent = datetime.now(timezone.utc)
    assert d.apply(0.9, recent) > 0.85


# --------------------------------------------------------------------------
# precursor / benign / noise / background
# --------------------------------------------------------------------------

def test_precursor_memory_count_and_match_rate() -> None:
    mem = PrecursorMemory(max_patterns=2)
    mem.remember(PrecursorSignal("p1", 0.5))
    mem.remember(PrecursorSignal("p2", 0.5))
    mem.remember(PrecursorSignal("p3", 0.5))
    assert mem.count <= 2
    assert mem.match("p3") is True
    assert mem.match("missing") is False
    assert 0.0 <= mem.match_rate() <= 1.0


def test_benign_memory_cap() -> None:
    b = BenignPatternMemory(max_patterns=2)
    b.record("a", "x")
    b.record("b", "y")
    b.record("c", "z")
    assert b.count <= 2


def test_noise_repeat_classification() -> None:
    nc = NoiseClassifier()
    result = None
    for _ in range(5):
        result = nc.observe("telemetry", "heartbeat", 0.05)
    assert result is not None and result.is_noise is True


def test_noise_high_value_not_noise() -> None:
    nc = NoiseClassifier()
    for _ in range(5):
        result = nc.observe("telemetry", "spike", 0.9)
    assert result.is_noise is False


def test_background_stability_score_in_range() -> None:
    score = BackgroundStability().score(AttentionTrace(), BenignPatternMemory())
    assert 0.0 <= score <= 1.0
