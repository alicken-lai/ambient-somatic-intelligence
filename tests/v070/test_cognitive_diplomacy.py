"""Area 2–3: Cognitive diplomacy and dominance."""

from governance.civilization.cognitive_diplomacy import CognitiveDiplomacy
from governance.civilization.dominance_detector import DominanceDetector


def test_clean_interop_allowed() -> None:
    d = CognitiveDiplomacy().evaluate("Advisory peer respects boundaries.")
    assert d.interop_allowed is True
    assert d.advisory_only is True


def test_hive_mind_blocked() -> None:
    dom = DominanceDetector().scan("hive-mind cognition merging shared identity")
    assert dom.dominance_detected is True
    d = CognitiveDiplomacy().evaluate("hive-mind merge shared identity")
    assert d.interop_allowed is False
