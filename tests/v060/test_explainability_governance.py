"""Area 6: governance explainability."""

from attention.explainability.arbitration_explainer import ArbitrationExplainer
from attention.explainability.authority_breakdown import AuthorityBreakdown
from attention.explainability.governance_reasoning import GovernanceReasoning
from governance.cognition.cognitive_governor import CognitiveGovernor
from governance.cognition.salience_arbitrator import SalienceArbitrator, SalienceClaim


def test_governance_reasoning() -> None:
    gov = CognitiveGovernor()
    d = gov.govern_salience([SalienceClaim("telemetry", 0.5, 0.8)])
    expl = GovernanceReasoning().explain_decision(d)
    assert expl["advisory_only"] is True
    assert "summary" in expl


def test_arbitration_explainer() -> None:
    arb = SalienceArbitrator().arbitrate([SalienceClaim("telemetry", 0.5, 0.8)])
    expl = ArbitrationExplainer().explain_arbitration(arb)
    assert "disclaimer" in expl


def test_authority_breakdown() -> None:
    b = AuthorityBreakdown().breakdown(base_salience=0.5, domain="somatic", somatic_strength=0.6)
    assert b["no_autonomous_execution"] is True
