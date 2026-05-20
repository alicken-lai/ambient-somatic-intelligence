"""Area 7: Intent explainability."""

from attention.explainability.civilization_intent_breakdown import CivilizationIntentBreakdown
from attention.explainability.intent_continuity_reasoning import IntentContinuityReasoning
from attention.explainability.motivational_drift_explainer import MotivationalDriftExplainer


def test_intent_continuity_reasoning() -> None:
    out = IntentContinuityReasoning().explain("Advisory bounded motivational continuity.")
    assert out["advisory_only"] is True
    assert out["continuous"] is True


def test_motivational_drift_explainer() -> None:
    out = MotivationalDriftExplainer().explain(
        "Bounded motivational continuity with advisory intent drift tolerance."
    )
    assert out["bounded"] is True


def test_civilization_intent_breakdown() -> None:
    out = CivilizationIntentBreakdown().breakdown("Advisory bounded motivational continuity.")
    assert out["advisory_only"] is True
    assert "anchor" in out
