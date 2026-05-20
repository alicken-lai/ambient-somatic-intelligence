"""Shared fixtures for v0.4.3 isolation tests."""

from __future__ import annotations

import pytest

from kernel.isolation.execution_context import ExecutionContext, Permission
from kernel.isolation.execution_scope import ExecutionScope, ScopeType
from kernel.isolation.rollback_plan import RollbackPlan, RollbackType
from kernel.isolation.write_guard import WriteGuard
from kernel.isolation.write_target import WriteTarget


@pytest.fixture
def execution_scope() -> ExecutionScope:
    return ExecutionScope()


@pytest.fixture
def write_guard(execution_scope: ExecutionScope) -> WriteGuard:
    return WriteGuard(scope=execution_scope)


@pytest.fixture
def governed_context() -> ExecutionContext:
    return ExecutionContext.create(
        caller_id="test-agent",
        caller_type="agent",
        scope=ScopeType.GOVERNED_WRITE.value,
        permissions={Permission.READ, Permission.WRITE},
        allowed_write_targets={WriteTarget.STATE.value},
        rollback_plan=RollbackPlan(rollback_type=RollbackType.SNAPSHOT),
    )
