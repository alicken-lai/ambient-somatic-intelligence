"""Area 3: replay coherence."""

from governance.coherence.replay_coherence import ReplayCoherence
from governance.identity.cognitive_identity import CognitiveIdentity


def test_live_batch_coherent() -> None:
    identity = CognitiveIdentity()
    replay = ReplayCoherence()
    batch = [
        identity.build_record_from_target(
            source_domain="telemetry",
            signal_type=f"l{i}",
            route_name="r",
            raw_confidence=0.8,
        )
        for i in range(5)
    ]
    assert replay.coherent(batch) is True
