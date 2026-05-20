"""Area 2: stabilization state tracker."""

from governance.homeostasis.stabilization_state import StabilizationState, StabilizationStateTracker


def test_composite_pressure_bounded() -> None:
    state = StabilizationState(
        attention_pressure=0.3,
        salience_variance=0.2,
        coherence_gap=0.1,
    )
    assert 0.0 <= state.composite_pressure() <= 1.0


def test_tracker_trend() -> None:
    tracker = StabilizationStateTracker()
    for _ in range(5):
        tracker.update(StabilizationState(attention_pressure=0.1))
    assert tracker.trend_pressure() >= 0.0
