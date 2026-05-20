"""Area 1: metacognitive reflection orchestrator + governor wiring."""

from attention.core.attention_target import AttentionTarget
from governance.cognition.cognitive_governor import CognitiveGovernor
from governance.metacognition.metacognitive_reflection import MetacognitiveReflection


def test_evaluate_after_coherence_clean(
    metacognitive_reflection: MetacognitiveReflection,
) -> None:
    verdict = metacognitive_reflection.evaluate_after_coherence(
        governed_salience=0.6,
        coherence_score=0.85,
        constitutional_compliant=True,
        identity_trusted=True,
        accepted=True,
    )
    assert verdict.reflective is True
    assert verdict.quality_score >= 0.55


def test_governor_attaches_metacognitive_verdict() -> None:
    gov = CognitiveGovernor()
    t = AttentionTarget("telemetry", "meta-wire", 0.55)
    d = gov.govern_target(t, raw_confidence=0.8)
    assert d.metacognitive_verdict is not None
    assert "quality_score" in d.metacognitive_verdict
    assert 0.0 <= d.metacognition_score <= 1.0


def test_governor_metacognition_does_not_override_acceptance() -> None:
    gov = CognitiveGovernor()
    t = AttentionTarget("telemetry", "meta-observe", 0.6)
    d = gov.govern_target(t, raw_confidence=0.85)
    accepted_before = d.accepted
    salience_before = d.governed_salience
    assert d.metacognitive_verdict is not None
    assert d.accepted == accepted_before
    assert d.governed_salience == salience_before
