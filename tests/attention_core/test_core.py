"""Unit tests for the reconstructed ``attention.core`` layer.

These tests pin the contract that higher attention layers and the v05x-v07x
consumers rely on: the 10-dimension salience model, the weighted salience
computation, and the four foundational value/state objects.
"""

from __future__ import annotations

import math

from attention.core.attention_state import AttentionKernelState
from attention.core.attention_target import AttentionTarget
from attention.core.precursor_signal import PrecursorSignal
from attention.core.salience import SalienceVector, compute_weighted_salience
from attention.core.salience_factor import (
    ALL_DIMENSIONS,
    DEFAULT_DIMENSION_WEIGHTS,
)


# --------------------------------------------------------------------------
# salience_factor
# --------------------------------------------------------------------------

def test_ten_dimensions_present() -> None:
    assert len(ALL_DIMENSIONS) == 10
    assert len(set(ALL_DIMENSIONS)) == 10


def test_default_weights_normalised() -> None:
    assert abs(sum(DEFAULT_DIMENSION_WEIGHTS.values()) - 1.0) < 1e-9
    # Every dimension carries a strictly positive weight.
    assert all(DEFAULT_DIMENSION_WEIGHTS[d] > 0.0 for d in ALL_DIMENSIONS)


def test_urgency_is_a_weighted_dimension() -> None:
    # Downstream decay tests rely on "urgency" contributing to the total.
    assert "urgency" in ALL_DIMENSIONS
    assert DEFAULT_DIMENSION_WEIGHTS["urgency"] > 0.0


# --------------------------------------------------------------------------
# compute_weighted_salience
# --------------------------------------------------------------------------

def test_full_saturation_reaches_one() -> None:
    dims = {d: 1.0 for d in ALL_DIMENSIONS}
    assert compute_weighted_salience(dims) >= 0.99


def test_weighted_salience_clamped_to_unit() -> None:
    dims = {d: 5.0 for d in ALL_DIMENSIONS}
    result = compute_weighted_salience(dims)
    assert result <= 1.0
    assert result >= 0.99
    neg = {d: -3.0 for d in ALL_DIMENSIONS}
    assert compute_weighted_salience(neg) == 0.0


def test_partial_dimensions_use_their_weight_only() -> None:
    result = compute_weighted_salience({"urgency": 1.0})
    assert math.isclose(result, DEFAULT_DIMENSION_WEIGHTS["urgency"])


def test_unknown_dimension_contributes_nothing() -> None:
    assert compute_weighted_salience({"not_a_dimension": 1.0}) == 0.0


# --------------------------------------------------------------------------
# SalienceVector
# --------------------------------------------------------------------------

def test_vector_total_matches_compute() -> None:
    v = SalienceVector("t1", {d: 0.5 for d in ALL_DIMENSIONS})
    assert v.total == compute_weighted_salience(v.dimensions, v.weights)


def test_vector_total_recomputes_after_mutation() -> None:
    v = SalienceVector("x", {"urgency": 1.0})
    before = v.total
    v.scale(0.5)
    assert v.total < before
    assert math.isclose(v.total, before * 0.5)


def test_vector_roundtrip() -> None:
    v = SalienceVector("t2", {"urgency": 0.4, "novelty": 0.6})
    restored = SalienceVector.from_dict(v.to_dict())
    assert restored.target_id == "t2"
    assert math.isclose(restored.total, v.total)


# --------------------------------------------------------------------------
# AttentionTarget
# --------------------------------------------------------------------------

def test_target_positional_construction() -> None:
    t = AttentionTarget("telemetry", "gov-test", 0.55)
    assert t.source_domain == "telemetry"
    assert t.signal_type == "gov-test"
    assert t.raw_value == 0.55
    assert t.metadata == {}


def test_target_raw_value_clamped() -> None:
    assert AttentionTarget("d", "s", 5.0).raw_value == 1.0
    assert AttentionTarget("d", "s", -1.0).raw_value == 0.0


def test_target_ids_are_unique() -> None:
    a = AttentionTarget("d", "s", 0.5)
    b = AttentionTarget("d", "s", 0.5)
    assert a.target_id != b.target_id


def test_target_roundtrip_with_salience() -> None:
    t = AttentionTarget(
        "memory", "recall", 0.6, metadata={"tags": ["a"]},
    )
    t.salience = SalienceVector(t.target_id, {"urgency": 0.5})
    restored = AttentionTarget.from_dict(t.to_dict())
    assert restored.target_id == t.target_id
    assert restored.metadata == {"tags": ["a"]}
    assert restored.salience is not None
    assert math.isclose(restored.salience.total, t.salience.total)


# --------------------------------------------------------------------------
# PrecursorSignal
# --------------------------------------------------------------------------

def test_precursor_defaults() -> None:
    p = PrecursorSignal(pattern_id="pat", strength=0.6)
    assert p.domain == "unknown"
    assert p.metadata == {}
    assert p.strength == 0.6


def test_precursor_strength_clamped() -> None:
    assert PrecursorSignal("p", 9.0).strength == 1.0
    assert PrecursorSignal("p", -1.0).strength == 0.0


def test_precursor_roundtrip() -> None:
    p = PrecursorSignal(
        pattern_id="pat-1", strength=0.6, domain="somatic",
        metadata={"tags": ["alert"]},
    )
    restored = PrecursorSignal.from_dict(p.to_dict())
    assert restored.pattern_id == "pat-1"
    assert restored.domain == "somatic"
    assert restored.metadata == {"tags": ["alert"]}
    assert restored.strength == 0.6


# --------------------------------------------------------------------------
# AttentionKernelState
# --------------------------------------------------------------------------

def test_kernel_state_defaults() -> None:
    state = AttentionKernelState()
    assert state.salience_by_target == {}
    assert state.focused_targets == []
    assert state.queue_depth == 0
    assert state.budget_remaining == 1.0
    assert state.fatigue_level == 0.0


def test_kernel_state_accepts_kwargs() -> None:
    state = AttentionKernelState(fatigue_level=0.5)
    assert state.fatigue_level == 0.5


def test_kernel_state_top_salience_and_focused_count() -> None:
    state = AttentionKernelState()
    assert state.top_salience == 0.0
    state.salience_by_target["a"] = SalienceVector("a", {"urgency": 0.8})
    state.salience_by_target["b"] = SalienceVector("b", {"urgency": 0.2})
    assert state.top_salience == state.salience_by_target["a"].total
    state.focused_targets.append("a")
    assert state.focused_count == 1


def test_kernel_state_clamps_levels() -> None:
    state = AttentionKernelState(fatigue_level=5.0, budget_remaining=-1.0)
    assert state.fatigue_level == 1.0
    assert state.budget_remaining == 0.0
