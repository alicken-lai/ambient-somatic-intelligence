"""Test 10: provenance corruption detected."""

from governance.identity.cognitive_identity import CognitiveIdentity


def test_corruption_detected() -> None:
    identity = CognitiveIdentity()
    r = identity.build_record_from_target(
        source_domain="telemetry",
        signal_type="x",
        route_name="attention_submit",
        raw_confidence=0.8,
        metadata={"provenance_corrupted": True},
    )
    d = identity.register(r)
    assert d.trusted is False
    assert d.authority_multiplier == 0.0
    assert d.reason == "provenance_corrupted"
