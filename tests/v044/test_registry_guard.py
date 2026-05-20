"""Phase 4 — RegistryGuard."""

from __future__ import annotations

from kernel.isolation.registry_guard import RegistryGuard
from kernel.isolation.write_target import WriteTarget


def test_registry_guard_mutate(governed_context):
    guard = RegistryGuard()
    guard.bind("skill_registry", write_target=WriteTarget.SKILL_REGISTRY, owner="skills")
    store: dict[str, int] = {}

    def register() -> str:
        store["n"] = store.get("n", 0) + 1
        return "skill-1"

    skill_id = guard.mutate(
        "skill_registry",
        register,
        context=governed_context,
        operation="register",
    )
    assert skill_id == "skill-1"
    assert guard.stats()["mutations"] == 1
