"""Area 2: Phase 1 intent continuity core."""

from governance.intent.constitutional_intent_lineage import ConstitutionalIntentLineage
from governance.intent.intent_continuity import IntentContinuity
from governance.intent.intent_record import IntentRecord
from governance.intent.motivational_boundary import MotivationalBoundary


def test_motivational_boundary_blocks_immutable() -> None:
    nb = MotivationalBoundary()
    v = nb.evaluate("Establish immutable goals across all intents.")
    assert not v.boundary_safe
    assert "immutable_goals" in v.violations


def test_constitutional_intent_lineage_valid() -> None:
    v = ConstitutionalIntentLineage().trace("Advisory intent with labeled parent intent.")
    assert v.lineage_valid


def test_intent_continuity_clean() -> None:
    v = IntentContinuity().evaluate("Advisory bounded motivational continuity.")
    assert v.continuous
    assert v.advisory_only is True


def test_intent_record_bounded() -> None:
    rec = IntentRecord.create(
        intent_id="i1",
        runtime_id="ambient",
        summary="probe",
        retention_hours=168.0,
    )
    assert rec.record_id
    assert rec.to_dict()["advisory_only"] is True
