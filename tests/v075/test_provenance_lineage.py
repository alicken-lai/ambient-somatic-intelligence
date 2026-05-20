"""Area 4: Provenance and intent lineage."""

from governance.intent.intent_lineage import IntentLineage
from governance.intent.intent_provenance import IntentProvenance


def test_provenance_valid_labeled() -> None:
    v = IntentProvenance().validate({"intent_id": "i1"})
    assert v.provenance_valid


def test_provenance_rejects_autonomous_evolution() -> None:
    v = IntentProvenance().validate({"autonomous_motivational_evolution": True})
    assert not v.provenance_valid


def test_intent_lineage_trace() -> None:
    v = IntentLineage().trace("Advisory intent with labeled parent intent.")
    assert v.lineage_valid
