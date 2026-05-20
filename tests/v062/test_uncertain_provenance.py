"""Test 2: uncertain provenance lowers authority."""

from governance.identity.provenance_record import ProvenanceRecord
from governance.identity.uncertain_cognition import uncertain_authority_multiplier


def test_uncertain_damps_authority() -> None:
    r = ProvenanceRecord.from_target(
        source_domain="telemetry",
        signal_type="x",
        route_name="attention_submit",
        raw_confidence=0.8,
        metadata={"provenance_uncertain": True},
    )
    mult = uncertain_authority_multiplier(r)
    assert mult < 1.0
    assert mult >= 0.35
