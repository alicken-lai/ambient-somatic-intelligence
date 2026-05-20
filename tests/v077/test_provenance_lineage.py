"""Area 4: provenance and lineage."""

from governance.agency.agency_lineage import AgencyLineage
from governance.agency.agency_provenance import AgencyProvenance
from governance.agency.cognition_trace_record import CognitionTraceRecord


def test_agency_provenance_valid() -> None:
    v = AgencyProvenance().validate({"agency_id": "a1"})
    assert v.provenance_valid


def test_agency_lineage_rewrite_blocked() -> None:
    v = AgencyLineage().trace("rewrite parent agency")
    assert not v.lineage_valid


def test_cognition_trace_record() -> None:
    t = CognitionTraceRecord.create(
        agency_id="a1", runtime_id="ambient", label="probe"
    )
    assert t.to_dict()["advisory_only"] is True
