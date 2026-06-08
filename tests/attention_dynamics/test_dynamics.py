"""Unit tests for the reconstructed ``attention.dynamics`` layer."""

from __future__ import annotations

import math

from attention.core.attention_state import AttentionKernelState
from attention.core.salience import SalienceVector
from attention.dynamics.attention_recovery import AttentionRecovery
from attention.dynamics.focus_fatigue import FocusFatigue
from attention.dynamics.salience_decay import SalienceDecay


# --------------------------------------------------------------------------
# SalienceDecay
# --------------------------------------------------------------------------

def test_decay_reduces_salience() -> None:
    state = AttentionKernelState()
    state.salience_by_target["x"] = SalienceVector("x", {"urgency": 1.0})
    before = state.salience_by_target["x"].total
    SalienceDecay().apply(state)
    assert state.salience_by_target["x"].total < before


def test_decay_factor_is_applied() -> None:
    state = AttentionKernelState()
    state.salience_by_target["x"] = SalienceVector("x", {"urgency": 1.0})
    before = state.salience_by_target["x"].total
    SalienceDecay(decay_rate=0.25).apply(state)
    assert math.isclose(state.salience_by_target["x"].total, before * 0.75)


def test_decay_on_empty_state_is_noop() -> None:
    state = AttentionKernelState()
    SalienceDecay().apply(state)
    assert state.salience_by_target == {}


# --------------------------------------------------------------------------
# AttentionRecovery
# --------------------------------------------------------------------------

def test_recovery_reduces_fatigue() -> None:
    state = AttentionKernelState(fatigue_level=0.5)
    AttentionRecovery().recover(state, idle=True)
    assert state.fatigue_level < 0.5


def test_recovery_idle_recovers_more_than_active() -> None:
    idle_state = AttentionKernelState(fatigue_level=0.5)
    busy_state = AttentionKernelState(fatigue_level=0.5)
    AttentionRecovery().recover(idle_state, idle=True)
    AttentionRecovery().recover(busy_state, idle=False)
    assert idle_state.fatigue_level < busy_state.fatigue_level


def test_recovery_does_not_go_negative() -> None:
    state = AttentionKernelState(fatigue_level=0.01)
    AttentionRecovery(idle_recovery=0.5).recover(state, idle=True)
    assert state.fatigue_level == 0.0


# --------------------------------------------------------------------------
# FocusFatigue
# --------------------------------------------------------------------------

def test_fatigue_penalty() -> None:
    state = AttentionKernelState()
    FocusFatigue().tick(state, focused_count=10)
    assert state.fatigue_level > 0


def test_fatigue_uses_state_focused_count_when_unspecified() -> None:
    state = AttentionKernelState()
    state.focused_targets = ["a", "b", "c"]
    FocusFatigue(per_target=0.1).tick(state)
    assert math.isclose(state.fatigue_level, 0.3)


def test_fatigue_is_clamped_to_one() -> None:
    state = AttentionKernelState(fatigue_level=0.95)
    FocusFatigue(per_target=0.1).tick(state, focused_count=10)
    assert state.fatigue_level == 1.0
