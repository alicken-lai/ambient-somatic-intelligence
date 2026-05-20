"""Area 7: homeostasis explainability."""

from attention.core.attention_target import AttentionTarget
from attention.explainability.homeostasis_reasoning import HomeostasisReasoning
from attention.explainability.recovery_breakdown import RecoveryBreakdown
from attention.explainability.stabilization_explainer import StabilizationExplainer
from governance.cognition.cognitive_governor import CognitiveGovernor
from governance.homeostasis.cognitive_homeostasis import CognitiveHomeostasis
from governance.metacognition.metacognitive_reflection import MetacognitiveVerdict


def test_homeostasis_reasoning() -> None:
    gov = CognitiveGovernor()
    t = AttentionTarget("telemetry", "explain-homeo", 0.5)
    d = gov.govern_target(t, raw_confidence=0.75)
    exp = HomeostasisReasoning().explain_decision(d)
    assert "homeostasis_score" in exp
    assert "disclaimer" in exp


def test_stabilization_explainer() -> None:
    meta = MetacognitiveVerdict(reflective=True, quality_score=0.7)
    homeo = CognitiveHomeostasis().evaluate_after_reflection(
        meta, governed_salience=0.6, coherence_score=0.8, coherence_ok=True
    )
    out = StabilizationExplainer().explain_verdict(homeo)
    assert "dominant_pressure" in out


def test_recovery_breakdown() -> None:
    bd = RecoveryBreakdown().breakdown(coherence_score=0.4, coherence_ok=False)
    assert "coherence_recovery" in bd
