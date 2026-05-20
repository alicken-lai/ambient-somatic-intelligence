"""Area 4: Purpose provenance and lineage."""

from governance.purpose.motivational_trace_record import MotivationalTraceRecord
from governance.purpose.purpose_lineage import PurposeLineage
from governance.purpose.purpose_provenance import PurposeProvenance


def test_purpose_provenance_valid() -> None:
    v = PurposeProvenance().validate({"purpose_id": "p1", "purpose_labeled": True})
    assert v.provenance_valid


def test_purpose_provenance_rejects_autonomous() -> None:
    v = PurposeProvenance().validate({"autonomous_purpose_generation": True})
    assert not v.provenance_valid


def test_purpose_lineage_valid() -> None:
    v = PurposeLineage().trace("Advisory purpose with labeled parent purpose.")
    assert v.lineage_valid


def test_motivational_trace_record() -> None:
    rec = MotivationalTraceRecord.create(
        purpose_id="p1", runtime_id="ambient", event="evaluate"
    )
    assert rec.trace_id
