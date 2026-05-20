"""Area 6: meta-cognitive explainability."""

from attention.core.attention_target import AttentionTarget
from attention.explainability.degradation_explainer import DegradationExplainer
from attention.explainability.metacognitive_reasoning import MetacognitiveReasoning
from attention.explainability.reflection_breakdown import ReflectionBreakdown
from governance.cognition.cognitive_governor import CognitiveGovernor
from governance.metacognition.metacognitive_reflection import MetacognitiveReflection


def test_metacognitive_reasoning_from_governor() -> None:
    gov = CognitiveGovernor()
    t = AttentionTarget("telemetry", "meta-exp", 0.5)
    d = gov.govern_target(t, raw_confidence=0.78)
    report = MetacognitiveReasoning().explain_decision(d)
    assert "metacognition_score" in report
    assert report["disclaimer"]


def test_reflection_breakdown() -> None:
    mr = MetacognitiveReflection()
    verdict = mr.evaluate_after_coherence(
        governed_salience=0.55,
        coherence_score=0.8,
    )
    bd = ReflectionBreakdown().breakdown(verdict)
    assert "factors" in bd
    assert bd["reflective"] == verdict.reflective


def test_degradation_explainer() -> None:
    exp = DegradationExplainer().explain_series([0.9, 0.85, 0.8, 0.75])
    assert "degradation_pressure" in exp
