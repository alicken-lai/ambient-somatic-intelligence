"""
Rollback Planner — Plan rollbacks for every evolution step.

Every evolution step must have a validated rollback plan:
  - What to undo, in what order
  - Validation checks to confirm rollback success
  - Data loss risk assessment
  - Estimated rollback duration

Rollback plans are created proactively (before changes are applied)
and validated on demand (to check if rollback is still viable given
current system state).
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from runtime.evolution_engine.refactor_planner import RefactorPlan, RefactorStep

logger = logging.getLogger(__name__)


@dataclass
class RollbackStep:
    """A single rollback action."""
    step_id: str = field(default_factory=lambda: f"rb_{uuid.uuid4().hex[:8]}")
    target_step_id: str = ""
    action: str = ""
    description: str = ""
    validation: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize to JSON-compatible dict."""
        return {
            "step_id": self.step_id,
            "target_step_id": self.target_step_id,
            "action": self.action,
            "description": self.description,
            "validation": self.validation,
        }


@dataclass
class RollbackPlan:
    """Complete rollback plan for an evolution proposal."""
    plan_id: str = field(default_factory=lambda: f"rollback_{uuid.uuid4().hex[:12]}")
    steps: list[RollbackStep] = field(default_factory=list)
    validation_checks: list[dict[str, Any]] = field(default_factory=list)
    estimated_duration: str = ""
    data_loss_risk: str = "none"
    created_at: str = field(
        default_factory=lambda: datetime.now(tz=timezone.utc).isoformat()
    )
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to JSON-compatible dict."""
        return {
            "plan_id": self.plan_id,
            "steps": [s.to_dict() for s in self.steps],
            "validation_checks": self.validation_checks,
            "estimated_duration": self.estimated_duration,
            "data_loss_risk": self.data_loss_risk,
            "created_at": self.created_at,
            "step_count": len(self.steps),
            "metadata": self.metadata,
        }


@dataclass
class RollbackValidation:
    """Result of validating a rollback plan against current state."""
    is_viable: bool = True
    blockers: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    state_drift: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to JSON-compatible dict."""
        return {
            "is_viable": self.is_viable,
            "blockers": self.blockers,
            "warnings": self.warnings,
            "state_drift": self.state_drift,
        }


class RollbackPlanner:
    """
    Plans rollbacks for every evolution step.

    Creates comprehensive rollback plans that can undo refactoring
    in the correct order, with validation checks at each step.

    Usage:
        planner = RollbackPlanner()

        rollback = planner.plan_rollback(refactor_plan)
        print(f"Rollback steps: {len(rollback.steps)}")
        print(f"Data loss risk: {rollback.data_loss_risk}")

        validation = planner.validate_rollback(rollback, current_state)
        if validation.is_viable:
            print("Rollback is safe to execute")
    """

    def __init__(self):
        self._plans: list[RollbackPlan] = []

    def plan_rollback(self, refactor_plan: RefactorPlan) -> RollbackPlan:
        """
        Create a rollback plan for a refactoring plan.

        Generates rollback steps in reverse order of the refactoring,
        with validation checks for each step.

        Args:
            refactor_plan: The refactoring plan to create rollback for

        Returns:
            RollbackPlan with ordered undo steps and validation
        """
        rollback_steps: list[RollbackStep] = []
        validation_checks: list[dict[str, Any]] = []

        reversed_steps = list(reversed(refactor_plan.steps))

        for refactor_step in reversed_steps:
            rb_step = self._create_rollback_step(refactor_step)
            rollback_steps.append(rb_step)

            validation = self._create_validation_check(refactor_step)
            validation_checks.append(validation)

        data_loss_risk = self._assess_data_loss_risk(refactor_plan)
        estimated_duration = self._estimate_rollback_duration(rollback_steps)

        plan = RollbackPlan(
            steps=rollback_steps,
            validation_checks=validation_checks,
            estimated_duration=estimated_duration,
            data_loss_risk=data_loss_risk,
            metadata={
                "source_plan_id": refactor_plan.plan_id,
                "source_step_count": len(refactor_plan.steps),
            },
        )

        self._plans.append(plan)
        logger.info(
            "Rollback plan created: %d steps, risk=%s, duration=%s",
            len(rollback_steps), data_loss_risk, estimated_duration
        )
        return plan

    def validate_rollback(
        self,
        rollback_plan: RollbackPlan,
        current_state: dict[str, Any],
    ) -> RollbackValidation:
        """
        Validate whether a rollback plan is still viable.

        Checks current system state against rollback assumptions to
        determine if the rollback can still be safely executed.

        Args:
            rollback_plan: The rollback plan to validate
            current_state: Current system state dict

        Returns:
            RollbackValidation with viability assessment
        """
        blockers: list[str] = []
        warnings: list[str] = []
        state_drift: list[dict[str, Any]] = []

        # Check if the system has drifted since the plan was created
        current_modules = set(current_state.get("modules", {}).keys())
        plan_targets = {
            step.target_step_id for step in rollback_plan.steps
        }

        for check in rollback_plan.validation_checks:
            check_type = check.get("type", "")
            target = check.get("target", "")

            if check_type == "module_exists":
                if target and target not in current_modules:
                    state_drift.append({
                        "type": "missing_module",
                        "target": target,
                        "impact": "rollback step may fail",
                    })
                    warnings.append(
                        f"Module '{target}' no longer exists; rollback step may be unnecessary"
                    )

            elif check_type == "health_above_threshold":
                threshold = check.get("threshold", 0.5)
                current_health = current_state.get("health_scores", {}).get(target, 1.0)
                if current_health < threshold:
                    warnings.append(
                        f"Module '{target}' health ({current_health:.2f}) below "
                        f"threshold ({threshold:.2f}); rollback may be risky"
                    )

        # Check for state changes that invalidate rollback
        if current_state.get("active_operations", 0) > 0:
            warnings.append(
                "Active operations detected; rollback should wait for quiescence"
            )

        if current_state.get("locked_modules"):
            locked = current_state["locked_modules"]
            for step in rollback_plan.steps:
                if step.target_step_id in locked:
                    blockers.append(
                        f"Module '{step.target_step_id}' is locked; "
                        f"cannot perform rollback step '{step.step_id}'"
                    )

        is_viable = len(blockers) == 0

        validation = RollbackValidation(
            is_viable=is_viable,
            blockers=blockers,
            warnings=warnings,
            state_drift=state_drift,
        )

        logger.info(
            "Rollback validation: viable=%s, blockers=%d, warnings=%d",
            is_viable, len(blockers), len(warnings)
        )
        return validation

    def get_plan(self, plan_id: str) -> RollbackPlan | None:
        """Retrieve a rollback plan by ID."""
        for plan in self._plans:
            if plan.plan_id == plan_id:
                return plan
        return None

    def _create_rollback_step(self, refactor_step: RefactorStep) -> RollbackStep:
        """Create a rollback step that undoes a refactoring step."""
        return RollbackStep(
            target_step_id=refactor_step.patch_id,
            action="revert",
            description=(
                f"Revert: {refactor_step.description}. "
                f"Undo changes from step #{refactor_step.order} "
                f"(patch: {refactor_step.patch_id})."
            ),
            validation=(
                f"Verify module state matches pre-step-{refactor_step.order} baseline. "
                f"Confirm no downstream dependencies are broken."
            ),
        )

    def _create_validation_check(self, refactor_step: RefactorStep) -> dict[str, Any]:
        """Create a validation check for a rollback step."""
        return {
            "type": "module_exists",
            "target": refactor_step.patch_id,
            "description": (
                f"Validate that reverting step #{refactor_step.order} "
                f"({refactor_step.description}) leaves the system in a consistent state"
            ),
            "expected_outcome": "module returns to pre-change state",
        }

    def _assess_data_loss_risk(self, refactor_plan: RefactorPlan) -> str:
        """
        Assess data loss risk of rolling back a refactoring plan.

        Categories: none, minimal, moderate, significant
        """
        if not refactor_plan.steps:
            return "none"

        max_risk = max(s.risk for s in refactor_plan.steps)

        if max_risk < 0.2:
            return "none"
        elif max_risk < 0.4:
            return "minimal"
        elif max_risk < 0.7:
            return "moderate"
        else:
            return "significant"

    def _estimate_rollback_duration(self, steps: list[RollbackStep]) -> str:
        """Estimate how long a rollback would take."""
        minutes_per_step = 10
        total_minutes = len(steps) * minutes_per_step

        if total_minutes < 60:
            return f"{total_minutes}m"
        hours = total_minutes // 60
        mins = total_minutes % 60
        return f"{hours}h {mins}m" if mins else f"{hours}h"
