"""Area 2: false positive tracker."""

from attention.calibration.false_positive_tracker import FalsePositiveTracker
from attention.calibration.confidence_cap import ABSOLUTE_MAX_CONFIDENCE


def test_fp_detection() -> None:
    t = FalsePositiveTracker()
    assert t.is_false_positive(0.8, 0.1) is True
    assert t.is_false_positive(0.5, 0.5) is False


def test_fp_adjusted_confidence_capped() -> None:
    t = FalsePositiveTracker()
    for _ in range(5):
        t.record("telemetry", "pat-a", 0.9, 0.1)
    adj = t.adjusted_confidence(0.95, "telemetry")
    assert adj <= ABSOLUTE_MAX_CONFIDENCE
