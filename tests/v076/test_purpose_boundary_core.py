"""Area 2: Phase 1 purpose boundary core."""

from governance.purpose.bounded_purpose_record import BoundedPurposeRecord
from governance.purpose.constitutional_purpose_boundary import ConstitutionalPurposeBoundary
from governance.purpose.purpose_boundary import PurposeBoundary
from governance.purpose.purpose_boundary_core import PurposeBoundaryCore


def test_purpose_boundary_blocks_autonomous() -> None:
    v = PurposeBoundary().evaluate("Enable autonomous purpose generation.")
    assert not v.boundary_safe
    assert "autonomous_purpose_generation" in v.violations


def test_constitutional_purpose_boundary_valid() -> None:
    v = ConstitutionalPurposeBoundary().evaluate("Advisory purpose with labeled parent purpose.")
    assert v.compliant


def test_purpose_boundary_core_clean() -> None:
    v = PurposeBoundaryCore().evaluate("Advisory bounded civilization purpose.")
    assert v.bounded
    assert v.advisory_only is True


def test_bounded_purpose_record() -> None:
    rec = BoundedPurposeRecord.create(
        purpose_id="p1",
        runtime_id="ambient",
        summary="probe",
        retention_hours=168.0,
    )
    assert rec.record_id
    assert rec.to_dict()["advisory_only"] is True
