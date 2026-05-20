"""Area 6: Civilization explainability."""

from attention.explainability.cognitive_diplomacy_reasoning import CognitiveDiplomacyReasoning
from attention.explainability.sovereignty_breakdown import SovereigntyBreakdown
from attention.explainability.treaty_explainer import TreatyExplainer


def test_diplomacy_reasoning() -> None:
    out = CognitiveDiplomacyReasoning().explain("Advisory peer note.")
    assert out["advisory_only"] is True
    assert "interop_allowed" in out


def test_treaty_and_sovereignty_explainers() -> None:
    t = TreatyExplainer().explain("foreign", "ambient", text="Advisory treaty scope.")
    s = SovereigntyBreakdown().explain("Respect Ambient sovereignty.")
    assert t.get("advisory_only") is True
    assert "combined_safe" in s
