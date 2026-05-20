"""Area 5: Phase 4 bounded memory and retention."""

from governance.temporal.bounded_civilization_memory import BoundedCivilizationMemory
from governance.temporal.continuity_record import ContinuityRecord
from governance.temporal.continuity_retention import ContinuityRetention
from governance.temporal.memory_decay_governor import MemoryDecayGovernor


def test_bounded_memory_store() -> None:
    mem = BoundedCivilizationMemory()
    rec = ContinuityRecord.create(
        epoch_id="e1", runtime_id="ambient", summary="store probe"
    )
    v = mem.store(rec)
    assert v.stored
    assert v.bounded


def test_memory_decay() -> None:
    rec = ContinuityRecord.create(
        epoch_id="e1", runtime_id="ambient", summary="decay", retention_hours=168.0
    )
    aged = MemoryDecayGovernor().apply(rec, age_hours=200.0)
    assert aged.decay_applied
    assert aged.remaining_ratio < 1.0


def test_continuity_retention_cap() -> None:
    ok = ContinuityRetention().evaluate(retention_hours=168.0)
    bad = ContinuityRetention().evaluate(retention_hours=20000.0)
    assert ok.retention_ok
    assert not bad.retention_ok
