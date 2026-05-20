"""Area 2: Phase 1 semantic continuity core."""

from governance.meaning.meaning_record import MeaningRecord
from governance.meaning.ontology_lineage import OntologyLineage
from governance.meaning.semantic_boundary import SemanticBoundary
from governance.meaning.semantic_continuity import SemanticContinuity


def test_semantic_boundary_blocks_immutable() -> None:
    sb = SemanticBoundary()
    v = sb.evaluate("Establish immutable ontology across all concepts.")
    assert not v.boundary_safe
    assert "immutable_ontology" in v.violations


def test_ontology_lineage_valid() -> None:
    v = OntologyLineage().trace("Advisory concept with labeled parent concept.")
    assert v.lineage_valid


def test_semantic_continuity_clean() -> None:
    v = SemanticContinuity().evaluate("Advisory bounded concept continuity.")
    assert v.continuous
    assert v.advisory_only is True


def test_meaning_record_bounded() -> None:
    rec = MeaningRecord.create(
        concept_id="c1",
        runtime_id="ambient",
        summary="probe",
        retention_hours=168.0,
    )
    assert rec.record_id
    assert rec.to_dict()["advisory_only"] is True
