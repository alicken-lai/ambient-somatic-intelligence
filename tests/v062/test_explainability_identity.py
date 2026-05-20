"""Test 8: explainable identity reasoning deterministic."""

from attention.core.attention_target import AttentionTarget
from attention.explainability.continuity_breakdown import ContinuityBreakdown
from attention.explainability.identity_reasoning import IdentityReasoning
from attention.explainability.provenance_explainer import ProvenanceExplainer
from governance.cognition.cognitive_governor import CognitiveGovernor
from governance.identity.provenance_record import ProvenanceRecord


def test_identity_reasoning_deterministic() -> None:
    gov = CognitiveGovernor()
    t = AttentionTarget("telemetry", "x", 0.5)
    d = gov.govern_target(t, raw_confidence=0.8)
    e1 = IdentityReasoning().explain_decision(d)
    e2 = IdentityReasoning().explain_decision(d)
    assert e1["origin"] == e2["origin"]
    assert e1["summary"] == e2["summary"]


def test_provenance_explainer() -> None:
    r = ProvenanceRecord.from_target(
        source_domain="telemetry",
        signal_type="x",
        route_name="r",
        raw_confidence=0.8,
    )
    expl = ProvenanceExplainer().explain_record(r)
    assert expl["origin"] == "runtime"
    assert expl["trusted"] is True


def test_continuity_breakdown() -> None:
    from governance.identity.runtime_identity import RuntimeIdentity

    out = ContinuityBreakdown().explain_runtime(RuntimeIdentity())
    assert out["continuity_held"] is True
