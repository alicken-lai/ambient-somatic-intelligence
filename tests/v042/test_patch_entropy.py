"""Patch registry entropy metrics."""

from __future__ import annotations

from kernel.entropy.patch_entropy_adapter import PatchEntropyAdapter
from kernel.wiring.patch_handle import PatchHandle
from kernel.wiring.patch_registry import PatchRegistry


class _Target:
    def method(self) -> str:
        return "original"


def test_patch_entropy_active_and_restore() -> None:
    registry = PatchRegistry()
    target = _Target()

    def replacement() -> str:
        return "patched"

    handle = PatchHandle(
        patch_id="test.patch",
        phase="test",
        target=target,
        attr_name="method",
        original=target.method,
        replacement=replacement,
    )
    registry.register(handle)
    assert registry.is_active("test.patch")

    metrics = {m.name: m for m in PatchEntropyAdapter().observe(registry)}
    assert metrics["patch_active_pressure"].value > 0

    registry.restore("test.patch")
    assert not registry.is_active("test.patch")

    after = PatchEntropyAdapter().observe(registry)
    leakage = next(m for m in after if m.name == "patch_leakage")
    assert leakage.value >= 0.0
