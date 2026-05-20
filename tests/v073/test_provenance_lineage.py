"""Area 4: Phase 3 provenance and lineage."""

from governance.meaning.concept_trace_record import ConceptTraceRecord
from governance.meaning.meaning_lineage import MeaningLineage
from governance.meaning.semantic_provenance import SemanticProvenance


def test_semantic_provenance_clean() -> None:
    v = SemanticProvenance().validate({"concept_id": "c1", "semantic_claim": True})
    assert v.provenance_valid


def test_semantic_provenance_rewrite_blocked() -> None:
    v = SemanticProvenance().validate({"autonomous_ontology_rewrite": True})
    assert not v.provenance_valid


def test_meaning_lineage_store() -> None:
    trace = ConceptTraceRecord.create(
        concept_id="c1", runtime_id="ambient", label="advisory probe"
    )
    v = MeaningLineage().store(trace, text="labeled parent concept")
    assert v.stored
    assert v.bounded
