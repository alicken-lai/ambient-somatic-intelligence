"""Test 7: identity decay bounded."""

from governance.identity.identity_decay import IdentityDecay


def test_decay_floor() -> None:
    decay = IdentityDecay()
    assert decay.multiplier(50) == 1.0
    assert decay.multiplier(200) >= 0.88
