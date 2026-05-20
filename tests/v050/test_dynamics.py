"""Area 6: dynamics decay and recovery."""

from attention.core.attention_state import AttentionKernelState
from attention.core.salience import SalienceVector
from attention.dynamics.attention_recovery import AttentionRecovery
from attention.dynamics.focus_fatigue import FocusFatigue
from attention.dynamics.salience_decay import SalienceDecay


def test_decay_reduces_salience() -> None:
    state = AttentionKernelState()
    state.salience_by_target["x"] = SalienceVector("x", {"urgency": 1.0})
    before = state.salience_by_target["x"].total
    SalienceDecay().apply(state)
    assert state.salience_by_target["x"].total < before


def test_recovery_reduces_fatigue() -> None:
    state = AttentionKernelState(fatigue_level=0.5)
    AttentionRecovery().recover(state, idle=True)
    assert state.fatigue_level < 0.5


def test_fatigue_penalty() -> None:
    state = AttentionKernelState()
    FocusFatigue().tick(state, focused_count=10)
    assert state.fatigue_level > 0
