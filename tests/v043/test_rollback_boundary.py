"""Area 7 — Rollback boundary."""

from __future__ import annotations

from kernel.isolation.execution_context import ExecutionContext, Permission
from kernel.isolation.execution_scope import ScopeType
from kernel.isolation.rollback_boundary import RollbackBoundary
from kernel.isolation.rollback_plan import RollbackPlan, RollbackType
from kernel.isolation.write_target import WriteTarget


def test_high_risk_rejects_none() -> None:
    boundary = RollbackBoundary()
    ctx = ExecutionContext.create(
        caller_id="r",
        scope=ScopeType.GOVERNED_WRITE.value,
        permissions={Permission.WRITE},
        rollback_plan=RollbackPlan(rollback_type=RollbackType.NONE),
    )
    ok, reason = boundary.check(ctx, WriteTarget.TRUTH_GRAPH)
    assert not ok
    assert "NONE" in reason


def test_snapshot_allows_state_write() -> None:
    boundary = RollbackBoundary()
    ctx = ExecutionContext.create(
        caller_id="r",
        scope=ScopeType.LOCAL_STATE.value,
        permissions={Permission.WRITE},
        rollback_plan=RollbackPlan(rollback_type=RollbackType.SNAPSHOT),
    )
    ok, _ = boundary.check(ctx, WriteTarget.STATE)
    assert ok
