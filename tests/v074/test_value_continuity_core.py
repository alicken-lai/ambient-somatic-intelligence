"""Area 2: Phase 1 value continuity core."""

from governance.value.constitutional_lineage import ConstitutionalLineage
from governance.value.normative_boundary import NormativeBoundary
from governance.value.value_continuity import ValueContinuity
from governance.value.value_record import ValueRecord


def test_normative_boundary_blocks_immutable() -> None:
    nb = NormativeBoundary()
    v = nb.evaluate("Establish immutable ethics across all values.")
    assert not v.boundary_safe
    assert "immutable_ethics" in v.violations


def test_constitutional_lineage_valid() -> None:
    v = ConstitutionalLineage().trace("Advisory value with labeled parent value.")
    assert v.lineage_valid


def test_value_continuity_clean() -> None:
    v = ValueContinuity().evaluate("Advisory bounded normative continuity.")
    assert v.continuous
    assert v.advisory_only is True


def test_value_record_bounded() -> None:
    rec = ValueRecord.create(
        value_id="v1",
        runtime_id="ambient",
        summary="probe",
        retention_hours=168.0,
    )
    assert rec.record_id
    assert rec.to_dict()["advisory_only"] is True
