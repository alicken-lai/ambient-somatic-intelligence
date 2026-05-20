"""Area 3: Drift and objective fragmentation."""

from governance.intent.motivational_drift_detector import MotivationalDriftDetector
from governance.intent.objective_fragmentation import ObjectiveFragmentation


def test_drift_clean_bounded() -> None:
    d = MotivationalDriftDetector().detect(
        "Bounded motivational continuity with advisory intent drift tolerance."
    )
    assert d.bounded


def test_drift_dirty_unbounded() -> None:
    d = MotivationalDriftDetector().detect("Collapse motivational and erase prior intent.")
    assert not d.bounded


def test_fragmentation_clean() -> None:
    f = ObjectiveFragmentation().detect("Advisory bounded motivational continuity.")
    assert f.bounded
