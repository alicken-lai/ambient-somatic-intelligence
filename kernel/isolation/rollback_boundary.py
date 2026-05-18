"""Rollback boundary — validates rollback coverage for writes."""

from __future__ import annotations

from kernel.isolation.execution_context import ExecutionContext
from kernel.isolation.rollback_plan import HIGH_RISK_FORBIDDEN, RollbackPlan, RollbackType
from kernel.isolation.write_target import WriteTarget


class RollbackBoundary:
    """Enforces rollback plan requirements on high-risk targets."""

    def check(
        self,
        context: ExecutionContext,
        target: WriteTarget | str,
        *,
        plan: RollbackPlan | None = None,
    ) -> tuple[bool, str]:
        wt = target if isinstance(target, WriteTarget) else WriteTarget.parse(str(target))
        if wt is None:
            return True, ""

        effective = plan
        if effective is None and context.rollback_plan is not None:
            effective = context.rollback_plan
        elif effective is None and context.rollback_boundaries:
            try:
                rb = RollbackType(context.rollback_boundaries[0])
                effective = RollbackPlan(rollback_type=rb)
            except ValueError:
                effective = RollbackPlan(rollback_type=RollbackType.NONE)

        if wt not in WriteTarget.high_risk():
            return True, ""

        if effective is None:
            return False, "high-risk write requires RollbackPlan"

        if not effective.satisfies_high_risk():
            return False, f"high-risk target '{wt.value}' cannot use rollback NONE"

        if wt == WriteTarget.EXTERNAL_SYSTEMS and effective.rollback_type == RollbackType.IRREVERSIBLE_WITH_APPROVAL:
            if not effective.guardian_reference and not context.guardian_reference:
                return False, "irreversible external write requires guardian_reference"

        return True, ""
