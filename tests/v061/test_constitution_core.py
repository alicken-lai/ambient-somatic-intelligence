"""Area 1: frozen constitution core."""

from governance.constitution.constitution import Constitution, load_constitution
from governance.constitution.constitutional_lock import ConstitutionalLockError


def test_constitution_sealed_at_load(sealed_constitution) -> None:
    assert sealed_constitution.sealed is True
    assert len(sealed_constitution.rules) >= 5


def test_runtime_cannot_add_rules(sealed_constitution) -> None:
    from governance.constitution.constitutional_rule import ConstitutionalRule

    try:
        sealed_constitution.attempt_add_rule(
            ConstitutionalRule("x", "X", "should fail")
        )
        assert False, "expected ConstitutionalLockError"
    except ConstitutionalLockError:
        pass


def test_load_constitution_singleton() -> None:
    a = load_constitution()
    b = load_constitution()
    assert a is b
