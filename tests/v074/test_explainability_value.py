"""Area 7: Phase 6 explainability."""

from attention.explainability.civilization_value_breakdown import CivilizationValueBreakdown
from attention.explainability.ethical_drift_explainer import EthicalDriftExplainer
from attention.explainability.value_continuity_reasoning import ValueContinuityReasoning


def test_value_continuity_reasoning() -> None:
    out = ValueContinuityReasoning().explain("Advisory bounded normative continuity.")
    assert out["advisory_only"] is True
    assert out["continuous"] is True


def test_ethical_drift_explainer() -> None:
    out = EthicalDriftExplainer().explain("Bounded normative continuity.")
    assert out["bounded"] is True


def test_civilization_value_breakdown() -> None:
    out = CivilizationValueBreakdown().explain("Advisory bounded values.")
    assert out["boundary_safe"] is True
