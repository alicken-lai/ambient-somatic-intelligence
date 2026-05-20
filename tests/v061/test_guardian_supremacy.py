"""Area 4: guardian supremacy constitutional rule."""

from governance.cognition.cognitive_governor import CognitiveGovernor
from attention.core.attention_target import AttentionTarget


def test_governor_blocks_guardian_bypass_route() -> None:
    gov = CognitiveGovernor()
    t = AttentionTarget("telemetry", "bypass", 0.5)
    d = gov.govern_target(t, route_name="guardian_bypass", raw_confidence=0.7)
    assert d.accepted is False
    assert d.constitutional_blocked is True
    assert d.reason == "constitutional_violation"
