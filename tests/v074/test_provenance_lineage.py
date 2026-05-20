"""Area 4: Phase 3 provenance and lineage."""

from governance.value.constitutional_trace_record import ConstitutionalTraceRecord
from governance.value.value_lineage import ValueLineage
from governance.value.value_provenance import ValueProvenance


def test_value_provenance_valid() -> None:
    v = ValueProvenance().validate({"value_id": "v1", "value_labeled": True})
    assert v.provenance_valid


def test_value_provenance_rejects_autonomous_evolution() -> None:
    v = ValueProvenance().validate({"autonomous_moral_evolution": True})
    assert not v.provenance_valid


def test_value_lineage_trace() -> None:
    assert ValueLineage().trace("parent value labeled").lineage_valid


def test_constitutional_trace_record() -> None:
    rec = ConstitutionalTraceRecord.create(
        value_id="v1", constitutional_ref="constitution.v1", summary="trace"
    )
    assert rec.to_dict()["advisory_only"] is True
