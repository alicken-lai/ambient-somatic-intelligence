"""Test 3: replay cognition distinguishable from runtime."""

from governance.identity.cognition_origin import CognitionOrigin
from governance.identity.provenance_record import ProvenanceRecord


def test_replay_origin_inferred() -> None:
    r = ProvenanceRecord.from_target(
        source_domain="telemetry",
        signal_type="hist",
        route_name="attention_submit",
        raw_confidence=0.7,
        replay_hint=0.7,
        metadata={"replay_derived": True},
    )
    assert r.origin == CognitionOrigin.REPLAY
    assert r.origin != CognitionOrigin.RUNTIME
