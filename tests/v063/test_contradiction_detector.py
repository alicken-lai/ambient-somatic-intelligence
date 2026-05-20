"""Area 2: contradiction detector."""

from governance.coherence.contradiction_detector import ContradictionDetector
from governance.identity.cognitive_identity import CognitiveIdentity


def test_no_contradiction_stable_batch() -> None:
    identity = CognitiveIdentity()
    detector = ContradictionDetector()
    batch = [
        identity.build_record_from_target(
            source_domain="telemetry",
            signal_type=f"t{i}",
            route_name="r",
            raw_confidence=0.75,
        )
        for i in range(4)
    ]
    assert detector.has_contradiction(batch) is False


def test_high_spread_raises_pressure() -> None:
    identity = CognitiveIdentity()
    detector = ContradictionDetector()
    batch = [
        identity.build_record_from_target(
            source_domain="telemetry",
            signal_type="low",
            route_name="r",
            raw_confidence=0.2,
        ),
        identity.build_record_from_target(
            source_domain="memory",
            signal_type="high",
            route_name="r",
            raw_confidence=0.95,
        ),
    ]
    assert detector.pressure(batch) >= 0.2
