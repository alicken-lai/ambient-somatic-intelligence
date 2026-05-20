"""Area 5: Phase 4 bounded ontology evolution."""

from governance.meaning.bounded_ontology_evolution import BoundedOntologyEvolution
from governance.meaning.interpretive_retention import InterpretiveRetention
from governance.meaning.meaning_record import MeaningRecord
from governance.meaning.semantic_decay_governor import SemanticDecayGovernor


def test_bounded_ontology_store() -> None:
    rec = MeaningRecord.create(
        concept_id="c1",
        runtime_id="ambient",
        summary="Advisory bounded semantics.",
    )
    v = BoundedOntologyEvolution().store(rec)
    assert v.stored
    assert v.bounded


def test_interpretive_retention_bound() -> None:
    v = InterpretiveRetention().evaluate(168.0)
    assert v.retention_ok


def test_semantic_decay_applies() -> None:
    v = SemanticDecayGovernor().apply(0.9, age_hours=168.0)
    assert v.decay_applied
    assert v.decay_factor < 1.0
