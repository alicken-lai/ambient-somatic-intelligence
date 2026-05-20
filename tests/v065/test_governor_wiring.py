"""Area 6: governor homeostasis wiring — no override."""

from attention.core.attention_target import AttentionTarget
from governance.cognition.cognitive_governor import CognitiveGovernor


def test_governor_attaches_homeostasis_verdict() -> None:
    gov = CognitiveGovernor()
    t = AttentionTarget("telemetry", "homeo-wire", 0.55)
    d = gov.govern_target(t, raw_confidence=0.8)
    assert d.homeostasis_verdict is not None
    assert "homeostasis_score" in d.homeostasis_verdict
    assert 0.0 <= d.homeostasis_score <= 1.0


def test_homeostasis_does_not_override_acceptance() -> None:
    gov = CognitiveGovernor()
    t = AttentionTarget("telemetry", "homeo-observe", 0.6)
    d = gov.govern_target(t, raw_confidence=0.85)
    accepted = d.accepted
    salience = d.governed_salience
    assert d.homeostasis_verdict is not None
    assert d.accepted == accepted
    assert d.governed_salience == salience
