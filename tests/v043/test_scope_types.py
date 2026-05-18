"""Area 10 — Scope types and state guard integration."""

from __future__ import annotations

from kernel.isolation.execution_scope import ScopeType
from kernel.isolation.state_guard import StateGuard


def test_scope_type_enum_values() -> None:
    assert ScopeType.SANDBOX.value == "sandbox"
    assert ScopeType.RELEASE_OPERATION.value == "release_operation"


def test_state_guard_uses_write_targets(
    governed_context,
    execution_scope,
) -> None:
    guard = StateGuard(scope=execution_scope)
    execution_scope.enter(governed_context)
    try:
        assert guard.check_write(governed_context, "state")
        assert not guard.check_write(governed_context, "memory")
    finally:
        execution_scope.exit(governed_context.context_id)
