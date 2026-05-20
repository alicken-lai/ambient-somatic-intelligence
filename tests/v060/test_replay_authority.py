"""Area 4: replay authority bounded."""

from governance.cognition.replay_authority import REPLAY_MAX_INFLUENCE, ReplayAuthority


def test_replay_bounded() -> None:
    auth = ReplayAuthority()
    r = auth.blend(0.6, 0.9, replay_confidence=1.0)
    assert r.replay_weight <= REPLAY_MAX_INFLUENCE
    assert r.bounded is True
    assert r.read_only is True
