"""Test 6: fragmentation detection stable."""

from governance.identity.fragmentation_guard import FragmentationGuard


def test_fragmentation_guard() -> None:
    guard = FragmentationGuard()
    assert guard.check_signatures(["a", "a", "b"]) is True
    assert guard.check_signatures([f"s{i}" for i in range(30)]) is False
