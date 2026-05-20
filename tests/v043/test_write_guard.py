"""Area 2 — Write authority guard."""

from __future__ import annotations

from kernel.isolation.execution_context import ExecutionContext, Permission
from kernel.isolation.execution_scope import ExecutionScope, ScopeType
from kernel.isolation.rollback_plan import RollbackPlan, RollbackType
from kernel.isolation.write_guard import WriteGuard
from kernel.isolation.write_target import WriteTarget


def test_blocks_without_context(write_guard: WriteGuard) -> None:
    assert write_guard.check(WriteTarget.STATE) is False
    assert write_guard.violations[-1].code == "no_context"


def test_allows_declared_target(
    write_guard: WriteGuard,
    execution_scope: ExecutionScope,
    governed_context: ExecutionContext,
) -> None:
    execution_scope.enter(governed_context)
    try:
        assert write_guard.check(WriteTarget.STATE) is True
    finally:
        execution_scope.exit(governed_context.context_id)


def test_blocks_high_risk_without_rollback(
    write_guard: WriteGuard,
    execution_scope: ExecutionScope,
) -> None:
    ctx = ExecutionContext.create(
        caller_id="x",
        scope=ScopeType.GOVERNED_WRITE.value,
        permissions={Permission.WRITE},
        allowed_write_targets={WriteTarget.MEMORY.value},
        rollback_plan=RollbackPlan(rollback_type=RollbackType.NONE),
    )
    execution_scope.enter(ctx)
    try:
        assert write_guard.check(WriteTarget.MEMORY) is False
    finally:
        execution_scope.exit(ctx.context_id)


def test_external_requires_guardian(
    write_guard: WriteGuard,
    execution_scope: ExecutionScope,
) -> None:
    ctx = ExecutionContext.create(
        caller_id="ext",
        scope=ScopeType.EXTERNAL_ACTION.value,
        permissions={Permission.WRITE, Permission.NETWORK},
        allowed_write_targets={WriteTarget.EXTERNAL_SYSTEMS.value},
        rollback_plan=RollbackPlan(rollback_type=RollbackType.MANUAL_REVIEW),
    )
    execution_scope.enter(ctx)
    try:
        assert write_guard.check(WriteTarget.EXTERNAL_SYSTEMS) is False
    finally:
        execution_scope.exit(ctx.context_id)
