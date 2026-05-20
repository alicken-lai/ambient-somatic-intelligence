"""Area 5: Phase 4 bounded normative evolution."""

from governance.value.bounded_normative_evolution import BoundedNormativeEvolution
from governance.value.ethical_decay_governor import EthicalDecayGovernor
from governance.value.value_record import ValueRecord
from governance.value.value_retention import ValueRetention


def test_bounded_normative_store() -> None:
    rec = ValueRecord.create(
        value_id="v1",
        runtime_id="ambient",
        summary="Advisory bounded values.",
    )
    v = BoundedNormativeEvolution().store(rec)
    assert v.stored
    assert v.bounded


def test_value_retention_cap() -> None:
    v = ValueRetention().cap(99999.0)
    assert v.retained
    assert v.capped_hours <= 8760 * 2


def test_ethical_decay_applies() -> None:
    v = EthicalDecayGovernor().apply(168.0)
    assert v.decay_applied
    assert v.decay_factor < 1.0
