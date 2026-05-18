"""Shared fixtures for v0.4.4 migration tests."""

from __future__ import annotations

import pytest

from kernel.isolation.execution_context import ExecutionContext, Permission
from kernel.isolation.execution_scope import ExecutionScope, ScopeType
from kernel.isolation.guarded_file_writer import GuardedFileWriter
from kernel.isolation.rollback_plan import RollbackPlan, RollbackType
from kernel.isolation.root_resolver import RootResolver
from kernel.isolation.write_guard import WriteGuard
from kernel.isolation.write_target import WriteTarget
from observability.v04.authority_trace import AuthorityTrace


@pytest.fixture
def execution_scope() -> ExecutionScope:
    return ExecutionScope()


@pytest.fixture
def authority_trace() -> AuthorityTrace:
    return AuthorityTrace()


@pytest.fixture
def write_guard(execution_scope: ExecutionScope) -> WriteGuard:
    return WriteGuard(scope=execution_scope)


@pytest.fixture
def governed_context() -> ExecutionContext:
    return ExecutionContext.create(
        caller_id="v044-test",
        caller_type="agent",
        scope=ScopeType.GOVERNED_WRITE.value,
        permissions={Permission.READ, Permission.WRITE},
        allowed_write_targets={
            WriteTarget.MEMORY.value,
            WriteTarget.GOVERNANCE_AUDIT.value,
            WriteTarget.SKILL_REGISTRY.value,
            WriteTarget.STATE.value,
        },
        rollback_plan=RollbackPlan(rollback_type=RollbackType.SNAPSHOT),
        guardian_reference="guardian-allow-v044-test",
    )


@pytest.fixture
def guarded_writer(
    write_guard: WriteGuard,
    authority_trace: AuthorityTrace,
    execution_scope: ExecutionScope,
) -> GuardedFileWriter:
    return GuardedFileWriter(
        write_guard=write_guard,
        root_resolver=RootResolver(),
        authority_trace=authority_trace,
        legacy_fallback=False,
    )
