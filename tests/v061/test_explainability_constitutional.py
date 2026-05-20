"""Area 6: constitutional explainability."""

from attention.explainability.constitutional_reasoning import ConstitutionalReasoning
from attention.explainability.governance_boundary_explainer import GovernanceBoundaryExplainer
from governance.cognition.cognitive_governor import CognitiveGovernor
from attention.core.attention_target import AttentionTarget


def test_constitutional_reasoning_block() -> None:
    gov = CognitiveGovernor()
    t = AttentionTarget("telemetry", "x", 0.5)
    d = gov.govern_target(t, route_name="skip_guardian_check")
    expl = ConstitutionalReasoning().explain_decision(d)
    assert expl["constitutional_blocked"] is True


def test_governance_boundary_layers() -> None:
    layers = GovernanceBoundaryExplainer().explain_layers()
    assert layers["constitutional_rule_count"] >= 5
    assert layers["layers"][0]["name"] == "constitutional_guard"
