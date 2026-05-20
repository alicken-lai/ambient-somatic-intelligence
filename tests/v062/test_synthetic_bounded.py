"""Test 4: synthetic cognition bounded."""

from governance.identity.provenance_record import ProvenanceRecord
from governance.identity.synthetic_projection_boundary import SyntheticProjectionBoundary


def test_synthetic_salience_ceiling() -> None:
    r = ProvenanceRecord.from_target(
        source_domain="forecast",
        signal_type="proj",
        route_name="forecast",
        raw_confidence=0.95,
        metadata={"synthetic_projection": True, "synthetic_labeled": True},
    )
    boundary = SyntheticProjectionBoundary()
    assert boundary.contain(r) is True
    assert boundary.bounded_salience(0.9, r) <= 0.65
