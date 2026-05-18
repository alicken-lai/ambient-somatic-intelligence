"""Phase 2 — SingletonGuard."""

from __future__ import annotations

import pytest

from kernel.isolation.singleton_guard import SingletonGuard
from kernel.isolation.execution_context import ExecutionContext


def test_singleton_requires_context(governed_context: ExecutionContext):
    guard = SingletonGuard()
    guard.register("test_bus", owner="somatic")

    with pytest.raises(PermissionError):
        guard.mutate("test_bus", lambda: None)

    result = guard.mutate(
        "test_bus",
        lambda: {"ok": True},
        context=governed_context,
        attribute="handlers",
    )
    assert result["ok"] is True
    assert guard.stats()["mutations"] == 1
