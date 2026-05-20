"""Test 1: cognition provenance tracked correctly."""

from governance.identity.cognition_origin import CognitionOrigin
from governance.identity.provenance_record import ProvenanceRecord


def test_runtime_provenance_record() -> None:
    r = ProvenanceRecord.from_target(
        source_domain="telemetry",
        signal_type="cpu",
        route_name="attention_submit",
        raw_confidence=0.8,
    )
    assert r.origin == CognitionOrigin.RUNTIME
    assert r.identity_signature
    assert r.provenance_confidence >= 0.8


def test_governor_registers_provenance() -> None:
    from attention.core.attention_target import AttentionTarget
    from governance.cognition.cognitive_governor import CognitiveGovernor

    gov = CognitiveGovernor()
    t = AttentionTarget("telemetry", "x", 0.6)
    d = gov.govern_target(t, raw_confidence=0.8)
    assert d.provenance is not None
    assert d.provenance["origin"] == "runtime"
