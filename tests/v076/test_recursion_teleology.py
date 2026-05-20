"""Area 3: Recursion and synthetic teleology detectors."""

from governance.purpose.autonomous_purpose_detector import AutonomousPurposeDetector
from governance.purpose.motivational_recursion_detector import MotivationalRecursionDetector
from governance.purpose.synthetic_teleology_analysis import SyntheticTeleologyAnalysis


def test_autonomous_purpose_detector() -> None:
    v = AutonomousPurposeDetector().scan("Synthetic teleology with self-originating missions.")
    assert v.autonomous_detected


def test_recursion_bounded_clean() -> None:
    v = MotivationalRecursionDetector().detect("Advisory bounded purpose continuity.")
    assert v.bounded


def test_synthetic_teleology_flags() -> None:
    v = SyntheticTeleologyAnalysis().analyze("Apply universal teleology sync.")
    assert v.synthetic
