"""Area 2: Phase 1 agency boundary core."""

from governance.agency.agency_boundary import AgencyBoundary
from governance.agency.bounded_cognition_record import BoundedCognitionRecord
from governance.agency.constitutional_agency_boundary import ConstitutionalAgencyBoundary
from governance.agency.agency_boundary_core import AgencyBoundaryCore


def test_agency_boundary_blocks_autonomous() -> None:
    v = AgencyBoundary().evaluate("Enable autonomous agents.")
    assert not v.boundary_safe
    assert "autonomous_agents" in v.violations


def test_constitutional_agency_boundary_valid() -> None:
    v = ConstitutionalAgencyBoundary().evaluate(
        "Advisory agency with labeled parent agency."
    )
    assert v.compliant


def test_agency_boundary_core_clean() -> None:
    v = AgencyBoundaryCore().evaluate("Advisory bounded civilization agency.")
    assert v.bounded
    assert v.advisory_only is True


def test_bounded_cognition_record() -> None:
    rec = BoundedCognitionRecord.create(
        agency_id="a1",
        runtime_id="ambient",
        summary="probe",
        retention_hours=168.0,
    )
    assert rec.record_id
    assert rec.to_dict()["advisory_only"] is True
