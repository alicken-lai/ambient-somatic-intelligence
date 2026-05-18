"""Area 8 — Isolation observability."""

from __future__ import annotations

from kernel.isolation.execution_context import ExecutionContext, Permission
from kernel.isolation.execution_scope import ExecutionScope, ScopeType
from kernel.isolation.rollback_plan import RollbackPlan, RollbackType
from kernel.isolation.write_guard import WriteGuard
from kernel.isolation.write_target import WriteTarget
from observability.v04.isolation_score import (
    GATE_THRESHOLD,
    IsolationMetrics,
    compute_isolation,
    evaluate_isolation,
)


def test_isolation_score_clean_metrics() -> None:
    metrics = IsolationMetrics(
        total_writes=10,
        writes_with_context=10,
        blocked_violations=0,
        sandbox_leaks=0,
        cross_context_attempts=0,
    )
    report = compute_isolation(metrics)
    assert report.score >= GATE_THRESHOLD
    assert report.gate_pass


def test_evaluate_from_guards() -> None:
    scope = ExecutionScope()
    guard = WriteGuard(scope=scope)
    ctx = ExecutionContext.create(
        caller_id="obs",
        scope=ScopeType.GOVERNED_WRITE.value,
        permissions={Permission.WRITE},
        allowed_write_targets={WriteTarget.STATE.value},
        rollback_plan=RollbackPlan(rollback_type=RollbackType.SNAPSHOT),
    )
    scope.enter(ctx)
    try:
        guard.check(WriteTarget.STATE)
    finally:
        scope.exit(ctx.context_id)
    report = evaluate_isolation(write_guard=guard, scope=scope)
    assert 0.0 <= report.score <= 1.0
