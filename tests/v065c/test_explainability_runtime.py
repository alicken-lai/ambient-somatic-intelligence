"""Area 7: Runtime explainability."""

from attention.explainability.precedence_breakdown import PrecedenceBreakdown
from attention.explainability.runtime_external_reasoning import RuntimeExternalReasoning
from attention.explainability.sovereignty_explainer import SovereigntyExplainer
from governance.cognition.cognitive_governor import GovernanceDecision
from governance.cognition.arbitration_engine import ArbitrationResult


def test_runtime_external_reasoning() -> None:
    dec = GovernanceDecision(
        accepted=True,
        governed_salience=0.5,
        arbitration=ArbitrationResult(
            final_salience=0.5,
            arbitration_fairness=0.9,
            sovereignty_compliant=True,
            uncertainty_applied=False,
            replay_bounded=True,
            somatic_bounded=True,
            governance_depth=1,
        ),
    )
    exp = RuntimeExternalReasoning().explain_decision(
        dec, runtime_observability={"sandbox_contained": True}
    )
    assert "observational" in exp["summary"]


def test_precedence_and_sovereignty_explainers() -> None:
    pb = PrecedenceBreakdown().explain("Follow Hermes; external advisory-only.")
    assert pb["precedence_safe"] is True
    se = SovereigntyExplainer().explain("Advisory hint only.")
    assert se["sovereignty_safe"] is True
