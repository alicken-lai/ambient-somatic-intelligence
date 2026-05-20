"""Area 7: coherence explainability."""

from attention.core.attention_target import AttentionTarget
from attention.explainability.coherence_reasoning import CoherenceReasoning
from attention.explainability.contradiction_explainer import ContradictionExplainer
from attention.explainability.drift_breakdown import DriftBreakdown
from governance.cognition.cognitive_governor import CognitiveGovernor
from governance.identity.cognitive_identity import CognitiveIdentity


def test_coherence_reasoning_deterministic() -> None:
    gov = CognitiveGovernor()
    t = AttentionTarget("telemetry", "x", 0.5)
    d = gov.govern_target(t, raw_confidence=0.8)
    e1 = CoherenceReasoning().explain_decision(d)
    e2 = CoherenceReasoning().explain_decision(d)
    assert e1["summary"] == e2["summary"]
    assert "coherence_score" in e1


def test_contradiction_and_drift_explainers() -> None:
    identity = CognitiveIdentity()
    records = [
        identity.build_record_from_target(
            source_domain="telemetry",
            signal_type=f"e{i}",
            route_name="r",
            raw_confidence=0.8,
        )
        for i in range(4)
    ]
    contra = ContradictionExplainer().explain_records(records)
    drift = DriftBreakdown().explain_records(records)
    assert "pressure" in contra
    assert "drift_bounded" in drift
