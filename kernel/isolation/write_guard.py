"""Write guard — central authority for governed writes."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from kernel.isolation.execution_context import ExecutionContext, Permission
from kernel.isolation.execution_scope import ExecutionScope
from kernel.isolation.rollback_boundary import RollbackBoundary
from kernel.isolation.rollback_plan import RollbackPlan
from kernel.isolation.write_target import WriteTarget
from kernel.isolation.write_violation import WriteViolation


@dataclass
class WriteGuard:
    """
    Block writes when:
      - no active ExecutionContext
      - target not declared
      - permission mismatch
      - no rollback for high-risk
      - no guardian ref for external
    """

    scope: ExecutionScope | None = None
    rollback: RollbackBoundary | None = None
    _violations: list[WriteViolation] = field(default_factory=list)
    _allowed_writes: int = 0

    def __post_init__(self) -> None:
        if self.scope is None:
            self.scope = ExecutionScope()
        if self.rollback is None:
            self.rollback = RollbackBoundary()

    @property
    def violations(self) -> list[WriteViolation]:
        return list(self._violations)

    def check(
        self,
        target: WriteTarget | str,
        *,
        context: ExecutionContext | None = None,
        plan: RollbackPlan | None = None,
    ) -> bool:
        ctx = context or self.scope.current()
        target_str = target.value if isinstance(target, WriteTarget) else str(target)
        wt = (
            target
            if isinstance(target, WriteTarget)
            else WriteTarget.parse(target_str)
        )

        if ctx is None:
            self._record("no_context", "write attempted without ExecutionContext", target_str)
            return False

        if wt is None:
            self._record(
                "undeclared_target",
                f"target '{target_str}' is not a canonical WriteTarget",
                target_str,
                ctx.context_id,
            )
            return False

        if not ctx.has_permission(Permission.WRITE):
            self._record("permission_mismatch", "WRITE not granted", target_str, ctx.context_id)
            return False

        allowed = ctx.allowed_write_targets or ctx.write_targets
        if allowed and wt.value not in allowed and target_str not in allowed:
            self._record(
                "target_not_declared",
                f"target '{wt.value}' not in allowed_write_targets",
                target_str,
                ctx.context_id,
            )
            return False

        ok, reason = self.rollback.check(ctx, wt, plan=plan)
        if not ok:
            self._record("rollback_required", reason, target_str, ctx.context_id)
            return False

        if wt == WriteTarget.EXTERNAL_SYSTEMS and not ctx.guardian_reference:
            self._record(
                "guardian_required",
                "external write requires guardian_reference",
                target_str,
                ctx.context_id,
            )
            return False

        active = self.scope.current()
        if active is not None and active.context_id != ctx.context_id:
            self._record("cross_context", "cross-context write blocked", target_str, ctx.context_id)
            return False

        self._allowed_writes += 1
        return True

    def assert_write(
        self,
        target: WriteTarget | str,
        *,
        context: ExecutionContext | None = None,
        plan: RollbackPlan | None = None,
    ) -> None:
        if not self.check(target, context=context, plan=plan):
            raise PermissionError(
                f"Write to '{target}' denied: {self._violations[-1].message}"
            )

    def guarded_write(
        self,
        target: WriteTarget | str,
        fn: Callable[[], Any],
        *,
        context: ExecutionContext | None = None,
        plan: RollbackPlan | None = None,
    ) -> Any:
        self.assert_write(target, context=context, plan=plan)
        return fn()

    def _record(
        self,
        code: str,
        message: str,
        target: str,
        context_id: str | None = None,
    ) -> None:
        self._violations.append(
            WriteViolation(code=code, message=message, target=target, context_id=context_id)
        )

    def stats(self) -> dict[str, Any]:
        return {
            "allowed_writes": self._allowed_writes,
            "violation_count": len(self._violations),
        }
