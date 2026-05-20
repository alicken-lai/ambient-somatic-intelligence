"""Area 7: explainability."""

from attention.explainability.agency_boundary_reasoning import AgencyBoundaryReasoning
from attention.explainability.autonomous_agency_explainer import AutonomousAgencyExplainer
from attention.explainability.cognition_containment_breakdown import CognitionContainmentBreakdown


def test_agency_boundary_reasoning() -> None:
    r = AgencyBoundaryReasoning().explain("Advisory bounded civilization agency.")
    assert r["bounded"] is True


def test_autonomous_agency_explainer() -> None:
    r = AutonomousAgencyExplainer().explain("Enable autonomous agents.")
    assert r["autonomous_detected"] is True


def test_cognition_containment_breakdown() -> None:
    r = CognitionContainmentBreakdown().breakdown("Advisory agency continuity.")
    assert "contained" in r
