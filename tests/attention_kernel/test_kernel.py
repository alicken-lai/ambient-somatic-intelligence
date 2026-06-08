"""Unit tests for the reconstructed ``attention.kernel`` layer."""

from __future__ import annotations

from attention.core.attention_target import AttentionTarget
from attention.core.salience_factor import ALL_DIMENSIONS
from attention.kernel.attention_kernel import AttentionKernel, KernelTickResult
from attention.kernel.attention_queue import AttentionQueue
from attention.kernel.salience_engine import KernelSalienceEngine


# --------------------------------------------------------------------------
# KernelSalienceEngine
# --------------------------------------------------------------------------

def test_engine_scores_all_ten_dimensions() -> None:
    engine = KernelSalienceEngine()
    sv = engine.compute(AttentionTarget("telemetry", "x", 0.5))
    assert set(sv.dimensions.keys()) == set(ALL_DIMENSIONS)
    assert len(sv.dimensions) == 10


def test_engine_is_deterministic() -> None:
    engine = KernelSalienceEngine()
    t = AttentionTarget("somatic", "alert", 0.9, metadata={"urgency": 0.95})
    assert engine.compute(t).total == engine.compute(t).total


def test_engine_urgency_metadata_drives_urgency_dimension() -> None:
    engine = KernelSalienceEngine()
    t = AttentionTarget("task", "x", 0.1, metadata={"urgency": 0.9})
    assert engine.score_dimensions(t)["urgency"] == 0.9


def test_engine_higher_raw_gives_higher_total() -> None:
    engine = KernelSalienceEngine()
    low = engine.compute(AttentionTarget("task", "routine", 0.05))
    high = engine.compute(AttentionTarget("somatic", "alert", 0.95))
    assert high.total > low.total


# --------------------------------------------------------------------------
# AttentionQueue
# --------------------------------------------------------------------------

def test_queue_depth_and_full() -> None:
    q = AttentionQueue(max_queue=2)
    assert q.depth == 0
    assert q.push(AttentionTarget("d", "s", 0.5), 0.5) is True
    assert q.push(AttentionTarget("d", "s", 0.5), 0.5) is True
    assert q.depth == 2
    assert q.is_full() is True
    assert q.push(AttentionTarget("d", "s", 0.5), 0.5) is False


def test_queue_pops_highest_score_first() -> None:
    q = AttentionQueue()
    low = AttentionTarget("d", "low", 0.1)
    high = AttentionTarget("d", "high", 0.9)
    q.push(low, 0.1)
    q.push(high, 0.9)
    assert q.pop_highest() is high
    assert q.pop_highest() is low
    assert q.pop_highest() is None


# --------------------------------------------------------------------------
# AttentionKernel
# --------------------------------------------------------------------------

def test_kernel_submit_accepts_and_attaches_salience() -> None:
    kernel = AttentionKernel(max_focus=5, max_queue=20)
    t = AttentionTarget("somatic", "cpu_spike", 0.85, metadata={"urgency": 0.9})
    r = kernel.submit(t)
    assert r["accepted"] is True
    assert t.salience is not None
    assert r["salience"] == round(t.salience.total, 4)


def test_kernel_submit_rejected_when_queue_full() -> None:
    kernel = AttentionKernel(max_focus=1, max_queue=1)
    assert kernel.submit(AttentionTarget("d", "s", 0.5))["accepted"] is True
    assert kernel.submit(AttentionTarget("d", "s", 0.5))["accepted"] is False


def test_kernel_tick_returns_snapshot() -> None:
    kernel = AttentionKernel(max_focus=5, max_queue=20)
    kernel.submit(AttentionTarget("somatic", "alert", 0.85))
    snap = kernel.tick()
    assert isinstance(snap, KernelTickResult)
    assert len(snap.state.focused_targets) >= 0


def test_kernel_high_salience_beats_low() -> None:
    kernel = AttentionKernel(max_focus=5, max_queue=20)
    kernel.submit(AttentionTarget("task", "routine", 0.05))
    kernel.submit(AttentionTarget("somatic", "alert", 0.95, metadata={"urgency": 0.95}))
    snap = kernel.tick()
    assert snap.focused_salience
    assert max(snap.focused_salience.values()) >= 0.3


def test_kernel_focus_respects_max_focus() -> None:
    kernel = AttentionKernel(max_focus=2, max_queue=20)
    for i in range(5):
        kernel.submit(AttentionTarget("task", f"s{i}", 0.5))
    snap = kernel.tick()
    assert len(snap.state.focused_targets) == 2
    assert snap.state.queue_depth == 3
