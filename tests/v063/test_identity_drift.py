"""Area 5: identity drift."""

from governance.coherence.identity_drift import IdentityDrift
from governance.identity.cognitive_identity import CognitiveIdentity


def test_small_window_bounded() -> None:
    identity = CognitiveIdentity()
    drift = IdentityDrift()
    records = [
        identity.build_record_from_target(
            source_domain="telemetry",
            signal_type=f"d{i}",
            route_name="r",
            raw_confidence=0.8,
        )
        for i in range(5)
    ]
    assert drift.drift_bounded(records) is True
