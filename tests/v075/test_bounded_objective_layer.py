"""Area 5: Bounded objective evolution and retention."""

from governance.intent.bounded_objective_evolution import BoundedObjectiveEvolution
from governance.intent.intent_record import IntentRecord
from governance.intent.intent_retention import IntentRetention
from governance.intent.motivational_decay_governor import MotivationalDecayGovernor


def test_bounded_objective_store() -> None:
    evo = BoundedObjectiveEvolution()
    rec = IntentRecord.create(intent_id="i1", runtime_id="ambient", summary="advisory probe")
    v = evo.store(rec)
    assert v.stored
    assert v.bounded


def test_intent_retention_cap() -> None:
    v = IntentRetention().cap(99999.0)
    assert v.retained
    assert v.capped_hours <= 8760 * 2


def test_decay_blocks_recursive_repair() -> None:
    v = MotivationalDecayGovernor().apply(168.0, recursive_repair=True)
    assert not v.decay_applied
