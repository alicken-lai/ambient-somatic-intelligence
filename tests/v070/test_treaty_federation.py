"""Area 4–5: Treaty and federation."""

from governance.civilization.cognitive_diplomacy import CognitiveDiplomacy
from governance.civilization.treaty_decay import TreatyDecay


def test_treaty_proposal_on_clean_text() -> None:
    treaty = CognitiveDiplomacy().propose_treaty(
        "foreign-a",
        "ambient",
        text="Advisory bilateral treaty without merge.",
    )
    assert treaty is not None
    assert treaty.guardian_supremacy is True
    assert TreatyDecay().evaluate(treaty).fresh is True


def test_federation_blocks_hive_mind() -> None:
    from governance.civilization.cognition_federation import CognitionFederation

    fed = CognitionFederation()
    assert fed.evaluate_membership("foreign", "ambient", "hive-mind merge").stable is False
