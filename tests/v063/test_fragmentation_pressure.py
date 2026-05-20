"""Area 6: fragmentation pressure."""

from governance.coherence.fragmentation_pressure import FragmentationPressure
from governance.identity.cognitive_identity import CognitiveIdentity


def test_normal_batch_low_pressure() -> None:
    identity = CognitiveIdentity()
    frag = FragmentationPressure()
    records = [
        identity.build_record_from_target(
            source_domain="telemetry",
            signal_type=f"f{i}",
            route_name="r",
            raw_confidence=0.75,
        )
        for i in range(6)
    ]
    assert frag.pressure(records) < 0.35
