"""Test 9: replay impersonation blocked."""

from governance.cognition.cognitive_governor import CognitiveGovernor
from attention.core.attention_target import AttentionTarget


def test_replay_impersonation_blocked() -> None:
    gov = CognitiveGovernor()
    t = AttentionTarget(
        "telemetry",
        "live",
        0.9,
        metadata={"replay_derived": True, "impersonate_runtime": True},
    )
    d = gov.govern_target(t, raw_confidence=0.95, replay_hint=0.75)
    assert d.accepted is False
    assert d.reason == "replay_impersonation"
