"""Area 1: cognitive coherence orchestrator + governor wiring."""

from attention.core.attention_target import AttentionTarget
from governance.cognition.cognitive_governor import CognitiveGovernor
from governance.coherence.cognitive_coherence import CognitiveCoherence


def test_evaluate_after_governance_clean(cognitive_coherence: CognitiveCoherence) -> None:
    verdict = cognitive_coherence.evaluate_after_governance(
        governed_salience=0.6,
        constitutional_compliant=True,
        identity_trusted=True,
    )
    assert verdict.coherent is True
    assert verdict.score >= 0.55


def test_governor_attaches_coherence_verdict() -> None:
    gov = CognitiveGovernor()
    t = AttentionTarget("telemetry", "coh-wire", 0.55)
    d = gov.govern_target(t, raw_confidence=0.8)
    assert d.coherence_verdict is not None
    assert "score" in d.coherence_verdict
    assert 0.0 <= d.coherence_score <= 1.0
