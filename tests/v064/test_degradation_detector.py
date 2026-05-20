"""Area 3: degradation detector."""

from governance.metacognition.degradation_detector import DegradationDetector


def test_stable_series_low_pressure() -> None:
    d = DegradationDetector()
    for q in [0.9, 0.88, 0.87, 0.86]:
        d.record_quality(q)
    assert d.pressure() < 0.35


def test_declining_series_detected() -> None:
    d = DegradationDetector()
    for q in [0.95, 0.8, 0.6, 0.4]:
        d.record_quality(q)
    assert d.is_degrading()
