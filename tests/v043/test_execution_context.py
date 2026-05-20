"""Area 1 — Execution context model."""

from __future__ import annotations

from kernel.isolation.execution_context import ExecutionContext, Permission
from kernel.isolation.execution_scope import ScopeType


def test_context_requires_caller_and_permissions() -> None:
    ctx = ExecutionContext.create(
        caller_id="daemon-1",
        caller_type="daemon",
        scope=ScopeType.READ_ONLY.value,
        permissions={Permission.READ},
    )
    assert ctx.context_id
    assert ctx.caller == "daemon-1"
    assert ctx.caller_type.value == "daemon"
    assert ctx.expires_at


def test_write_targets_backward_compat(governed_context: ExecutionContext) -> None:
    assert "state" in governed_context.write_targets
    assert governed_context.can_write("state")
    assert not governed_context.can_write("memory")
