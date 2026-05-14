"""
Mandatory Pre-Execution Gate — Single entry point for all governance checks.

Combines ExecutionValidator (4-stage pipeline) with ToolPermissionMatrix
(per-agent tool access) into one atomic check. Every action must pass through
this gate before execution. All decisions are automatically audited.

Gate flow:
  1. Tool Permission check (if tool_name provided)
  2. Execution Validation (policy → anomaly → resource → injection)
  3. Combined result with risk escalation
  4. Automatic audit record

Usage:
    gate = MandatoryGate(validator, permissions, audit_log)
    result = gate.check("git push origin main", agent_id="cursor-agent", tool_name="git:push")
    if not result.allowed:
        print(f"BLOCKED: {result.reason}")
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from governance.policy_engine import RiskLevel
from governance.execution_validator import ExecutionValidator, ValidationResult
from governance.tool_permissions import (
    ToolPermissionMatrix,
    ToolPermission,
    PermissionResult,
)
from governance.audit_log import GovernanceAuditLog


@dataclass
class GateResult:
    """Combined result from the mandatory governance gate."""
    allowed: bool
    risk_level: RiskLevel
    action: str
    agent_id: str
    validation_result: ValidationResult | None = None
    permission_result: PermissionResult | None = None
    audit_recorded: bool = False
    reason: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @property
    def is_blocked(self) -> bool:
        return not self.allowed

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "allowed": self.allowed,
            "risk_level": self.risk_level.name,
            "action": self.action,
            "agent_id": self.agent_id,
            "reason": self.reason,
            "audit_recorded": self.audit_recorded,
            "timestamp": self.timestamp,
        }
        if self.validation_result:
            result["validation"] = self.validation_result.to_dict()
        if self.permission_result:
            result["permission"] = self.permission_result.to_dict()
        return result


class MandatoryGate:
    """
    The single mandatory governance checkpoint for all agent actions.

    Combines tool permissions and execution validation into one atomic check.
    Every decision is automatically recorded in the governance audit log.
    """

    def __init__(
        self,
        validator: ExecutionValidator | None = None,
        permissions: ToolPermissionMatrix | None = None,
        audit_log: GovernanceAuditLog | None = None,
    ):
        self.validator = validator or ExecutionValidator()
        self.permissions = permissions or ToolPermissionMatrix()
        self.audit_log = audit_log or GovernanceAuditLog()
        self._total_checks = 0
        self._blocked_count = 0
        self._review_count = 0

    def check(
        self,
        action: str,
        agent_id: str = "unknown",
        tool_name: str | None = None,
        resource: str = "",
        scopes: list[str] | None = None,
        context: str = "",
    ) -> GateResult:
        """
        Run the full mandatory governance gate.

        Steps:
          1. If tool_name is provided, check tool permissions first.
             - DENIED → immediate block (skip validation pipeline).
             - REQUIRES_REVIEW → escalate risk, continue validation.
          2. Run ExecutionValidator pipeline.
          3. Combine results: highest risk wins.
          4. Record decision in audit log.

        Returns GateResult with the combined decision.
        """
        self._total_checks += 1

        perm_result: PermissionResult | None = None
        perm_risk = RiskLevel.ALLOW

        # Step 1: Tool permission check
        if tool_name:
            perm_result = self.permissions.check(agent_id, tool_name)

            if perm_result.is_denied:
                self._blocked_count += 1
                gate_result = GateResult(
                    allowed=False,
                    risk_level=RiskLevel.BLOCK,
                    action=action,
                    agent_id=agent_id,
                    permission_result=perm_result,
                    reason=f"Tool permission denied: {perm_result.reason}",
                )
                self._record_audit(gate_result)
                return gate_result

            if perm_result.needs_review:
                perm_risk = RiskLevel.REVIEW_REQUIRED

        # Step 2: Execution validation pipeline
        validation_result = self.validator.validate(
            action=action,
            agent_id=agent_id,
            resource=resource,
            scopes=scopes,
            context=context,
        )

        # Step 3: Combine — highest risk wins
        combined_risk = max(validation_result.risk, perm_risk)
        allowed = validation_result.allowed and perm_risk != RiskLevel.BLOCK

        if combined_risk == RiskLevel.REVIEW_REQUIRED and validation_result.allowed:
            reason = "Requires review"
            if perm_result and perm_result.needs_review:
                reason = f"Tool '{tool_name}' requires review for {agent_id}"
            elif validation_result.blocking_stage:
                reason = validation_result.blocking_stage.details
            self._review_count += 1
        elif not allowed:
            blocking = validation_result.blocking_stage
            reason = blocking.details if blocking else "Blocked by governance gate"
            self._blocked_count += 1
        else:
            reason = "Allowed by governance gate"

        gate_result = GateResult(
            allowed=allowed,
            risk_level=combined_risk,
            action=action,
            agent_id=agent_id,
            validation_result=validation_result,
            permission_result=perm_result,
            reason=reason,
        )

        # Step 4: Audit
        self._record_audit(gate_result)

        return gate_result

    def _record_audit(self, result: GateResult) -> None:
        """Record the gate decision in the governance audit log."""
        matched_policies: list[str] = []
        validation_stages = None

        if result.validation_result:
            for stage in result.validation_result.stages:
                policy_name = stage.metadata.get("policy", "")
                if policy_name:
                    matched_policies.append(policy_name)
            validation_stages = [
                {"name": s.name, "passed": s.passed, "risk": s.risk.name}
                for s in result.validation_result.stages
            ]

        metadata: dict[str, Any] = {"gate": "mandatory", "source": "MandatoryGate"}
        if result.permission_result:
            metadata["tool_permission"] = result.permission_result.to_dict()

        self.audit_log.record_decision(
            action=result.action,
            risk=result.risk_level,
            reason=result.reason,
            agent_id=result.agent_id,
            matched_policies=matched_policies,
            validation_stages=validation_stages,
            metadata=metadata,
        )
        result.audit_recorded = True

    def stats(self) -> dict[str, Any]:
        """Gate usage statistics."""
        return {
            "total_checks": self._total_checks,
            "blocked": self._blocked_count,
            "review_required": self._review_count,
            "allowed": self._total_checks - self._blocked_count - self._review_count,
            "block_rate": self._blocked_count / max(self._total_checks, 1),
        }
