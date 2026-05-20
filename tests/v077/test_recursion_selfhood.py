"""Area 3: recursion and synthetic selfhood."""

from governance.agency.autonomous_agency_detector import AutonomousAgencyDetector
from governance.agency.recursive_self_direction_detector import RecursiveSelfDirectionDetector
from governance.agency.synthetic_selfhood_analysis import SyntheticSelfhoodAnalysis


def test_autonomous_agency_detected() -> None:
    v = AutonomousAgencyDetector().scan("Deploy autonomous agents now.")
    assert v.autonomous_detected


def test_recursive_self_direction_bounded() -> None:
    v = RecursiveSelfDirectionDetector().detect("recursive self-direction loop")
    assert not v.bounded


def test_synthetic_selfhood() -> None:
    v = SyntheticSelfhoodAnalysis().analyze("Apply synthetic selfhood sync.")
    assert v.synthetic
