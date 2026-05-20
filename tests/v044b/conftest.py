"""Shared fixtures for v0.4.4B tests."""

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
def governed_context() -> ExecutionContext:
    return ExecutionContext.create(
        caller_id="v044b-test",
        caller_type="agent",
        scope=ScopeType.GOVERNED_WRITE.value,
        permissions={Permission.READ, Permission.WRITE},
        allowed_write_targets={
            WriteTarget.MEMORY.value,
            WriteTarget.GOVERNANCE_AUDIT.value,
            WriteTarget.STATE.value,
            WriteTarget.SKILL_REGISTRY.value,
            WriteTarget.TRUTH_GRAPH.value,
            WriteTarget.INTEGRATION_BUS.value,
        },
        rollback_plan=RollbackPlan(rollback_type=RollbackType.SNAPSHOT),
        guardian_reference="guardian-allow-v044b-test",
    )


@pytest.fixture
def guarded_writer(
    write_guard: WriteGuard,
    authority_trace: AuthorityTrace,
) -> GuardedFileWriter:
    return GuardedFileWriter(
        write_guard=write_guard,
        root_resolver=RootResolver(),
        authority_trace=authority_trace,
        legacy_fallback=False,
    )


@pytest.fixture
def write_guard(execution_scope: ExecutionScope) -> WriteGuard:
    return WriteGuard(scope=execution_scope)
