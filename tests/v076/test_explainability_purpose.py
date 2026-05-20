"""Area 7: Purpose explainability."""

from attention.explainability.autonomous_purpose_explainer import AutonomousPurposeExplainer
from attention.explainability.motivational_containment_breakdown import (
    MotivationalContainmentBreakdown,
)
from attention.explainability.purpose_boundary_reasoning import PurposeBoundaryReasoning


def test_purpose_boundary_reasoning() -> None:
    out = PurposeBoundaryReasoning().explain("Advisory bounded civilization purpose.")
    assert out["advisory_only"] is True
    assert out["bounded"] is True


def test_autonomous_purpose_explainer() -> None:
    out = AutonomousPurposeExplainer().explain("Enable autonomous purpose generation.")
    assert out["autonomous_detected"] is True


def test_motivational_containment_breakdown() -> None:
    out = MotivationalContainmentBreakdown().breakdown(
        "Bounded civilization purpose with advisory teleology tolerance."
    )
    assert out["advisory_only"] is True
