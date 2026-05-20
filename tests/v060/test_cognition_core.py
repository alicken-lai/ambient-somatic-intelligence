"""Area 1: cognitive governor core."""

from attention.core.attention_target import AttentionTarget
from governance.cognition.cognitive_governor import CognitiveGovernor


def test_govern_target_accepted() -> None:
    gov = CognitiveGovernor()
    t = AttentionTarget("telemetry", "gov-test", 0.55)
    d = gov.govern_target(t, raw_confidence=0.75, uncertainty=0.3)
    assert d.accepted is True
    assert d.governed_salience > 0.0
    assert d.autonomous_blocked is False


def test_recursive_route_blocked() -> None:
    gov = CognitiveGovernor()
    t = AttentionTarget("governance", "loop", 0.8)
    d = gov.govern_target(t, route_name="cognitive_self_loop")
    assert d.accepted is False
    assert d.autonomous_blocked is True
